"""
Dataset management utilities
Handles VBA macros, API references, geometry JSON, and prompt templates
"""

from loguru import logger
from pathlib import Path
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
from config.settings import settings
import aiofiles


class DatasetManager:
    """Manages training datasets for SOLIDWORKS VBA ML model"""

    def __init__(self):
        self.base_path = Path(settings.DATASET_BASE_PATH)
        self.vba_macros_path = Path(settings.VBA_MACROS_PATH)
        self.api_references_path = Path(settings.API_REFERENCES_PATH)
        self.geometry_json_path = Path(settings.GEOMETRY_JSON_PATH)
        self.prompts_path = Path(settings.PROMPTS_PATH)
        self.training_samples_path = Path(settings.TRAINING_SAMPLES_PATH)

        # Create directories if they don't exist
        self._create_directories()

    def _create_directories(self):
        """Create dataset directories"""
        for path in [
            self.base_path,
            self.vba_macros_path,
            self.api_references_path,
            self.geometry_json_path,
            self.prompts_path,
            self.training_samples_path
        ]:
            path.mkdir(parents=True, exist_ok=True)

        logger.info("Dataset directories initialized")

    async def add_sample(
        self,
        sample_id: str,
        prompt: str,
        vba_code: str,
        api_calls: List[str],
        geometry_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a training sample to the dataset

        Args:
            sample_id: Unique identifier for the sample
            prompt: Natural language description
            vba_code: VBA code implementation
            api_calls: List of SOLIDWORKS API calls used
            geometry_data: Optional geometry JSON data
            metadata: Additional metadata

        Returns:
            Success status
        """
        try:
            sample_data = {
                "sample_id": sample_id,
                "prompt": prompt,
                "vba_code": vba_code,
                "api_calls": api_calls,
                "geometry_data": geometry_data,
                "metadata": metadata or {},
                "created_at": datetime.utcnow().isoformat()
            }

            # Save to JSON file
            sample_file = self.training_samples_path / f"{sample_id}.json"
            async with aiofiles.open(sample_file, 'w') as f:
                await f.write(json.dumps(sample_data, indent=2))

            logger.info(f"Training sample {sample_id} saved")
            return True

        except Exception as e:
            logger.error(f"Failed to add sample {sample_id}: {e}")
            return False

    async def validate_dataset(self, dataset_path: str) -> bool:
        """Validate that a dataset exists and is accessible"""
        path = Path(dataset_path)
        return path.exists() and path.is_dir()

    async def get_dataset_size(self, dataset_path: str) -> int:
        """Get number of samples in dataset"""
        path = Path(dataset_path)
        if not path.exists():
            return 0

        # Count JSON files
        json_files = list(path.glob("*.json"))
        return len(json_files)

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive dataset statistics

        Returns:
            Dictionary containing dataset stats
        """
        try:
            # Count samples in each category
            vba_macros_count = len(list(self.vba_macros_path.glob("*.vba")))
            api_references_count = len(list(self.api_references_path.glob("*.json")))
            geometry_samples_count = len(list(self.geometry_json_path.glob("*.json")))
            prompt_templates_count = len(list(self.prompts_path.glob("*.txt")))
            training_samples = list(self.training_samples_path.glob("*.json"))
            total_samples = len(training_samples)

            # Analyze API call distribution
            api_call_distribution = {}
            code_lengths = []

            for sample_file in training_samples:
                async with aiofiles.open(sample_file, 'r') as f:
                    content = await f.read()
                    sample = json.loads(content)

                    # Count API calls
                    for api_call in sample.get('api_calls', []):
                        api_call_distribution[api_call] = api_call_distribution.get(api_call, 0) + 1

                    # Track code lengths
                    code_lengths.append(len(sample.get('vba_code', '')))

            # Calculate code length statistics
            code_length_stats = {
                "min": min(code_lengths) if code_lengths else 0,
                "max": max(code_lengths) if code_lengths else 0,
                "mean": sum(code_lengths) / len(code_lengths) if code_lengths else 0,
            }

            dataset_info = {
                "total_samples": total_samples,
                "vba_macros_count": vba_macros_count,
                "api_references_count": api_references_count,
                "geometry_samples_count": geometry_samples_count,
                "prompt_templates_count": prompt_templates_count,
                "last_updated": datetime.utcnow()
            }

            return {
                "dataset_info": dataset_info,
                "api_call_distribution": api_call_distribution,
                "code_length_stats": code_length_stats,
                "timestamp": datetime.utcnow()
            }

        except Exception as e:
            logger.error(f"Failed to get dataset statistics: {e}")
            raise

    async def prepare_dataset(self, task_id: str):
        """
        Prepare and preprocess dataset for training

        This method:
        - Organizes VBA macros
        - Processes API references
        - Structures geometry JSON data
        - Creates training/validation splits
        """
        try:
            logger.info(f"Starting dataset preparation (task_id={task_id})")

            # Load all training samples
            samples = []
            for sample_file in self.training_samples_path.glob("*.json"):
                async with aiofiles.open(sample_file, 'r') as f:
                    content = await f.read()
                    samples.append(json.loads(content))

            logger.info(f"Loaded {len(samples)} training samples")

            # Create train/validation split (80/20)
            split_idx = int(len(samples) * 0.8)
            train_samples = samples[:split_idx]
            val_samples = samples[split_idx:]

            # Save splits
            train_file = self.base_path / "train.json"
            val_file = self.base_path / "validation.json"

            async with aiofiles.open(train_file, 'w') as f:
                await f.write(json.dumps(train_samples, indent=2))

            async with aiofiles.open(val_file, 'w') as f:
                await f.write(json.dumps(val_samples, indent=2))

            logger.info(f"Dataset preparation complete: {len(train_samples)} train, {len(val_samples)} validation")

        except Exception as e:
            logger.error(f"Dataset preparation failed: {e}", exc_info=True)
            raise

    async def load_api_references(self) -> List[Dict[str, Any]]:
        """Load SOLIDWORKS API reference data"""
        api_references = []

        for ref_file in self.api_references_path.glob("*.json"):
            async with aiofiles.open(ref_file, 'r') as f:
                content = await f.read()
                api_references.append(json.loads(content))

        return api_references

    async def save_vba_macro(self, name: str, code: str) -> bool:
        """Save a VBA macro to the dataset"""
        try:
            macro_file = self.vba_macros_path / f"{name}.vba"
            async with aiofiles.open(macro_file, 'w') as f:
                await f.write(code)
            logger.info(f"VBA macro {name} saved")
            return True
        except Exception as e:
            logger.error(f"Failed to save VBA macro: {e}")
            return False
