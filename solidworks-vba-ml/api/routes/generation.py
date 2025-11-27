"""
Code Generation API Routes
Endpoints for generating VBA code from natural language prompts
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from loguru import logger
from datetime import datetime
import time
import uuid

from api.models import (
    CodeGenerationRequest,
    CodeGenerationResponse,
    GeneratedCode
)
from utils.model_manager import ModelManager
from validation.vba_validator import VBAValidator

router = APIRouter()
model_manager = ModelManager()
vba_validator = VBAValidator()


@router.post("/code", response_model=CodeGenerationResponse)
async def generate_vba_code(request: CodeGenerationRequest):
    """
    Generate VBA code from natural language description

    This endpoint uses the trained model to generate SOLIDWORKS VBA code
    based on the provided prompt.
    """
    start_time = time.time()
    request_id = str(uuid.uuid4())

    logger.info(f"Code generation request {request_id}: {request.prompt[:100]}")

    try:
        # Load model
        model = await model_manager.get_model()

        # Generate code
        generated_outputs = await model_manager.generate_code(
            prompt=request.prompt,
            max_length=request.max_length,
            temperature=request.temperature,
            top_p=request.top_p,
            num_return_sequences=request.num_return_sequences
        )

        # Process generated codes
        generated_codes = []
        for output in generated_outputs:
            code = output['code']

            # Detect API calls
            api_calls = vba_validator.extract_api_calls(code)

            # Calculate confidence score
            confidence = output.get('confidence_score', 0.0)

            # Generate explanation if requested
            explanation = None
            if request.include_explanation:
                explanation = await model_manager.generate_explanation(code)

            generated_codes.append(GeneratedCode(
                code=code,
                confidence_score=confidence,
                api_calls_detected=api_calls,
                explanation=explanation
            ))

        generation_time = (time.time() - start_time) * 1000  # Convert to ms

        logger.info(f"Generated {len(generated_codes)} code samples in {generation_time:.2f}ms")

        return CodeGenerationResponse(
            request_id=request_id,
            generated_codes=generated_codes,
            generation_time_ms=generation_time,
            model_version=model_manager.model_version,
            timestamp=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Code generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Code generation failed: {str(e)}")


@router.get("/models")
async def list_available_models():
    """List all available models for code generation"""
    try:
        models = await model_manager.list_models()
        return {
            "models": models,
            "current_model": model_manager.current_model_name,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/{model_name}/load")
async def load_model(model_name: str):
    """Load a specific model for code generation"""
    try:
        logger.info(f"Loading model: {model_name}")
        await model_manager.load_model(model_name)
        return {
            "status": "success",
            "message": f"Model {model_name} loaded successfully",
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Failed to load model {model_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
