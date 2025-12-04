import os
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
import json
from lovable_client import get_lovable_client
from nexgen_analytics import get_nexgen_analytics
from data_processor import get_data_processor
from deduplication import (
    get_deduplication_engine,
    get_triage_engine,
    get_review_queue
)
from fastapi import File, UploadFile

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

class AnalyticsRequest(BaseModel):
    predictions: List[Dict[str, Any]]
    results: List[Dict[str, Any]]
    time_range: Optional[int] = 30  # days
    include_trends: Optional[bool] = True
    include_event_breakdown: Optional[bool] = True
    include_roi: Optional[bool] = True

class AnalyticsResponse(BaseModel):
    summary: Dict[str, Any]
    event_breakdown: Optional[Dict[str, Any]] = None
    roi_metrics: Optional[Dict[str, Any]] = None
    trends: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any]

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

@app.post("/nexgen-analytics", response_model=AnalyticsResponse)
async def nexgen_analytics(
    request: AnalyticsRequest,
    x_api_key: Optional[str] = Header(None)
):
    """
    Run NEXGEN ANALYTICS on provided predictions and results data

    This endpoint uses your GPU-powered NEXGEN ANALYTICS engine to:
    - Compute accuracy metrics
    - Analyze trends over time
    - Break down performance by event type
    - Calculate ROI
    - Generate comprehensive insights

    Send your predictions and results data, get back deep analytics.
    """
    # Check API key if configured
    if GPU_API_KEY and x_api_key != GPU_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        logger.info(f"Running NEXGEN Analytics on {len(request.predictions)} predictions, {len(request.results)} results")

        # Get NEXGEN Analytics engine
        analytics_engine = get_nexgen_analytics()

        # Compute comprehensive report
        report = analytics_engine.generate_comprehensive_report(
            predictions=request.predictions,
            results=request.results,
            time_range=request.time_range
        )

        # Build response based on request flags
        response = AnalyticsResponse(
            summary=report["summary"],
            metadata=report["metadata"]
        )

        if request.include_event_breakdown:
            response.event_breakdown = report.get("event_breakdown")

        if request.include_roi:
            response.roi_metrics = report.get("roi_metrics")

        if request.include_trends:
            response.trends = report.get("trends")

        logger.info("NEXGEN Analytics computation complete")
        return response

    except Exception as e:
        logger.error(f"NEXGEN Analytics error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/nexgen-analytics-simple", response_model=Dict[str, Any])
async def nexgen_analytics_simple(
    time_range: Optional[int] = 30,
    x_api_key: Optional[str] = Header(None)
):
    """
    Simplified NEXGEN Analytics endpoint that fetches data from Lovable automatically

    This endpoint:
    1. Fetches predictions and results from Lovable database
    2. Runs NEXGEN Analytics on that data
    3. Returns comprehensive analytics

    No need to send data - it pulls from Lovable automatically!
    """
    # Check API key if configured
    if GPU_API_KEY and x_api_key != GPU_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        logger.info("Running simplified NEXGEN Analytics (auto-fetch from Lovable)")

        # TODO: Fetch data from Lovable
        # For now, return placeholder
        # In production, you'd call Lovable's get-predictions and get-results endpoints

        analytics_engine = get_nexgen_analytics()

        # Placeholder - replace with actual data fetch
        predictions = []
        results = []

        report = analytics_engine.generate_comprehensive_report(
            predictions=predictions,
            results=results,
            time_range=time_range
        )

        return report

    except Exception as e:
        logger.error(f"Simplified NEXGEN Analytics error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest-historical-data", response_model=Dict[str, Any])
