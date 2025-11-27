"""
Training API Routes
Endpoints for training and managing ML models
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from loguru import logger
from datetime import datetime
import uuid

from api.models import (
    TrainingSampleRequest,
    TrainingSampleResponse,
    TrainingJobRequest,
    TrainingJobResponse,
    TrainingProgressResponse,
    TrainingStatus,
    DatasetStatsResponse
)
from training.trainer import ModelTrainer
from utils.dataset_manager import DatasetManager

router = APIRouter()
trainer = ModelTrainer()
dataset_manager = DatasetManager()


@router.post("/samples", response_model=TrainingSampleResponse)
async def submit_training_sample(sample: TrainingSampleRequest):
    """
    Submit a new training sample to the dataset

    This endpoint receives training samples including:
    - Natural language prompts
    - Corresponding VBA code
    - API calls used
    - Geometry data (optional)
    """
    try:
        sample_id = str(uuid.uuid4())

        # Save sample to dataset
        await dataset_manager.add_sample(
            sample_id=sample_id,
            prompt=sample.prompt,
            vba_code=sample.vba_code,
            api_calls=sample.api_calls,
            geometry_data=sample.geometry_data,
            metadata=sample.metadata
        )

        logger.info(f"Training sample {sample_id} added successfully")

        return TrainingSampleResponse(
            sample_id=sample_id,
            status="success",
            message="Training sample added successfully",
            timestamp=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Failed to add training sample: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to add sample: {str(e)}")


@router.post("/jobs", response_model=TrainingJobResponse)
async def start_training_job(
    request: TrainingJobRequest,
    background_tasks: BackgroundTasks
):
    """
    Start a new training job

    This endpoint initiates model training with the specified configuration.
    Training runs in the background and can be monitored via the progress endpoint.
    """
    try:
        job_id = str(uuid.uuid4())

        # Validate dataset exists
        dataset_exists = await dataset_manager.validate_dataset(request.dataset_path)
        if not dataset_exists:
            raise HTTPException(status_code=404, detail="Dataset not found")

        # Estimate training time
        dataset_size = await dataset_manager.get_dataset_size(request.dataset_path)
        estimated_time = trainer.estimate_training_time(
            dataset_size=dataset_size,
            num_epochs=request.num_epochs,
            batch_size=request.batch_size
        )

        # Start training in background
        background_tasks.add_task(
            trainer.train,
            job_id=job_id,
            dataset_path=request.dataset_path,
            model_name=request.model_name,
            num_epochs=request.num_epochs,
            batch_size=request.batch_size,
            learning_rate=request.learning_rate,
            output_dir=request.output_dir,
            use_lora=request.use_lora
        )

        logger.info(f"Training job {job_id} started")

        return TrainingJobResponse(
            job_id=job_id,
            status=TrainingStatus.QUEUED,
            message="Training job started successfully",
            estimated_time_minutes=estimated_time,
            timestamp=datetime.utcnow()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start training job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start training: {str(e)}")


@router.get("/jobs/{job_id}", response_model=TrainingProgressResponse)
async def get_training_progress(job_id: str):
    """
    Get training job progress

    Returns current status, metrics, and progress information for a training job.
    """
    try:
        progress = await trainer.get_progress(job_id)

        if not progress:
            raise HTTPException(status_code=404, detail="Training job not found")

        return TrainingProgressResponse(**progress)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get training progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/jobs/{job_id}")
async def cancel_training_job(job_id: str):
    """
    Cancel a running training job
    """
    try:
        success = await trainer.cancel_job(job_id)

        if not success:
            raise HTTPException(status_code=404, detail="Training job not found or already completed")

        return {
            "status": "success",
            "message": f"Training job {job_id} cancelled",
            "timestamp": datetime.utcnow()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel training job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dataset/stats", response_model=DatasetStatsResponse)
async def get_dataset_statistics():
    """
    Get statistics about the training dataset

    Returns information about:
    - Total samples
    - VBA macros count
    - API references
    - Geometry samples
    - API call distribution
    - Code length statistics
    """
    try:
        stats = await dataset_manager.get_statistics()
        return DatasetStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Failed to get dataset stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dataset/prepare")
async def prepare_dataset(background_tasks: BackgroundTasks):
    """
    Prepare and preprocess the dataset for training

    This endpoint:
    - Organizes VBA macros
    - Processes API references
    - Structures geometry JSON data
    - Creates training/validation splits
    """
    try:
        task_id = str(uuid.uuid4())

        background_tasks.add_task(dataset_manager.prepare_dataset, task_id)

        return {
            "task_id": task_id,
            "status": "queued",
            "message": "Dataset preparation started",
            "timestamp": datetime.utcnow()
        }

    except Exception as e:
        logger.error(f"Failed to start dataset preparation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
