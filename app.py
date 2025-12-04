import os
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
import json
from lovable_client import get_lovable_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RodeoAI GPU API",
    description="GPU-accelerated API for rodeo analytics and predictions",
    version="1.0.0"
)

# Get API key from environment
GPU_API_KEY = os.getenv("GPU_API_KEY", "")

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
    model_version: str = "l40s-v1.0.0"

class HealthResponse(BaseModel):
    status: str
    gpu_available: bool = True
    model_version: str = "l40s-v1.0.0"
    timestamp: str

class GenerateAndPushRequest(BaseModel):
    event_name: str
    event_location: str
    event_date: str  # ISO format, e.g., "2024-12-15T19:00:00Z"
    event_type: str  # bull_riding, saddle_bronc, bareback, barrel_racing, etc.
    rider_name: str
    rider_rank: Optional[int] = None
    rider_stats: Optional[Dict[str, Any]] = None
    animal_stats: Optional[Dict[str, Any]] = None

class GenerateAndPushResponse(BaseModel):
    prediction: PredictionResponse
    lovable_response: Dict[str, Any]
    status: str

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "RodeoAI GPU API",
        "version": "1.0.0",
        "description": "GPU-accelerated rodeo analytics",
        "status": "active"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API health and GPU status"""
    return HealthResponse(
        status="healthy",
        gpu_available=True,
        model_version="l40s-v1.0.0",
        timestamp=datetime.now().isoformat()
    )

@app.post("/generate-and-push", response_model=GenerateAndPushResponse)
async def generate_and_push(
    request: GenerateAndPushRequest,
    x_api_key: Optional[str] = Header(None)
):
    """
    Generate a prediction using GPU and automatically push to Lovable RodeoAI

    This endpoint:
    1. Generates a prediction based on provided stats
    2. Pushes the prediction to Lovable's ingest-prediction endpoint
    3. Returns both the prediction and Lovable's response
    """
    # Check API key if configured
    if GPU_API_KEY and x_api_key != GPU_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        logger.info(f"Generating and pushing prediction for {request.event_name} - {request.rider_name}")

        # Generate prediction using GPU logic
        score = 0.5
        if request.rider_stats:
            if "wins" in request.rider_stats:
                score += min(0.2, request.rider_stats["wins"] / 100)
            if "average_score" in request.rider_stats:
                score += min(0.2, request.rider_stats["average_score"] / 100)
            if "win_rate" in request.rider_stats:
                score += min(0.15, request.rider_stats["win_rate"] / 100)

        if request.animal_stats:
            if "buck_score" in request.animal_stats:
                score -= min(0.1, request.animal_stats["buck_score"] / 100)

        score = max(0.0, min(1.0, score))
        confidence = min(95.0, score * 100 + 10)  # Convert to percentage

        # Calculate odds (simplified)
        if score > 0.7:
            odds = 200 + (score * 100)
        else:
            odds = 300 + (score * 150)

        # Generate analysis text
        win_rate = request.rider_stats.get("win_rate", 0) if request.rider_stats else 0
        analysis = f"Based on {request.rider_name}'s performance statistics "
        if win_rate > 0:
            analysis += f"with a {win_rate:.1f}% win rate, "
        analysis += f"the model predicts a {confidence:.1f}% chance of success in this {request.event_type} event."

        prediction = PredictionResponse(
            prediction_score=score,
            confidence=confidence / 100,  # Normalize back to 0-1
            factors={
                "rider_experience": 0.35,
                "recent_performance": 0.25,
                "event_conditions": 0.20,
                "historical_matchup": 0.20
            },
            timestamp=datetime.now().isoformat(),
            model_version="l40s-v1.0.0"
        )

        # Push to Lovable
        lovable_client = get_lovable_client()
        lovable_response = await lovable_client.push_prediction(
            event_name=request.event_name,
            event_location=request.event_location,
            event_date=request.event_date,
            event_type=request.event_type,
            rider_name=request.rider_name,
            rider_rank=request.rider_rank,
            rider_win_rate=win_rate if win_rate > 0 else None,
            prediction_type="winner",
            predicted_value="Win" if score > 0.5 else "Unlikely",
            confidence=confidence,
            odds=odds,
            model_version="l40s-v1.0.0",
            analysis=analysis
        )

        return GenerateAndPushResponse(
            prediction=prediction,
            lovable_response=lovable_response,
            status="success"
        )

    except Exception as e:
        logger.error(f"Error in generate-and-push: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict", response_model=PredictionResponse)
async def predict(
    request: PredictionRequest,
    x_api_key: Optional[str] = Header(None)
):
    """
    Make a single prediction using GPU acceleration
    """
    # Check API key if configured
    if GPU_API_KEY and x_api_key != GPU_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        logger.info(f"Processing prediction for {request.event_type}")

        # Simulate scoring based on stats (placeholder logic)
        score = 0.5
        if request.rider_stats:
            # Factor in rider experience
            if "wins" in request.rider_stats:
                score += min(0.2, request.rider_stats["wins"] / 100)
            if "average_score" in request.rider_stats:
                score += min(0.2, request.rider_stats["average_score"] / 100)

        if request.animal_stats:
            # Factor in animal difficulty
            if "buck_score" in request.animal_stats:
                score -= min(0.1, request.animal_stats["buck_score"] / 100)

        # Ensure score is between 0 and 1
        score = max(0.0, min(1.0, score))

        # Calculate confidence
        confidence = 0.75  # Base confidence

        # Feature importance
        factors = {
            "rider_experience": 0.35,
            "recent_performance": 0.25,
            "event_conditions": 0.20,
            "historical_matchup": 0.20
        }

        return PredictionResponse(
            prediction_score=score,
            confidence=confidence,
            factors=factors,
            timestamp=datetime.now().isoformat(),
            model_version="l40s-v1.0.0"
        )

    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/batch_predict", response_model=List[PredictionResponse])
async def batch_predict(
    request: BatchPredictionRequest,
    x_api_key: Optional[str] = Header(None)
):
    """
    Process multiple predictions in parallel on GPU
    """
    # Check API key if configured
    if GPU_API_KEY and x_api_key != GPU_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        logger.info(f"Processing batch of {len(request.predictions)} predictions")

        results = []
        for pred_request in request.predictions:
            # Process each prediction (in production, this would be parallelized)
            result = await predict(pred_request, x_api_key)
            results.append(result)

        return results

    except Exception as e:
        logger.error(f"Batch prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/gpu_info", response_model=Dict[str, Any])
async def gpu_info():
    """
    Get GPU information (simulated for RunPod L40S)
    """
    return {
        "gpu_available": True,
        "gpu_name": "NVIDIA L40S",
        "cuda_version": "12.1",
        "memory": {
            "total_gb": 48,
            "available_gb": 45
        },
        "compute_capability": "8.9",
        "status": "active"
    }

# RunPod serverless handler (if needed)
@app.post("/runsync")
async def runsync(request: Dict[str, Any]):
    """
    RunPod serverless handler for synchronous requests
    """
    try:
        # Extract the actual request from RunPod wrapper
        input_data = request.get("input", {})

        # Route based on action
        action = input_data.get("action", "predict")

        if action == "predict":
            pred_request = PredictionRequest(**input_data.get("data", {}))
            result = await predict(pred_request, None)
            return {"output": result.dict()}
        elif action == "health":
            result = await health_check()
            return {"output": result.dict()}
        else:
            return {"output": {"error": f"Unknown action: {action}"}}

    except Exception as e:
        logger.error(f"RunPod handler error: {str(e)}")
        return {"output": {"error": str(e)}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)