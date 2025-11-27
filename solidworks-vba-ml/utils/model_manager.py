"""
Model management utilities
Handles loading, caching, and inference of trained models
"""

from loguru import logger
from pathlib import Path
from typing import List, Dict, Any, Optional
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from config.settings import settings
import asyncio


class ModelManager:
    """Manages ML models for code generation"""

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.current_model_name = None
        self.model_version = "0.1.0"
        self.cache_dir = Path(settings.MODEL_CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"ModelManager initialized (device={self.device})")

    async def get_model(self):
        """Get the current loaded model, load default if not loaded"""
        if self.model is None:
            await self.load_model(settings.DEFAULT_MODEL)
        return self.model

    async def load_model(self, model_name: str):
        """
        Load a model for code generation

        Args:
            model_name: HuggingFace model name or local path
        """
        try:
            logger.info(f"Loading model: {model_name}")

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=str(self.cache_dir),
                trust_remote_code=True
            )

            # Load model
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                cache_dir=str(self.cache_dir),
                trust_remote_code=True,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                low_cpu_mem_usage=True
            )

            self.model.to(self.device)
            self.model.eval()
            self.current_model_name = model_name

            logger.info(f"Model {model_name} loaded successfully on {self.device}")

        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise

    async def generate_code(
        self,
        prompt: str,
        max_length: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        num_return_sequences: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Generate VBA code from natural language prompt

        Args:
            prompt: Natural language description
            max_length: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            num_return_sequences: Number of sequences to generate

        Returns:
            List of generated code outputs with metadata
        """
        try:
            if self.model is None or self.tokenizer is None:
                await self.load_model(settings.DEFAULT_MODEL)

            # Format prompt for code generation
            formatted_prompt = self._format_prompt(prompt)

            # Tokenize
            inputs = self.tokenizer(
                formatted_prompt,
                return_tensors="pt",
                truncation=True,
                max_length=settings.MAX_SEQUENCE_LENGTH
            ).to(self.device)

            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    temperature=temperature,
                    top_p=top_p,
                    num_return_sequences=num_return_sequences,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    output_scores=True,
                    return_dict_in_generate=True
                )

            # Decode outputs
            generated_codes = []
            for i, sequence in enumerate(outputs.sequences):
                code = self.tokenizer.decode(sequence, skip_special_tokens=True)

                # Remove the prompt from the generated code
                code = code.replace(formatted_prompt, "").strip()

                # Calculate confidence score (average of token probabilities)
                # This is a simplified version - you can improve this
                confidence_score = 0.75  # Placeholder

                generated_codes.append({
                    "code": code,
                    "confidence_score": confidence_score
                })

            return generated_codes

        except Exception as e:
            logger.error(f"Code generation failed: {e}", exc_info=True)
            raise

    async def generate_explanation(self, code: str) -> str:
        """
        Generate natural language explanation for VBA code

        Args:
            code: VBA code to explain

        Returns:
            Natural language explanation
        """
        try:
            explanation_prompt = f"Explain this VBA code:\n\n{code}\n\nExplanation:"

            inputs = self.tokenizer(
                explanation_prompt,
                return_tensors="pt",
                truncation=True
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=256,
                    temperature=0.7,
                    do_sample=True
                )

            explanation = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            explanation = explanation.replace(explanation_prompt, "").strip()

            return explanation

        except Exception as e:
            logger.error(f"Explanation generation failed: {e}")
            return "Explanation generation unavailable"

    def _format_prompt(self, prompt: str) -> str:
        """
        Format prompt for code generation

        Args:
            prompt: User's natural language description

        Returns:
            Formatted prompt for the model
        """
        return f"""Generate SOLIDWORKS VBA code for the following task:

Task: {prompt}

VBA Code:
"""

    async def list_models(self) -> List[str]:
        """
        List available models

        Returns:
            List of model names
        """
        # Check cache directory for downloaded models
        cached_models = []
        if self.cache_dir.exists():
            cached_models = [d.name for d in self.cache_dir.iterdir() if d.is_dir()]

        # Add common code generation models
        recommended_models = [
            "microsoft/codebert-base",
            "Salesforce/codegen-350M-mono",
            "Salesforce/codegen-2B-mono",
            "codellama/CodeLlama-7b-hf",
            "WizardLM/WizardCoder-15B-V1.0"
        ]

        all_models = list(set(cached_models + recommended_models))
        return all_models

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        return {
            "model_name": self.current_model_name,
            "model_version": self.model_version,
            "device": self.device,
            "is_loaded": self.model is not None,
            "cache_dir": str(self.cache_dir)
        }


class ModelCache:
    """Model caching utilities"""

    def __init__(self):
        self.cache_dir = Path(settings.MODEL_CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Model cache initialized")

    def clear_cache(self):
        """Clear model cache"""
        import shutil
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Model cache cleared")