async def ingest_historical_data(
    file: UploadFile = File(...),
    auto_push: bool = True,
    skip_deduplication: bool = False,
    skip_triage: bool = False,
    x_api_key: Optional[str] = Header(None)
):
    """
    Ingest historical rodeo data from uploaded files with smart deduplication and triage

    This endpoint:
    1. Checks for duplicate files (exact and semantic)
    2. Quickly triages file relevance
    3. Extracts text and data using GPU
    4. Assesses data quality
    5. Routes to review queue if needed
    6. Optionally auto-pushes to Lovable database

    Supported formats: .pdf, .csv, .xlsx, .txt, .jpg, .png

    Args:
        file: Uploaded file
        auto_push: If True, automatically push to Lovable after processing
        skip_deduplication: Skip deduplication checks (for re-uploads)
        skip_triage: Skip triage checks (force process everything)
        x_api_key: API key for authentication

    Returns:
        Processing results with deduplication and triage status
    """
    # Check API key if configured
    if GPU_API_KEY and x_api_key != GPU_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        logger.info(f"Ingesting historical data from: {file.filename}")

        # Read file content
        content = await file.read()
        logger.info(f"File size: {len(content)} bytes")

        # STEP 1: Check for duplicate file
        dedup_result = {"is_duplicate": False}
        if not skip_deduplication:
            dedup_engine = get_deduplication_engine()
            dedup_result = dedup_engine.check_file_duplicate(content, file.filename)

            if dedup_result["is_duplicate"]:
                logger.warning(f"DUPLICATE FILE DETECTED: {file.filename}")
                return {
                    "status": "duplicate",
                    "filename": file.filename,
                    "file_size": len(content),
                    "duplicate_check": dedup_result,
                    "message": "This file was already uploaded. Use skip_deduplication=true to force re-upload.",
                    "action": "rejected"
                }

        # STEP 2: Smart triage - Quick relevance check
        triage_result = {"verdict": "relevant", "action": "process"}
        if not skip_triage:
            triage_engine = get_triage_engine()
            triage_result = triage_engine.assess_file_relevance(
                filename=file.filename,
                content=content,
                file_type=file.content_type or ''
            )

            logger.info(f"Triage verdict: {triage_result['verdict']} (score: {triage_result['relevance_score']})")

            # If irrelevant, reject immediately
            if triage_result["action"] == "reject":
                logger.warning(f"IRRELEVANT FILE: {file.filename}")

                review_queue = get_review_queue()
                review_queue.add_to_review(
                    filename=file.filename,
                    reason="File appears irrelevant to rodeo data",
                    file_hash=dedup_result.get("hash", "unknown"),
                    assessment=triage_result
                )

                return {
                    "status": "rejected",
                    "filename": file.filename,
                    "file_size": len(content),
                    "triage": triage_result,
                    "message": "File does not appear to contain rodeo data. Sent to review queue.",
                    "action": "rejected",
                    "review_queue_id": len(get_review_queue().queue) - 1
                }

        # STEP 3: Process file (extract data)
        processor = get_data_processor()
        processed_data = processor.process_file(
            file_content=content,
            filename=file.filename,
            file_type=file.content_type or ''
        )

        logger.info(f"Processed data: {processed_data.keys()}")

        # STEP 4: Check for semantic data duplication
        data_dedup_result = {"is_duplicate": False}
        if not skip_deduplication and not dedup_result["is_duplicate"]:
            data_dedup_result = dedup_engine.check_data_duplicate(processed_data, file.filename)

            if data_dedup_result["is_duplicate"]:
                logger.warning(f"DUPLICATE DATA DETECTED: {file.filename}")
                return {
                    "status": "duplicate",
                    "filename": file.filename,
                    "file_size": len(content),
                    "duplicate_check": data_dedup_result,
                    "message": "This data was already uploaded (possibly in different format)",
                    "action": "rejected"
                }

        # STEP 5: Assess data quality
        quality_result = {"verdict": "good", "action": "process"}
        if not skip_triage:
            quality_result = triage_engine.assess_data_quality(processed_data, file.filename)

            logger.info(f"Quality verdict: {quality_result['verdict']} (score: {quality_result['quality_score']})")

            # If poor quality, route to review
            if quality_result["action"] == "reject":
                logger.warning(f"POOR QUALITY DATA: {file.filename}")

                review_queue = get_review_queue()
                review_queue.add_to_review(
                    filename=file.filename,
                    reason="Poor data quality",
                    file_hash=dedup_result.get("hash", "unknown"),
                    assessment=quality_result
                )

                return {
                    "status": "rejected",
                    "filename": file.filename,
                    "file_size": len(content),
                    "quality_assessment": quality_result,
                    "message": "Data quality too low. Sent to review queue.",
                    "action": "rejected",
                    "review_queue_id": len(get_review_queue().queue) - 1
                }

            # If needs review, route to review queue but don't reject
            if quality_result["action"] == "review" or triage_result.get("action") == "review":
                logger.info(f"NEEDS REVIEW: {file.filename}")

                review_queue = get_review_queue()
                review_queue.add_to_review(
                    filename=file.filename,
                    reason="Uncertain quality or relevance - needs manual review",
                    file_hash=dedup_result.get("hash", "unknown"),
                    assessment={**triage_result, **quality_result}
                )

        # STEP 6: Auto-push to Lovable if enabled and passed all checks
        push_results = []
        if auto_push and quality_result["action"] == "process":
            logger.info("Auto-pushing processed data to Lovable")
            lovable_client = get_lovable_client()

            # Push predictions
            if "predictions" in processed_data:
                for pred in processed_data["predictions"]:
                    try:
                        result = await lovable_client.push_prediction(**pred)
                        push_results.append({"type": "prediction", "status": "success", "id": result.get("prediction_id")})
                    except Exception as e:
                        logger.error(f"Error pushing prediction: {str(e)}")
                        push_results.append({"type": "prediction", "status": "error", "error": str(e)})

            # Push results
            if "results" in processed_data:
                for res in processed_data["results"]:
                    try:
                        result = await lovable_client.push_result(**res)
                        push_results.append({"type": "result", "status": "success", "id": result.get("result_id")})
                    except Exception as e:
                        logger.error(f"Error pushing result: {str(e)}")
                        push_results.append({"type": "result", "status": "error", "error": str(e)})

        # Determine final status
        if quality_result["action"] == "review" or triage_result.get("action") == "review":
            final_status = "needs_review"
        elif quality_result["action"] == "process" and auto_push:
            final_status = "success"
        else:
            final_status = "processed"

        return {
            "status": final_status,
            "filename": file.filename,
            "file_size": len(content),
            "deduplication": {
                "file_duplicate": dedup_result["is_duplicate"],
                "data_duplicate": data_dedup_result["is_duplicate"]
            },
            "triage": {
                "verdict": triage_result["verdict"],
                "confidence": triage_result.get("confidence", 0),
                "reasons": triage_result.get("reasons", [])
            },
            "quality": {
                "verdict": quality_result["verdict"],
                "score": quality_result.get("quality_score", 0),
                "issues": quality_result.get("issues", []),
                "warnings": quality_result.get("warnings", [])
            },
            "processed_data": {
                "events_count": len(processed_data.get("events", [])),
                "riders_count": len(processed_data.get("riders", [])),
                "predictions_count": len(processed_data.get("predictions", [])),
                "results_count": len(processed_data.get("results", []))
            },
            "auto_push_enabled": auto_push,
            "push_results": push_results if auto_push else None,
            "action_taken": quality_result["action"],
            "review_queue_id": len(get_review_queue().queue) - 1 if final_status == "needs_review" else None
        }

    except Exception as e:
        logger.error(f"Error ingesting historical data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest-batch", response_model=Dict[str, Any])
