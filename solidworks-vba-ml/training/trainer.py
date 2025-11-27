"""
PyTorch Model Trainer
Handles fine-tuning of code generation models with LoRA
"""

from loguru import logger
from pathlib import Path
from typing import Dict, Any, Optional
import torch
from torch.utils.data import DataLoader
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, TaskType, PeftModel
from datasets import Dataset
import json
from datetime import datetime
import asyncio
from config.settings import settings


class ModelTrainer:
    """
    PyTorch trainer for SOLIDWORKS VBA code generation models

    Supports:
    - Full fine-tuning
    - LoRA efficient fine-tuning
    - Progress tracking
    - Checkpoint saving
    """

    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.training_jobs: Dict[str, Dict[str, Any]] = {}
        logger.info(f"ModelTrainer initialized (device={self.device})")

    async def train(
        self,
        job_id: str,
        dataset_path: str,
        model_name: str,
        num_epochs: int,
        batch_size: int,
        learning_rate: float,
        output_dir: str,
        use_lora: bool = True
    ):
        """
        Train/fine-tune a code generation model

        Args:
            job_id: Unique training job identifier
            dataset_path: Path to training dataset
            model_name: Base model to fine-tune
            num_epochs: Number of training epochs
            batch_size: Training batch size
            learning_rate: Learning rate
            output_dir: Directory to save checkpoints
            use_lora: Whether to use LoRA for efficient fine-tuning
        """
        try:
            logger.info(f"Starting training job {job_id}")

            # Initialize job tracking
            self.training_jobs[job_id] = {
                "status": "running",
                "current_epoch": 0,
                "total_epochs": num_epochs,
                "current_step": 0,
                "total_steps": 0,
                "loss": None,
                "learning_rate": learning_rate,
                "start_time": datetime.utcnow(),
                "elapsed_time_seconds": 0
            }

            # Load dataset
            logger.info(f"Loading dataset from {dataset_path}")
            train_dataset = await self._load_dataset(dataset_path)

            # Load tokenizer
            logger.info(f"Loading tokenizer: {model_name}")
            tokenizer = AutoTokenizer.from_pretrained(model_name)

            # Add padding token if not present
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token

            # Tokenize dataset
            logger.info("Tokenizing dataset")
            tokenized_dataset = await self._tokenize_dataset(train_dataset, tokenizer)

            # Load model
            logger.info(f"Loading model: {model_name}")
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                low_cpu_mem_usage=True
            )

            # Apply LoRA if requested
            if use_lora:
                logger.info("Applying LoRA configuration")
                model = await self._apply_lora(model)

            # Training arguments
            training_args = TrainingArguments(
                output_dir=output_dir,
                num_train_epochs=num_epochs,
                per_device_train_batch_size=batch_size,
                learning_rate=learning_rate,
                warmup_steps=100,
                logging_steps=10,
                save_steps=500,
                save_total_limit=3,
                fp16=self.device == "cuda",
                report_to="none",
                remove_unused_columns=False,
                gradient_accumulation_steps=2,
                eval_strategy="no"
            )

            # Data collator
            data_collator = DataCollatorForLanguageModeling(
                tokenizer=tokenizer,
                mlm=False
            )

            # Create trainer
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=tokenized_dataset,
                data_collator=data_collator,
                callbacks=[TrainingProgressCallback(self, job_id)]
            )

            # Calculate total steps
            total_steps = (len(tokenized_dataset) // batch_size) * num_epochs
            self.training_jobs[job_id]["total_steps"] = total_steps

            # Train
            logger.info("Starting training")
            trainer.train()

            # Save final model
            final_model_path = Path(output_dir) / "final_model"
            trainer.save_model(str(final_model_path))
            tokenizer.save_pretrained(str(final_model_path))

            # Update job status
            self.training_jobs[job_id]["status"] = "completed"
            elapsed = (datetime.utcnow() - self.training_jobs[job_id]["start_time"]).total_seconds()
            self.training_jobs[job_id]["elapsed_time_seconds"] = elapsed

            logger.info(f"Training job {job_id} completed successfully")

        except Exception as e:
            logger.error(f"Training job {job_id} failed: {e}", exc_info=True)
            if job_id in self.training_jobs:
                self.training_jobs[job_id]["status"] = "failed"
                self.training_jobs[job_id]["error"] = str(e)
            raise

    async def _load_dataset(self, dataset_path: str) -> Dataset:
        """Load and prepare training dataset"""
        dataset_file = Path(dataset_path)

        if dataset_file.is_file() and dataset_file.suffix == ".json":
            # Load from JSON file
            with open(dataset_file, 'r') as f:
                data = json.load(f)
        else:
            # Load from directory
            data_files = list(Path(dataset_path).glob("*.json"))
            data = []
            for file in data_files:
                with open(file, 'r') as f:
                    data.append(json.load(f))

        # Convert to HuggingFace Dataset
        dataset = Dataset.from_list(data)
        logger.info(f"Loaded {len(dataset)} samples")

        return dataset

    async def _tokenize_dataset(self, dataset: Dataset, tokenizer) -> Dataset:
        """Tokenize dataset for training"""

        def tokenize_function(examples):
            # Format: prompt + code
            texts = []
            for i in range(len(examples['prompt'])):
                text = f"Task: {examples['prompt'][i]}\n\nVBA Code:\n{examples['vba_code'][i]}"
                texts.append(text)

            return tokenizer(
                texts,
                truncation=True,
                max_length=settings.MAX_SEQUENCE_LENGTH,
                padding="max_length"
            )

        tokenized = dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=dataset.column_names
        )

        return tokenized

    async def _apply_lora(self, model) -> PeftModel:
        """Apply LoRA configuration to model for efficient fine-tuning"""

        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=settings.LORA_R,
            lora_alpha=settings.LORA_ALPHA,
            lora_dropout=settings.LORA_DROPOUT,
            target_modules=["q_proj", "v_proj"],  # Adjust based on model architecture
            bias="none"
        )

        model = get_peft_model(model, lora_config)
        model.print_trainable_parameters()

        return model

    def estimate_training_time(
        self,
        dataset_size: int,
        num_epochs: int,
        batch_size: int
    ) -> int:
        """
        Estimate training time in minutes

        Args:
            dataset_size: Number of samples
            num_epochs: Training epochs
            batch_size: Batch size

        Returns:
            Estimated time in minutes
        """
        # Simple estimation: ~1 second per batch on GPU, ~5 seconds on CPU
        seconds_per_batch = 1 if self.device == "cuda" else 5
        total_batches = (dataset_size // batch_size) * num_epochs
        total_seconds = total_batches * seconds_per_batch
        return int(total_seconds / 60)

    async def get_progress(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get training progress for a job"""
        if job_id not in self.training_jobs:
            return None

        job = self.training_jobs[job_id]

        # Calculate elapsed time
        if job["status"] == "running":
            elapsed = (datetime.utcnow() - job["start_time"]).total_seconds()
            job["elapsed_time_seconds"] = elapsed

            # Estimate remaining time
            if job["current_step"] > 0 and job["total_steps"] > 0:
                time_per_step = elapsed / job["current_step"]
                remaining_steps = job["total_steps"] - job["current_step"]
                job["estimated_remaining_seconds"] = time_per_step * remaining_steps
            else:
                job["estimated_remaining_seconds"] = None

        return {
            "job_id": job_id,
            "status": job["status"],
            "current_epoch": job["current_epoch"],
            "total_epochs": job["total_epochs"],
            "current_step": job["current_step"],
            "total_steps": job["total_steps"],
            "loss": job.get("loss"),
            "learning_rate": job.get("learning_rate"),
            "elapsed_time_seconds": job["elapsed_time_seconds"],
            "estimated_remaining_seconds": job.get("estimated_remaining_seconds"),
            "timestamp": datetime.utcnow()
        }

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running training job"""
        if job_id not in self.training_jobs:
            return False

        if self.training_jobs[job_id]["status"] not in ["running", "queued"]:
            return False

        self.training_jobs[job_id]["status"] = "cancelled"
        logger.info(f"Training job {job_id} cancelled")
        return True


class TrainingProgressCallback:
    """Callback to track training progress"""

    def __init__(self, trainer: ModelTrainer, job_id: str):
        self.trainer = trainer
        self.job_id = job_id

    def on_epoch_begin(self, args, state, control, **kwargs):
        """Called at the beginning of each epoch"""
        if self.job_id in self.trainer.training_jobs:
            self.trainer.training_jobs[self.job_id]["current_epoch"] = state.epoch

    def on_step_end(self, args, state, control, **kwargs):
        """Called after each training step"""
        if self.job_id in self.trainer.training_jobs:
            job = self.trainer.training_jobs[self.job_id]
            job["current_step"] = state.global_step

            if state.log_history:
                latest_log = state.log_history[-1]
                job["loss"] = latest_log.get("loss")
                job["learning_rate"] = latest_log.get("learning_rate")
