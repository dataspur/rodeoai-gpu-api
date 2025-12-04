from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import torch
import logging
from datetime import datetime
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RodeoAI GPU API",
    description="GPU-accelerated API for rodeo analytics and predictions",
    version="1.0.0"
)

# Check if CUDA is available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
logger.info(f"Using device: {device}")

# Request/Response Models
class PredictionRequest(BaseModel):
    event_type: str  # bull_riding, saddle_bronc, bareback, etc.
    rider_stats: Dict[str, Any]
    animal_stats: Optional[Dict[str, Any]] = None
    conditions: Optional[Dict[str, Any]] = None

class BatchPredictionRequest(BaseModel):
    predictions: List[PredictionRequest]

class PredictionResponse(BaseModel):
    prediction_score: float
    confidence: float
    factors: Dict[str, float]
    timestamp: str
    device_used: str

class ModelTrainingRequest(BaseModel):
    data: List[Dict[str, Any]]
    model_type: str
    epochs: Optional[int] = 10
    batch_size: Optional[int] = 32

class HealthResponse(BaseModel):
    status: str
    gpu_available: bool
    gpu_name: Optional[str] = None
    cuda_version: Optional[str] = None
    memory_allocated: Optional[float] = None
    memory_reserved: Optional[float] = None

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "RodeoAI GPU API",
        "version": "1.0.0",
        "description": "GPU-accelerated rodeo analytics",
        "device": str(device)
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API health and GPU status"""
    response = {
        "status": "healthy",
        "gpu_available": torch.cuda.is_available()
    }

    if torch.cuda.is_available():
        response.update({
            "gpu_name": torch.cuda.get_device_name(0),
            "cuda_version": torch.version.cuda,
            "memory_allocated": round(torch.cuda.memory_allocated(0) / 1024**3, 2),  # GB
            "memory_reserved": round(torch.cuda.memory_reserved(0) / 1024**3, 2)  # GB
        })

    return response

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    Make a single prediction using GPU acceleration
    """
    try:
        # Simulate GPU computation
        logger.info(f"Processing prediction for {request.event_type}")

        # Convert input to tensors
        features = []
        for key, value in request.rider_stats.items():
            if isinstance(value, (int, float)):
                features.append(float(value))

        if request.animal_stats:
            for key, value in request.animal_stats.items():
                if isinstance(value, (int, float)):
                    features.append(float(value))

        # Create tensor and move to GPU
        input_tensor = torch.tensor(features, dtype=torch.float32).to(device)

        # Simulate neural network forward pass
        with torch.no_grad():
            # This is a placeholder - replace with actual model
            weights = torch.randn(len(features), 1).to(device)
            output = torch.sigmoid(torch.matmul(input_tensor, weights))
            prediction_score = output.item()

        # Calculate confidence (placeholder logic)
        confidence = min(0.95, abs(prediction_score - 0.5) * 2 + 0.5)

        # Feature importance (placeholder)
        factors = {
            "rider_experience": 0.35,
            "recent_performance": 0.25,
            "event_conditions": 0.20,
            "historical_matchup": 0.20
        }

        return PredictionResponse(
            prediction_score=prediction_score,
            confidence=confidence,
            factors=factors,
            timestamp=datetime.now().isoformat(),
            device_used=str(device)
        )

    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/batch_predict", response_model=List[PredictionResponse])
async def batch_predict(request: BatchPredictionRequest):
    """
    Process multiple predictions in parallel on GPU
    """
    try:
        logger.info(f"Processing batch of {len(request.predictions)} predictions")

        results = []
        for pred_request in request.predictions:
            result = await predict(pred_request)
            results.append(result)

        return results

    except Exception as e:
        logger.error(f"Batch prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/train", response_model=Dict[str, Any])
async def train_model(request: ModelTrainingRequest):
    """
    Train a model on GPU (placeholder endpoint)
    """
    try:
        logger.info(f"Training {request.model_type} model with {len(request.data)} samples")

        # Placeholder for actual training logic
        # In production, this would:
        # 1. Prepare data
        # 2. Initialize model
        # 3. Run training loop on GPU
        # 4. Save model weights

        return {
            "status": "success",
            "model_type": request.model_type,
            "samples_trained": len(request.data),
            "epochs": request.epochs,
            "device": str(device),
            "message": "Training completed successfully (placeholder)"
        }

    except Exception as e:
        logger.error(f"Training error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/gpu_info", response_model=Dict[str, Any])
async def gpu_info():
    """
    Get detailed GPU information
    """
    if not torch.cuda.is_available():
        return {"error": "No GPU available"}

    return {
        "device_count": torch.cuda.device_count(),
        "current_device": torch.cuda.current_device(),
        "device_name": torch.cuda.get_device_name(0),
        "cuda_version": torch.version.cuda,
        "pytorch_version": torch.__version__,
        "memory": {
            "allocated_gb": round(torch.cuda.memory_allocated(0) / 1024**3, 2),
            "reserved_gb": round(torch.cuda.memory_reserved(0) / 1024**3, 2),
            "total_gb": round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 2)
        },
        "properties": {
            "multi_processor_count": torch.cuda.get_device_properties(0).multi_processor_count,
            "major": torch.cuda.get_device_properties(0).major,
            "minor": torch.cuda.get_device_properties(0).minor
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)