"""
Pydantic models for API request/response validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    message: str
    version: str
    timestamp: datetime


class TrainingSampleRequest(BaseModel):
    """Request model for submitting training samples"""
    prompt: str = Field(..., description="Natural language description of VBA task")
    vba_code: str = Field(..., description="Corresponding VBA code")
    api_calls: List[str] = Field(default=[], description="SOLIDWORKS API calls used")
    geometry_data: Optional[Dict[str, Any]] = Field(None, description="Geometry JSON data")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    @validator('prompt')
    def validate_prompt(cls, v):
        if len(v.strip()) < 10:
            raise ValueError("Prompt must be at least 10 characters")
        return v.strip()

    @validator('vba_code')
    def validate_vba_code(cls, v):
        if len(v.strip()) < 5:
            raise ValueError("VBA code must be at least 5 characters")
        return v.strip()


class TrainingSampleResponse(BaseModel):
    """Response after submitting training sample"""
    sample_id: str
    status: str
    message: str
    timestamp: datetime


class CodeGenerationRequest(BaseModel):
    """Request model for generating VBA code"""
    prompt: str = Field(..., description="Natural language description")
    max_length: int = Field(512, ge=50, le=2048, description="Max tokens to generate")
    temperature: float = Field(0.7, ge=0.1, le=2.0, description="Sampling temperature")
    top_p: float = Field(0.9, ge=0.1, le=1.0, description="Nucleus sampling")
    num_return_sequences: int = Field(1, ge=1, le=5, description="Number of sequences")
    include_explanation: bool = Field(False, description="Include code explanation")

    @validator('prompt')
    def validate_prompt(cls, v):
        if len(v.strip()) < 5:
            raise ValueError("Prompt must be at least 5 characters")
        return v.strip()


class GeneratedCode(BaseModel):
    """Single generated code output"""
    code: str
    confidence_score: float
    api_calls_detected: List[str]
    explanation: Optional[str] = None


class CodeGenerationResponse(BaseModel):
    """Response from code generation"""
    request_id: str
    generated_codes: List[GeneratedCode]
    generation_time_ms: float
    model_version: str
    timestamp: datetime


class ValidationRequest(BaseModel):
    """Request to validate VBA code"""
    code: str = Field(..., description="VBA code to validate")
    strict_mode: bool = Field(True, description="Enable strict validation")
    check_api_calls: bool = Field(True, description="Validate API calls")


class ValidationError(BaseModel):
    """Validation error details"""
    line_number: Optional[int]
    error_type: str
    message: str
    severity: str  # "error", "warning", "info"


class ValidationResponse(BaseModel):
    """Response from code validation"""
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]
    api_calls_found: List[str]
    syntax_valid: bool
    timestamp: datetime


class CodeTestRequest(BaseModel):
    """Request to test generated code"""
    code: str = Field(..., description="VBA code to test")
    test_context: Optional[Dict[str, Any]] = Field(None, description="Test context data")
    timeout_seconds: int = Field(30, ge=5, le=300, description="Test timeout")


class CodeTestResponse(BaseModel):
    """Response from code testing"""
    test_id: str
    success: bool
    output: Optional[str]
    errors: List[str]
    execution_time_ms: float
    timestamp: datetime


class EvaluationMetrics(BaseModel):
    """Model evaluation metrics"""
    total_samples: int
    accuracy: float
    syntax_validity_rate: float
    api_call_accuracy: float
    average_generation_time_ms: float


class EvaluationRequest(BaseModel):
    """Request to evaluate model performance"""
    test_samples: List[TrainingSampleRequest]
    metrics_to_compute: List[str] = Field(
        default=["accuracy", "syntax_validity", "api_call_accuracy"],
        description="Metrics to compute"
    )


class EvaluationResponse(BaseModel):
    """Response from model evaluation"""
    evaluation_id: str
    metrics: EvaluationMetrics
    detailed_results: List[Dict[str, Any]]
    timestamp: datetime


class TrainingStatus(str, Enum):
    """Training job status"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TrainingJobRequest(BaseModel):
    """Request to start a training job"""
    dataset_path: str = Field(..., description="Path to training dataset")
    model_name: str = Field("microsoft/codebert-base", description="Base model to fine-tune")
    num_epochs: int = Field(3, ge=1, le=50, description="Number of training epochs")
    batch_size: int = Field(8, ge=1, le=64, description="Training batch size")
    learning_rate: float = Field(2e-5, ge=1e-6, le=1e-3, description="Learning rate")
    output_dir: str = Field("models/checkpoints", description="Output directory")
    use_lora: bool = Field(True, description="Use LoRA for efficient fine-tuning")


class TrainingJobResponse(BaseModel):
    """Response after starting training job"""
    job_id: str
    status: TrainingStatus
    message: str
    estimated_time_minutes: Optional[int]
    timestamp: datetime


class TrainingProgressResponse(BaseModel):
    """Training progress information"""
    job_id: str
    status: TrainingStatus
    current_epoch: int
    total_epochs: int
    current_step: int
    total_steps: int
    loss: Optional[float]
    learning_rate: Optional[float]
    elapsed_time_seconds: float
    estimated_remaining_seconds: Optional[float]
    timestamp: datetime


class DatasetInfo(BaseModel):
    """Dataset information"""
    total_samples: int
    vba_macros_count: int
    api_references_count: int
    geometry_samples_count: int
    prompt_templates_count: int
    last_updated: datetime


class DatasetStatsResponse(BaseModel):
    """Response with dataset statistics"""
    dataset_info: DatasetInfo
    api_call_distribution: Dict[str, int]
    code_length_stats: Dict[str, float]
    timestamp: datetime
