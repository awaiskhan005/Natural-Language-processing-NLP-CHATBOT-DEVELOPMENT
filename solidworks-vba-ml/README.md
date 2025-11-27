# SOLIDWORKS VBA ML System

A complete machine learning system for training, fine-tuning, and generating SOLIDWORKS VBA automation code using PyTorch and transformers.

## Features

- **FastAPI Web API** - RESTful API for model interaction
- **PyTorch Training Pipeline** - Fine-tune code generation models
- **LoRA Support** - Efficient fine-tuning with parameter-efficient methods
- **VBA Validation** - Syntax and API call validation
- **Code Testing** - Execute and test generated code
- **Dataset Management** - Organize VBA macros, API references, and geometry data
- **Model Evaluation** - Comprehensive metrics and performance tracking
- **Docker Support** - Easy deployment with Docker Compose

## Architecture

```
solidworks-vba-ml/
├── api/                    # FastAPI application
│   ├── routes/            # API endpoints
│   ├── models.py          # Pydantic models
│   └── main.py            # Main application
├── training/              # PyTorch training pipeline
│   ├── trainer.py         # Model trainer
│   └── evaluator.py       # Model evaluator
├── validation/            # Code validation
│   ├── vba_validator.py   # VBA syntax validator
│   ├── api_validator.py   # API call validator
│   └── code_tester.py     # Code execution tester
├── utils/                 # Utilities
│   ├── model_manager.py   # Model loading and inference
│   ├── dataset_manager.py # Dataset organization
│   └── logger.py          # Logging configuration
├── datasets/              # Training data
│   ├── vba_macros/        # VBA macro files
│   ├── api_references/    # SOLIDWORKS API docs
│   ├── geometry_json/     # Geometry data
│   ├── prompts/           # Prompt templates
│   └── training_samples/  # Training samples
├── models/                # Model storage
│   ├── checkpoints/       # Training checkpoints
│   ├── cache/             # Model cache
│   └── exports/           # Exported models
└── config/                # Configuration
    └── settings.py        # Application settings
```

## Quick Start

### Prerequisites

- Python 3.10+
- CUDA (optional, for GPU acceleration)
- Docker & Docker Compose (optional)

### Installation

1. **Clone the repository**
```bash
cd solidworks-vba-ml
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

5. **Run the API**
```bash
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

6. **Access API documentation**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Docker Deployment

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## API Endpoints

### Code Generation

**Generate VBA Code**
```bash
POST /api/v1/generate/code
```
```json
{
  "prompt": "Create a circle with radius 50mm at origin",
  "max_length": 512,
  "temperature": 0.7,
  "include_explanation": true
}
```

### Training

**Submit Training Sample**
```bash
POST /api/v1/training/samples
```
```json
{
  "prompt": "Draw a rectangle",
  "vba_code": "Sub DrawRectangle()...",
  "api_calls": ["swModel.CreateLine2"],
  "geometry_data": {}
}
```

**Start Training Job**
```bash
POST /api/v1/training/jobs
```
```json
{
  "dataset_path": "datasets/train.json",
  "model_name": "microsoft/codebert-base",
  "num_epochs": 3,
  "batch_size": 8,
  "use_lora": true
}
```

**Get Training Progress**
```bash
GET /api/v1/training/jobs/{job_id}
```

### Validation

**Validate VBA Code**
```bash
POST /api/v1/validate/vba
```
```json
{
  "code": "Sub Example()...",
  "strict_mode": true,
  "check_api_calls": true
}
```

**Test Code Execution**
```bash
POST /api/v1/validate/test
```
```json
{
  "code": "Sub Example()...",
  "timeout_seconds": 30
}
```

### Evaluation

**Evaluate Model**
```bash
POST /api/v1/evaluate/evaluate
```
```json
{
  "test_samples": [...],
  "metrics_to_compute": ["accuracy", "syntax_validity"]
}
```

## Dataset Preparation

### 1. VBA Macros

Save VBA macro files in `datasets/vba_macros/`:

```vba
' example_circle.vba
Sub CreateCircle()
    Dim swApp As SldWorks.SldWorks
    Dim swModel As SldWorks.ModelDoc2

    Set swApp = CreateObject("SldWorks.Application")
    Set swModel = swApp.ActiveDoc

    swModel.InsertSketch2 True
    swModel.CreateCircle2 0, 0, 0, 0.05
    swModel.InsertSketch2 False
End Sub
```

### 2. API References

Create JSON files in `datasets/api_references/`:

```json
{
  "swModel.CreateCircle2": {
    "description": "Creates a circle in a sketch",
    "parameters": ["x", "y", "z", "radius"],
    "return_type": "SketchSegment"
  }
}
```

### 3. Training Samples

Submit samples via API or create JSON files in `datasets/training_samples/`:

```json
{
  "sample_id": "uuid",
  "prompt": "Create a circle with radius 50mm",
  "vba_code": "Sub CreateCircle()...",
  "api_calls": ["swModel.CreateCircle2"],
  "geometry_data": {"type": "circle", "radius": 50}
}
```

## Training Workflow

1. **Prepare Dataset**
```bash
curl -X POST http://localhost:8000/api/v1/training/dataset/prepare
```

2. **Start Training**
```bash
curl -X POST http://localhost:8000/api/v1/training/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_path": "datasets/train.json",
    "model_name": "microsoft/codebert-base",
    "num_epochs": 3,
    "batch_size": 8,
    "learning_rate": 2e-5,
    "use_lora": true
  }'
```

3. **Monitor Progress**
```bash
curl http://localhost:8000/api/v1/training/jobs/{job_id}
```

4. **Load Trained Model**
```bash
curl -X POST http://localhost:8000/api/v1/generate/models/your-model-name/load
```

## Model Fine-Tuning

### Supported Models

- **microsoft/codebert-base** (Recommended for starting)
- **Salesforce/codegen-350M-mono**
- **Salesforce/codegen-2B-mono**
- **codellama/CodeLlama-7b-hf**
- **WizardLM/WizardCoder-15B-V1.0**

### LoRA Configuration

LoRA (Low-Rank Adaptation) enables efficient fine-tuning:

```python
# In config/settings.py
USE_LORA = True
LORA_R = 8           # Rank
LORA_ALPHA = 16      # Alpha scaling
LORA_DROPOUT = 0.05  # Dropout rate
```

Benefits:
- Reduces trainable parameters by 90%+
- Faster training
- Lower memory requirements
- Easy model switching

## Validation System

### VBA Syntax Validation

The system validates:
- Sub/Function block matching
- Control flow statements
- Variable declarations
- VBA keyword usage
- Best practices

### API Call Validation

Ensures generated code uses valid SOLIDWORKS API calls:
- Checks against API reference database
- Validates method signatures
- Detects incorrect API usage

### Code Testing

Execute generated code in a controlled environment:
- Syntax checking
- Runtime error detection
- Output validation

## Evaluation Metrics

- **Accuracy** - Percentage of correct code generations
- **Syntax Validity Rate** - Percentage of syntactically valid code
- **API Call Accuracy** - Percentage of correct API usage
- **Generation Time** - Average time to generate code

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black .
```

### Linting

```bash
pylint api/ training/ validation/ utils/
```

## Project Requirements

This system is designed to meet the following requirements:

- ✅ **ML/AI Development** - PyTorch-based training pipeline
- ✅ **Model Fine-Tuning** - LoRA and full fine-tuning support
- ✅ **Web API** - FastAPI RESTful API
- ✅ **Dataset Management** - VBA macros, API references, geometry data
- ✅ **Code Validation** - Verification system for valid API calls
- ✅ **Testing Pipeline** - Code generation and evaluation
- ✅ **Logging** - Comprehensive logging with loguru
- ✅ **Production Ready** - Docker deployment, health checks

## Next Steps

### Immediate Tasks

1. **Collect Training Data**
   - Gather VBA macros from SOLIDWORKS projects
   - Document SOLIDWORKS API calls
   - Create geometry JSON datasets

2. **Train Initial Model**
   - Prepare dataset with 100+ samples
   - Fine-tune CodeBERT or CodeGen model
   - Evaluate on test set

3. **Deploy API**
   - Configure production settings
   - Set up monitoring
   - Deploy with Docker

### Future Enhancements

- [ ] Add more sophisticated code testing (actual SOLIDWORKS execution)
- [ ] Implement code similarity detection
- [ ] Add multi-turn conversation support
- [ ] Create web dashboard for monitoring
- [ ] Add support for other CAD platforms
- [ ] Implement automated data collection from existing projects

## Troubleshooting

### Common Issues

**1. CUDA Out of Memory**
```python
# Reduce batch size in .env
DEFAULT_BATCH_SIZE=4

# Enable gradient accumulation
gradient_accumulation_steps=4
```

**2. Model Loading Fails**
```bash
# Clear model cache
rm -rf models/cache/*

# Re-download model
python -c "from utils.model_manager import ModelManager; import asyncio; asyncio.run(ModelManager().load_model('microsoft/codebert-base'))"
```

**3. API Connection Refused**
```bash
# Check if port is available
lsof -i :8000

# Run on different port
uvicorn api.main:app --port 8001
```

## Contributing

This is an internal project. For issues or suggestions, please contact the development team.

## License

Proprietary - Internal Use Only

## Support

For questions or issues:
- Create an issue in the project repository
- Contact via Slack
- Email: [your-email]

---

**Built with ❤️ for SOLIDWORKS automation**