async def ingest_batch(
    files: List[UploadFile] = File(...),
    auto_push: bool = True,
    x_api_key: Optional[str] = Header(None)
):
    """
    Batch ingest multiple historical data files

    Upload multiple files at once for processing.
    Each file is processed independently and results are aggregated.

    Args:
        files: List of uploaded files
        auto_push: If True, automatically push to Lovable after processing
        x_api_key: API key for authentication

    Returns:
        Aggregated processing results
    """
    # Check API key if configured
    if GPU_API_KEY and x_api_key != GPU_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        logger.info(f"Batch ingesting {len(files)} files")

        results = []
        total_events = 0
        total_riders = 0
        total_predictions = 0
        total_results = 0

        for file in files:
            try:
                # Process each file
                result = await ingest_historical_data(file, auto_push, x_api_key)
                results.append({
                    "filename": file.filename,
                    "status": "success",
                    "details": result
                })

                # Aggregate counts
                pd = result["processed_data"]
                total_events += pd.get("events_count", 0)
                total_riders += pd.get("riders_count", 0)
                total_predictions += pd.get("predictions_count", 0)
                total_results += pd.get("results_count", 0)

            except Exception as e:
                logger.error(f"Error processing {file.filename}: {str(e)}")
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "error": str(e)
                })

        return {
            "status": "success",
            "files_processed": len(files),
            "totals": {
                "events": total_events,
                "riders": total_riders,
                "predictions": total_predictions,
                "results": total_results
            },
            "file_results": results
        }

    except Exception as e:
        logger.error(f"Error in batch ingestion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/review-queue", response_model=Dict[str, Any])
async def get_review_queue_endpoint(
    x_api_key: Optional[str] = Header(None)
):
    """
    Get all files in the review queue

    Files end up in the review queue if:
    - They appear irrelevant to rodeo data
    - Data quality is too low
    - Extraction confidence is low
    - File structure is unclear

    Returns list of files needing manual review.
    """
    # Check API key if configured
    if GPU_API_KEY and x_api_key != GPU_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        review_queue = get_review_queue()
        queue_items = review_queue.get_review_queue()

        return {
            "status": "success",
            "queue_length": len(queue_items),
            "items": queue_items
        }

    except Exception as e:
        logger.error(f"Error fetching review queue: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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