"""
Validation API Routes
Endpoints for validating VBA code and API calls
"""

from fastapi import APIRouter, HTTPException
from loguru import logger
from datetime import datetime

from api.models import (
    ValidationRequest,
    ValidationResponse,
    CodeTestRequest,
    CodeTestResponse
)
from validation.vba_validator import VBAValidator
from validation.api_validator import APIValidator
from validation.code_tester import CodeTester
import uuid
import time

router = APIRouter()
vba_validator = VBAValidator()
api_validator = APIValidator()
code_tester = CodeTester()


@router.post("/vba", response_model=ValidationResponse)
async def validate_vba_code(request: ValidationRequest):
    """
    Validate VBA code for syntax and API call correctness

    This endpoint:
    - Checks VBA syntax
    - Validates SOLIDWORKS API calls
    - Detects common errors and warnings
    - Returns detailed validation results
    """
    try:
        logger.info(f"Validating VBA code (strict={request.strict_mode})")

        # Syntax validation
        syntax_result = await vba_validator.validate_syntax(
            code=request.code,
            strict=request.strict_mode
        )

        # API call validation
        api_calls = []
        if request.check_api_calls:
            api_calls = await api_validator.validate_api_calls(request.code)

        # Collect errors and warnings
        errors = syntax_result.get('errors', [])
        warnings = syntax_result.get('warnings', [])

        is_valid = len(errors) == 0 and syntax_result.get('syntax_valid', False)

        logger.info(f"Validation complete: valid={is_valid}, errors={len(errors)}, warnings={len(warnings)}")

        return ValidationResponse(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            api_calls_found=api_calls,
            syntax_valid=syntax_result.get('syntax_valid', False),
            timestamp=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.post("/test", response_model=CodeTestResponse)
async def test_code(request: CodeTestRequest):
    """
    Test VBA code execution

    This endpoint executes the VBA code in a controlled environment
    and returns the results, output, and any errors.
    """
    try:
        test_id = str(uuid.uuid4())
        logger.info(f"Testing code (test_id={test_id})")

        start_time = time.time()

        # Execute code in test environment
        test_result = await code_tester.execute_code(
            code=request.code,
            context=request.test_context,
            timeout=request.timeout_seconds
        )

        execution_time = (time.time() - start_time) * 1000  # Convert to ms

        success = test_result.get('success', False)
        output = test_result.get('output')
        errors = test_result.get('errors', [])

        logger.info(f"Test {test_id} completed: success={success}, time={execution_time:.2f}ms")

        return CodeTestResponse(
            test_id=test_id,
            success=success,
            output=output,
            errors=errors,
            execution_time_ms=execution_time,
            timestamp=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Code testing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Code testing failed: {str(e)}")


@router.get("/api-reference")
async def get_api_reference():
    """
    Get SOLIDWORKS API reference information

    Returns a list of valid SOLIDWORKS API calls and their documentation.
    """
    try:
        api_reference = await api_validator.get_api_reference()

        return {
            "api_calls": api_reference,
            "total_count": len(api_reference),
            "timestamp": datetime.utcnow()
        }

    except Exception as e:
        logger.error(f"Failed to get API reference: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api-reference/validate-call")
async def validate_api_call(api_call: str):
    """
    Validate a specific SOLIDWORKS API call

    Returns whether the API call is valid and provides documentation.
    """
    try:
        result = await api_validator.validate_single_call(api_call)

        return {
            "api_call": api_call,
            "is_valid": result.get('is_valid', False),
            "documentation": result.get('documentation'),
            "parameters": result.get('parameters', []),
            "return_type": result.get('return_type'),
            "timestamp": datetime.utcnow()
        }

    except Exception as e:
        logger.error(f"Failed to validate API call: {e}")
        raise HTTPException(status_code=500, detail=str(e))
