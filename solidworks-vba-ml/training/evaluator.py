"""
Model Evaluator
Evaluates model performance on test datasets
"""

from loguru import logger
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from pathlib import Path
import time

from utils.model_manager import ModelManager
from validation.vba_validator import VBAValidator
from validation.api_validator import APIValidator


class ModelEvaluator:
    """Evaluates trained models on test datasets"""

    def __init__(self):
        self.model_manager = ModelManager()
        self.vba_validator = VBAValidator()
        self.api_validator = APIValidator()
        self.evaluations: Dict[str, Dict[str, Any]] = {}
        self.results_dir = Path("logs/evaluations")
        self.results_dir.mkdir(parents=True, exist_ok=True)

    async def evaluate(
        self,
        evaluation_id: str,
        test_samples: List[Dict[str, Any]],
        metrics: List[str]
    ) -> Dict[str, Any]:
        """
        Evaluate model on test samples

        Args:
            evaluation_id: Unique evaluation identifier
            test_samples: List of test samples
            metrics: Metrics to compute

        Returns:
            Evaluation results with metrics
        """
        try:
            logger.info(f"Starting evaluation {evaluation_id} with {len(test_samples)} samples")

            results = {
                "correct_count": 0,
                "syntax_valid_count": 0,
                "api_call_correct_count": 0,
                "total_generation_time_ms": 0,
                "detailed_results": []
            }

            for idx, sample in enumerate(test_samples):
                logger.info(f"Evaluating sample {idx + 1}/{len(test_samples)}")

                # Generate code
                start_time = time.time()
                generated_outputs = await self.model_manager.generate_code(
                    prompt=sample.prompt,
                    max_length=512,
                    temperature=0.7,
                    num_return_sequences=1
                )
                generation_time = (time.time() - start_time) * 1000

                results["total_generation_time_ms"] += generation_time

                if not generated_outputs:
                    continue

                generated_code = generated_outputs[0]['code']

                # Validate syntax
                syntax_valid = await self._validate_syntax(generated_code)
                if syntax_valid:
                    results["syntax_valid_count"] += 1

                # Validate API calls
                api_calls_correct = await self._validate_api_calls(
                    generated_code,
                    sample.api_calls
                )
                if api_calls_correct:
                    results["api_call_correct_count"] += 1

                # Check if code matches expected
                is_correct = await self._check_correctness(
                    generated_code,
                    sample.vba_code
                )
                if is_correct:
                    results["correct_count"] += 1

                # Store detailed result
                results["detailed_results"].append({
                    "sample_id": idx,
                    "prompt": sample.prompt,
                    "expected_code": sample.vba_code,
                    "generated_code": generated_code,
                    "syntax_valid": syntax_valid,
                    "api_calls_correct": api_calls_correct,
                    "is_correct": is_correct,
                    "generation_time_ms": generation_time
                })

            # Calculate metrics
            total_samples = len(test_samples)
            evaluation_results = {
                "accuracy": results["correct_count"] / total_samples if total_samples > 0 else 0,
                "syntax_validity_rate": results["syntax_valid_count"] / total_samples if total_samples > 0 else 0,
                "api_call_accuracy": results["api_call_correct_count"] / total_samples if total_samples > 0 else 0,
                "average_generation_time_ms": results["total_generation_time_ms"] / total_samples if total_samples > 0 else 0,
                "detailed_results": results["detailed_results"]
            }

            # Save evaluation results
            self.evaluations[evaluation_id] = evaluation_results
            await self._save_results(evaluation_id, evaluation_results)

            logger.info(f"Evaluation {evaluation_id} completed")
            return evaluation_results

        except Exception as e:
            logger.error(f"Evaluation failed: {e}", exc_info=True)
            raise

    async def _validate_syntax(self, code: str) -> bool:
        """Validate code syntax"""
        try:
            result = await self.vba_validator.validate_syntax(code, strict=False)
            return result.get('syntax_valid', False) and len(result.get('errors', [])) == 0
        except Exception as e:
            logger.error(f"Syntax validation error: {e}")
            return False

    async def _validate_api_calls(
        self,
        generated_code: str,
        expected_api_calls: List[str]
    ) -> bool:
        """Validate API calls in generated code"""
        try:
            found_api_calls = await self.api_validator.validate_api_calls(generated_code)

            # Check if all expected API calls are present
            for expected_call in expected_api_calls:
                if not any(expected_call in found_call for found_call in found_api_calls):
                    return False

            return True

        except Exception as e:
            logger.error(f"API validation error: {e}")
            return False

    async def _check_correctness(self, generated: str, expected: str) -> bool:
        """
        Check if generated code is functionally correct

        This is a simplified check - you may want to implement more sophisticated
        comparison logic (e.g., AST comparison, execution testing, etc.)
        """
        # Simple similarity check
        generated_clean = generated.strip().lower()
        expected_clean = expected.strip().lower()

        # Check if they're similar (>80% match)
        similarity = self._calculate_similarity(generated_clean, expected_clean)
        return similarity > 0.8

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity (simple approach)"""
        if not text1 or not text2:
            return 0.0

        # Token-based similarity
        tokens1 = set(text1.split())
        tokens2 = set(text2.split())

        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)

        if not union:
            return 0.0

        return len(intersection) / len(union)

    async def _save_results(self, evaluation_id: str, results: Dict[str, Any]):
        """Save evaluation results to file"""
        result_file = self.results_dir / f"{evaluation_id}.json"

        with open(result_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"Evaluation results saved to {result_file}")

    async def get_results(self, evaluation_id: str) -> Optional[Dict[str, Any]]:
        """Get results from a previous evaluation"""
        if evaluation_id in self.evaluations:
            return self.evaluations[evaluation_id]

        # Try to load from file
        result_file = self.results_dir / f"{evaluation_id}.json"
        if result_file.exists():
            with open(result_file, 'r') as f:
                return json.load(f)

        return None

    async def get_metrics_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get historical evaluation metrics"""
        history = []

        # Load recent evaluation files
        result_files = sorted(
            self.results_dir.glob("*.json"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )[:limit]

        for result_file in result_files:
            with open(result_file, 'r') as f:
                result = json.load(f)
                history.append({
                    "evaluation_id": result_file.stem,
                    "accuracy": result.get("accuracy"),
                    "syntax_validity_rate": result.get("syntax_validity_rate"),
                    "api_call_accuracy": result.get("api_call_accuracy"),
                    "timestamp": result_file.stat().st_mtime
                })

        return history
