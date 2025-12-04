# RodeoAI GPU API

FastAPI-based GPU API for rodeo analytics and predictions, optimized for RunPod deployment.

## Features

- 🚀 FastAPI with async support
- 🔐 API key authentication
- 📊 Prediction endpoints (single and batch)
- 🏥 Health check and GPU info endpoints
- 🎯 Optimized for RunPod L40S deployment

## Endpoints

### Root
- `GET /` - API information

### Health
- `GET /health` - Health check with GPU status

### Predictions
- `POST /predict` - Single prediction
- `POST /batch_predict` - Batch predictions

### GPU Info
- `GET /gpu_info` - GPU information

### RunPod Handler
- `POST /runsync` - RunPod serverless handler

## RunPod Deployment

### 1. Create Serverless Endpoint

Go to RunPod → Serverless → Create Endpoint

### 2. Configuration

**GitHub Repository:**
```
https://github.com/dataspur/rodeoai-gpu-api
```

**Start Command:**
```
uvicorn app:app --host 0.0.0.0 --port 8000
```

**Environment Variables:**
```
GPU_API_KEY=your-secret-key-here
```

**GPU Type:** L40S (or any NVIDIA GPU)

### 3. Test Your Endpoint

Once deployed, test with:

```bash
# Health check
curl https://YOUR-ENDPOINT.runpod.io/health

# Prediction
curl -X POST "https://YOUR-ENDPOINT.runpod.io/predict" \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{
    "event_type": "bull_riding",
    "rider_stats": {
      "wins": 25,
      "average_score": 85
    },
    "animal_stats": {
      "buck_score": 45
    }
  }'
```

## Local Development

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run Locally
```bash
python app.py
```

Or with uvicorn:
```bash
uvicorn app:app --reload
```

### Test Locally
Visit http://localhost:8000/docs for interactive API documentation.

## Docker Build

```bash
docker build -t rodeoai-gpu-api .
docker run -p 8000:8000 -e GPU_API_KEY=your-key rodeoai-gpu-api
```

## API Key Security

Set the `GPU_API_KEY` environment variable in your RunPod endpoint settings. All prediction endpoints require this key in the `x-api-key` header.

## License

Proprietary - DataSpur/RodeoAI