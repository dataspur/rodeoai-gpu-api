"""
Client for pushing predictions to Lovable RodeoAI web app
"""
import os
import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Lovable edge function URLs
LOVABLE_BASE_URL = os.getenv("LOVABLE_INGEST_URL", "https://utbyiiyghrekahruzywo.supabase.co/functions/v1")
GPU_API_KEY = os.getenv("GPU_API_KEY", "")


class LovableClient:
    """Client for interacting with Lovable RodeoAI edge functions"""

    def __init__(self, base_url: str = LOVABLE_BASE_URL, api_key: str = GPU_API_KEY):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)

    async def push_prediction(
        self,
        event_name: str,
        event_location: str,
        event_date: str,  # ISO format
        event_type: str,
        rider_name: str,
        rider_rank: Optional[int] = None,
        rider_win_rate: Optional[float] = None,
        prediction_type: str = "winner",
        predicted_value: str = "Win",
        confidence: float = 0.0,
        odds: Optional[float] = None,
        model_version: str = "l40s-v1.0.0",
        analysis: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Push a prediction to Lovable's ingest-prediction endpoint

        Args:
            event_name: Name of the event (e.g., "NFR Round 7 - Bull Riding")
            event_location: Location (e.g., "Las Vegas, NV")
            event_date: ISO 8601 datetime string
            event_type: bull_riding, saddle_bronc, bareback, barrel_racing, etc.
            rider_name: Rider's name
            rider_rank: Optional rider rank
            rider_win_rate: Optional win rate (0-100)
            prediction_type: Type of prediction (winner, score_range, placement)
            predicted_value: The prediction itself
            confidence: Confidence score (0-100)
            odds: Betting odds
            model_version: Version of ML model used
            analysis: Optional AI-generated analysis text

        Returns:
            Response from Lovable API
        """
        url = f"{self.base_url}/ingest-prediction"

        payload = {
            "event": {
                "name": event_name,
                "location": event_location,
                "event_date": event_date,
                "event_type": event_type
            },
            "rider": {
                "name": rider_name
            },
            "prediction": {
                "prediction_type": prediction_type,
                "predicted_value": predicted_value,
                "confidence": confidence,
                "model_version": model_version
            }
        }

        # Add optional fields
        if rider_rank is not None:
            payload["rider"]["rank"] = rider_rank
        if rider_win_rate is not None:
            payload["rider"]["win_rate"] = rider_win_rate
        if odds is not None:
            payload["prediction"]["odds"] = odds
        if analysis:
            payload["prediction"]["analysis"] = analysis

        headers = {
            "Content-Type": "application/json",
            "x-gpu-api-key": self.api_key
        }

        try:
            logger.info(f"Pushing prediction to Lovable: {event_name} - {rider_name}")
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully pushed prediction: {result}")
            return result
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error pushing prediction: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error pushing prediction to Lovable: {str(e)}")
            raise

    async def push_result(
        self,
        event_name: str,
        rider_name: str,
        actual_value: str,
        score: Optional[float] = None,
        placement: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Push an actual result to Lovable's ingest-result endpoint

        Args:
            event_name: Name of the event (must match existing event)
            rider_name: Rider's name (must match existing rider)
            actual_value: Actual outcome
            score: Optional score
            placement: Optional placement (1st, 2nd, etc.)

        Returns:
            Response from Lovable API
        """
        url = f"{self.base_url}/ingest-result"

        payload = {
            "event_name": event_name,
            "rider_name": rider_name,
            "actual_value": actual_value
        }

        if score is not None:
            payload["score"] = score
        if placement is not None:
            payload["placement"] = placement

        headers = {
            "Content-Type": "application/json",
            "x-gpu-api-key": self.api_key
        }

        try:
            logger.info(f"Pushing result to Lovable: {event_name} - {rider_name}")
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully pushed result: {result}")
            return result
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error pushing result: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error pushing result to Lovable: {str(e)}")
            raise

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Singleton instance
_lovable_client: Optional[LovableClient] = None

def get_lovable_client() -> LovableClient:
    """Get or create the Lovable client singleton"""
    global _lovable_client
    if _lovable_client is None:
        _lovable_client = LovableClient()
    return _lovable_client