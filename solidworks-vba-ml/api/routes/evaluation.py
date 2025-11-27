"""
Evaluation API Routes
Endpoints for evaluating model performance
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from loguru import logger
from datetime import datetime
import uuid

from api.models import (
    EvaluationRequest,
    EvaluationResponse,
    EvaluationMetrics
)
from training.evaluator import ModelEvaluator

router = APIRouter()
evaluator = ModelEvaluator()


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_model(request: EvaluationRequest, background_tasks: BackgroundTasks):
    """
    Evaluate model performance on test samples

    This endpoint:
    - Tests model on provided samples
    - Computes accuracy metrics
    - Validates syntax of generated code
    - Checks API call correctness
    - Measures generation time
    """
    try:
        evaluation_id = str(uuid.uuid4())

        logger.info(f"Starting evaluation {evaluation_id} with {len(request.test_samples)} samples")

        # Run evaluation
        results = await evaluator.evaluate(
            evaluation_id=evaluation_id,
            test_samples=request.test_samples,
            metrics=request.metrics_to_compute
        )

        # Compute metrics
        metrics = EvaluationMetrics(
            total_samples=len(request.test_samples),
            accuracy=results.get('accuracy', 0.0),
            syntax_validity_rate=results.get('syntax_validity_rate', 0.0),
            api_call_accuracy=results.get('api_call_accuracy', 0.0),
            average_generation_time_ms=results.get('average_generation_time_ms', 0.0)
        )

        logger.info(f"Evaluation {evaluation_id} completed: accuracy={metrics.accuracy:.2%}")

        return EvaluationResponse(
            evaluation_id=evaluation_id,
            metrics=metrics,
            detailed_results=results.get('detailed_results', []),
            timestamp=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@router.get("/evaluations/{evaluation_id}")
async def get_evaluation_results(evaluation_id: str):
    """
    Get results from a previous evaluation
    """
    try:
        results = await evaluator.get_results(evaluation_id)

        if not results:
            raise HTTPException(status_code=404, detail="Evaluation not found")

        return {
            "evaluation_id": evaluation_id,
            "results": results,
            "timestamp": datetime.utcnow()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get evaluation results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/history")
async def get_metrics_history(limit: int = 10):
    """
    Get historical evaluation metrics

    Returns metrics from recent evaluations for tracking model performance over time.
    """
    try:
        history = await evaluator.get_metrics_history(limit=limit)

        return {
            "history": history,
            "count": len(history),
            "timestamp": datetime.utcnow()
        }

    except Exception as e:
        logger.error(f"Failed to get metrics history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
