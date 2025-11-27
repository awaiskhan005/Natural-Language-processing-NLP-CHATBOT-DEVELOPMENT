# SOLIDWORKS VBA ML - Setup Guide

This guide will walk you through setting up the SOLIDWORKS VBA ML system from scratch.

## Table of Contents

1. [Environment Setup](#environment-setup)
2. [Local Development Setup](#local-development-setup)
3. [Docker Setup](#docker-setup)
4. [Dataset Preparation](#dataset-preparation)
5. [Training Your First Model](#training-your-first-model)
6. [Testing the API](#testing-the-api)
7. [Production Deployment](#production-deployment)

## Environment Setup

### System Requirements

**Minimum Requirements:**
- CPU: 4 cores
- RAM: 8GB
- Storage: 20GB free space
- OS: Linux, macOS, or Windows

**Recommended for Training:**
- CPU: 8+ cores
- RAM: 16GB+
- GPU: NVIDIA GPU with 8GB+ VRAM (for faster training)
- Storage: 50GB+ SSD
- OS: Linux (Ubuntu 20.04+)

### Software Prerequisites

1. **Python 3.10+**
```bash
python --version
# Should show Python 3.10.x or higher
```

2. **Git**
```bash
git --version
```

3. **CUDA (Optional, for GPU acceleration)**
```bash
nvidia-smi
# Should show CUDA version and GPU info
```

4. **Docker (Optional)**
```bash
docker --version
docker-compose --version
```

## Local Development Setup

### Step 1: Create Virtual Environment

```bash
# Navigate to project directory
cd solidworks-vba-ml

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Step 2: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# This will install:
# - FastAPI & Uvicorn (Web API)
# - PyTorch & Transformers (ML)
# - Loguru (Logging)
# - Pydantic (Data validation)
# - And more...
```

### Step 3: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your preferred settings
nano .env  # or use your favorite editor
```

**Key settings to configure:**

```bash
# API Settings
DEBUG=True                    # Set to False in production
PORT=8000                     # API port

# Model Settings
DEFAULT_MODEL=microsoft/codebert-base  # Base model for fine-tuning

# Training Settings
DEFAULT_BATCH_SIZE=8          # Reduce if out of memory
USE_LORA=True                 # Enable efficient fine-tuning
```

### Step 4: Verify Installation

```bash
# Test Python imports
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import transformers; print(f'Transformers: {transformers.__version__}')"
python -c "import fastapi; print(f'FastAPI: {fastapi.__version__}')"

# Check CUDA availability (if you have GPU)
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

### Step 5: Start the API

```bash
# Run the API server
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# You should see:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     🚀 Starting SOLIDWORKS VBA ML API
```

### Step 6: Test the API

Open your browser and navigate to:
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

You should see the Swagger UI with all available endpoints.

## Docker Setup

### Step 1: Build Docker Image

```bash
# Build the image
docker-compose build

# This will:
# - Create Python 3.10 environment
# - Install all dependencies
# - Set up the application
```

### Step 2: Start Services

```bash
# Start API and Redis
docker-compose up -d

# Check logs
docker-compose logs -f api
```

### Step 3: Verify Services

```bash
# Check running containers
docker ps

# Should show:
# - solidworks-vba-ml-api
# - solidworks-vba-ml-redis

# Test API
curl http://localhost:8000/health
```

### Step 4: Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Dataset Preparation

### Step 1: Understand Dataset Structure

```
datasets/
├── vba_macros/          # .vba files with VBA code
├── api_references/      # .json files with API documentation
├── geometry_json/       # .json files with geometry data
├── prompts/             # .txt files with prompt templates
└── training_samples/    # .json files with training samples
```

### Step 2: Create Sample VBA Macros

Create file: `datasets/vba_macros/create_circle.vba`

```vba
Sub CreateCircle()
    Dim swApp As SldWorks.SldWorks
    Dim swModel As SldWorks.ModelDoc2

    Set swApp = CreateObject("SldWorks.Application")
    Set swModel = swApp.ActiveDoc

    ' Insert sketch
    swModel.InsertSketch2 True

    ' Create circle at origin with radius 50mm
    swModel.CreateCircle2 0, 0, 0, 0.05

    ' Exit sketch
    swModel.InsertSketch2 False
End Sub
```

### Step 3: Create API Reference

Create file: `datasets/api_references/solidworks_sketch_api.json`

```json
{
  "swModel.InsertSketch2": {
    "description": "Inserts or exits a sketch",
    "parameters": ["edit_mode"],
    "return_type": "Boolean"
  },
  "swModel.CreateCircle2": {
    "description": "Creates a circle in the active sketch",
    "parameters": ["x", "y", "z", "radius"],
    "return_type": "SketchSegment"
  }
}
```

### Step 4: Submit Training Samples via API

```bash
# Using curl
curl -X POST http://localhost:8000/api/v1/training/samples \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a circle with radius 50mm at the origin",
    "vba_code": "Sub CreateCircle()\n    Dim swApp As SldWorks.SldWorks\n    Set swApp = CreateObject(\"SldWorks.Application\")\n    swModel.InsertSketch2 True\n    swModel.CreateCircle2 0, 0, 0, 0.05\n    swModel.InsertSketch2 False\nEnd Sub",
    "api_calls": ["swModel.InsertSketch2", "swModel.CreateCircle2"],
    "geometry_data": {
      "type": "circle",
      "center": [0, 0, 0],
      "radius": 50
    }
  }'
```

### Step 5: Prepare Dataset for Training

```bash
# This will organize and split your data
curl -X POST http://localhost:8000/api/v1/training/dataset/prepare

# Check dataset statistics
curl http://localhost:8000/api/v1/training/dataset/stats
```

## Training Your First Model

### Step 1: Submit Enough Training Samples

You need at least 50-100 training samples for meaningful training.

```bash
# Check how many samples you have
curl http://localhost:8000/api/v1/training/dataset/stats
```

### Step 2: Start Training Job

```bash
curl -X POST http://localhost:8000/api/v1/training/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_path": "datasets/train.json",
    "model_name": "microsoft/codebert-base",
    "num_epochs": 3,
    "batch_size": 8,
    "learning_rate": 2e-5,
    "output_dir": "models/checkpoints/my_first_model",
    "use_lora": true
  }'

# Response will include job_id
```

### Step 3: Monitor Training Progress

```bash
# Replace {job_id} with actual ID from step 2
curl http://localhost:8000/api/v1/training/jobs/{job_id}

# Response shows:
# - current_epoch
# - current_step
# - loss
# - estimated remaining time
```

### Step 4: Load Trained Model

```bash
# Once training is complete, load the model
curl -X POST http://localhost:8000/api/v1/generate/models/my_first_model/load
```

### Step 5: Generate Code with Your Model

```bash
curl -X POST http://localhost:8000/api/v1/generate/code \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a rectangle with width 100mm and height 50mm",
    "max_length": 512,
    "temperature": 0.7,
    "include_explanation": true
  }'
```

## Testing the API

### Health Check

```bash
curl http://localhost:8000/health
```

### Generate Code

```bash
curl -X POST http://localhost:8000/api/v1/generate/code \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Draw a circle",
    "max_length": 256
  }'
```

### Validate Code

```bash
curl -X POST http://localhost:8000/api/v1/validate/vba \
  -H "Content-Type: application/json" \
  -d '{
    "code": "Sub Test()\nEnd Sub",
    "strict_mode": true
  }'
```

### Evaluate Model

```bash
curl -X POST http://localhost:8000/api/v1/evaluate/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "test_samples": [
      {
        "prompt": "Create a circle",
        "vba_code": "Sub CreateCircle()...",
        "api_calls": ["swModel.CreateCircle2"]
      }
    ],
    "metrics_to_compute": ["accuracy", "syntax_validity"]
  }'
```

## Production Deployment

### 1. Update Environment for Production

```bash
# In .env
DEBUG=False
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### 2. Use Production Server

Instead of uvicorn directly, use gunicorn:

```bash
pip install gunicorn

gunicorn api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### 3. Set Up Nginx (Reverse Proxy)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 4. Enable HTTPS

```bash
# Using Let's Encrypt
sudo certbot --nginx -d your-domain.com
```

### 5. Set Up Monitoring

- Use Prometheus for metrics
- Set up Grafana dashboards
- Configure log aggregation

### 6. Backup Strategy

```bash
# Backup models
tar -czf models-backup-$(date +%Y%m%d).tar.gz models/

# Backup datasets
tar -czf datasets-backup-$(date +%Y%m%d).tar.gz datasets/

# Backup logs
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/
```

## Troubleshooting

### Issue: Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
uvicorn api.main:app --port 8001
```

### Issue: CUDA Out of Memory

```bash
# Reduce batch size in .env
DEFAULT_BATCH_SIZE=4

# Or disable CUDA and use CPU
CUDA_VISIBLE_DEVICES="" python -m uvicorn api.main:app
```

### Issue: Module Not Found

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall requirements
pip install -r requirements.txt
```

### Issue: Model Download Fails

```bash
# Set HuggingFace cache directory
export HF_HOME=/path/to/large/storage

# Or use offline mode with pre-downloaded models
export TRANSFORMERS_OFFLINE=1
```

## Next Steps

1. ✅ API is running
2. ✅ Dataset is prepared
3. ✅ First model is trained
4. ⬜ Collect more training data
5. ⬜ Fine-tune with larger dataset
6. ⬜ Deploy to production
7. ⬜ Set up monitoring and alerts

## Getting Help

- Check logs: `tail -f logs/api.log`
- API documentation: http://localhost:8000/docs
- Project README: See README.md

---

**You're all set! Start building your SOLIDWORKS VBA automation system.**
