"""
Deduplication and Smart Triage System

This module provides:
1. Deduplication - Detect if data was already uploaded
2. Smart Triage - Quickly assess file relevance
3. Review Queue - Route problematic files for manual review
"""

import hashlib
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)


class DeduplicationEngine:
    """
    Handles deduplication of uploaded data
    """

    def __init__(self):
        logger.info("Initializing DeduplicationEngine")
        # In production, this would connect to a cache/database
        self.seen_hashes = set()  # In-memory for now, use Redis in production

    def compute_content_hash(self, content: bytes) -> str:
        """
        Compute SHA-256 hash of file content

        Args:
            content: Raw file bytes

        Returns:
            Hex string of content hash
        """
        return hashlib.sha256(content).hexdigest()

    def compute_data_hash(self, data: Dict[str, Any]) -> str:
        """
        Compute hash of extracted data (semantic deduplication)

        This catches duplicates even if file format is different
        (e.g., same data in CSV vs Excel)

        Args:
            data: Processed data dictionary

        Returns:
            Hash of data content
        """
        # Create a canonical representation of the data
        canonical = []

        # Hash events
        if "events" in data:
            for event in data["events"]:
                canonical.append(f"event:{event.get('name')}:{event.get('event_date')}")

        # Hash predictions
        if "predictions" in data:
            for pred in data["predictions"]:
                canonical.append(f"pred:{pred.get('event', {}).get('name')}:{pred.get('rider', {}).get('name')}")

        # Hash results
        if "results" in data:
            for result in data["results"]:
                canonical.append(f"result:{result.get('event_name')}:{result.get('rider_name')}")

        # Sort and join
        canonical_str = "|".join(sorted(canonical))
        return hashlib.sha256(canonical_str.encode()).hexdigest()

    def check_file_duplicate(self, content: bytes, filename: str) -> Dict[str, Any]:
        """
        Check if file was already uploaded

        Args:
            content: Raw file bytes
            filename: Original filename

        Returns:
            Dictionary with duplicate status
        """
        content_hash = self.compute_content_hash(content)

        # Check if we've seen this exact file before
        if content_hash in self.seen_hashes:
            logger.warning(f"DUPLICATE FILE: {filename} (hash: {content_hash[:8]}...)")
            return {
                "is_duplicate": True,
                "duplicate_type": "exact_file",
                "hash": content_hash,
                "message": f"This exact file was already uploaded"
            }

        # Mark as seen
        self.seen_hashes.add(content_hash)

        return {
            "is_duplicate": False,
            "hash": content_hash,
            "message": "File is unique"
        }

    def check_data_duplicate(
        self,
        processed_data: Dict[str, Any],
        filename: str
    ) -> Dict[str, Any]:
        """
        Check if extracted data was already uploaded (semantic deduplication)

        Args:
            processed_data: Processed data dictionary
            filename: Original filename

        Returns:
            Dictionary with duplicate status
        """
        data_hash = self.compute_data_hash(processed_data)

        # Check if we've seen this data before
        if data_hash in self.seen_hashes:
            logger.warning(f"DUPLICATE DATA: {filename} (data_hash: {data_hash[:8]}...)")
            return {
                "is_duplicate": True,
                "duplicate_type": "semantic_data",
                "hash": data_hash,
                "message": "This data was already uploaded (possibly in different format)"
            }

        # Mark as seen
        self.seen_hashes.add(data_hash)

        return {
            "is_duplicate": False,
            "hash": data_hash,
            "message": "Data is unique"
        }


class SmartTriageEngine:
    """
    Quickly assess file relevance and route to appropriate queue
    """

    def __init__(self):
        logger.info("Initializing SmartTriageEngine")

        # Define rodeo-related keywords
        self.rodeo_keywords = {
            # Event types
            'bull', 'bronc', 'barrel', 'roping', 'wrestling', 'steer', 'calf',
            'saddle', 'bareback', 'breakaway', 'team roping', 'tie-down',

            # Organizations
            'prca', 'pbr', 'wpra', 'nfr', 'wnfr', 'rodeo', 'professional rodeo',

            # Locations
            'las vegas', 'thomas mack', 'cowboy', 'arena',

            # Metrics
            'score', 'time', 'seconds', 'points', 'rank', 'standings',
            'round', 'placement', 'win', 'prize'
        }

        # Define irrelevant indicators
        self.irrelevant_keywords = {
            'recipe', 'cooking', 'diet', 'fashion', 'clothing', 'weather',
            'stock market', 'finance', 'real estate', 'invoice', 'receipt',
            'medical', 'prescription', 'diagnosis', 'resume', 'cv'
        }

    def assess_file_relevance(
        self,
        filename: str,
        content: bytes,
        file_type: str
    ) -> Dict[str, Any]:
        """
        Quickly assess if file is relevant to rodeo data

        Args:
            filename: Original filename
            content: Raw file bytes
            file_type: MIME type or extension

        Returns:
            Triage assessment
        """
        logger.info(f"Triaging file: {filename}")

        # Quick checks
        relevance_score = 0
        confidence = 0.0
        reasons = []

        # Check 1: Filename
        filename_lower = filename.lower()
        filename_score = self._score_text(filename_lower)
        relevance_score += filename_score * 2  # Weight filename heavily

        if filename_score > 0:
            reasons.append(f"Filename contains rodeo keywords")

        # Check 2: Quick content sample (first 1000 bytes)
        try:
            # Try to decode as text
            sample = content[:1000].decode('utf-8', errors='ignore').lower()
            content_score = self._score_text(sample)
            relevance_score += content_score

            if content_score > 0:
                reasons.append(f"Content sample contains rodeo keywords")
            elif content_score < 0:
                reasons.append(f"Content sample contains irrelevant keywords")

        except Exception as e:
            logger.warning(f"Could not sample content: {str(e)}")
            reasons.append("Binary file - cannot quick sample")

        # Check 3: File type
        if any(ext in file_type.lower() or filename.endswith(ext) for ext in ['.csv', '.xlsx', '.xls']):
            relevance_score += 1
            reasons.append("Data file format (CSV/Excel)")

        # Calculate confidence
        confidence = min(100, abs(relevance_score) * 20)

        # Determine verdict
        if relevance_score >= 2:
            verdict = "relevant"
            action = "process"
            reasons.append("✅ File appears relevant to rodeo data")
        elif relevance_score <= -2:
            verdict = "irrelevant"
            action = "reject"
            reasons.append("❌ File appears irrelevant")
        else:
            verdict = "uncertain"
            action = "review"
            reasons.append("⚠️  Uncertain - needs manual review")

        return {
            "verdict": verdict,
            "action": action,
            "relevance_score": relevance_score,
            "confidence": confidence,
            "reasons": reasons,
            "triage_time_ms": 0  # Would measure actual time
        }

    def assess_data_quality(
        self,
        processed_data: Dict[str, Any],
        filename: str
    ) -> Dict[str, Any]:
        """
        Assess quality of extracted data

        Args:
            processed_data: Processed data dictionary
            filename: Original filename

        Returns:
            Quality assessment
        """
        logger.info(f"Assessing data quality: {filename}")

        issues = []
        warnings = []
        quality_score = 100  # Start at 100, deduct for issues

        # Check for empty data
        events_count = len(processed_data.get("events", []))
        riders_count = len(processed_data.get("riders", []))
        predictions_count = len(processed_data.get("predictions", []))
        results_count = len(processed_data.get("results", []))

        total_records = events_count + riders_count + predictions_count + results_count

        if total_records == 0:
            quality_score -= 100
            issues.append("No data extracted from file")
            return {
                "verdict": "empty",
                "action": "reject",
                "quality_score": 0,
                "issues": issues,
                "warnings": warnings
            }

        if total_records < 5:
            quality_score -= 30
            warnings.append(f"Very few records extracted ({total_records})")

        # Check for missing critical fields
        if predictions_count > 0:
            pred = processed_data["predictions"][0]
            if not pred.get("event", {}).get("name"):
                quality_score -= 20
                issues.append("Predictions missing event names")
            if not pred.get("rider", {}).get("name"):
                quality_score -= 20
                issues.append("Predictions missing rider names")

        if results_count > 0:
            result = processed_data["results"][0]
            if not result.get("event_name"):
                quality_score -= 20
                issues.append("Results missing event names")
            if not result.get("rider_name"):
                quality_score -= 20
                issues.append("Results missing rider names")

        # Check if needs manual mapping
        if processed_data.get("needs_manual_mapping"):
            quality_score -= 25
            warnings.append("Data structure unclear - may need manual field mapping")

        # Check if needs review
        if processed_data.get("needs_review"):
            quality_score -= 15
            warnings.append("Data extraction uncertain - should review")

        # Determine verdict
        if quality_score >= 80:
            verdict = "excellent"
            action = "process"
        elif quality_score >= 60:
            verdict = "good"
            action = "process"
        elif quality_score >= 40:
            verdict = "fair"
            action = "review"
        else:
            verdict = "poor"
            action = "reject" if quality_score < 20 else "review"

        return {
            "verdict": verdict,
            "action": action,
            "quality_score": max(0, quality_score),
            "issues": issues,
            "warnings": warnings,
            "record_counts": {
                "events": events_count,
                "riders": riders_count,
                "predictions": predictions_count,
                "results": results_count,
                "total": total_records
            }
        }

    def _score_text(self, text: str) -> int:
        """
        Score text based on keyword presence

        Args:
            text: Text to score

        Returns:
            Score (positive = relevant, negative = irrelevant)
        """
        score = 0

        # Count rodeo keywords
        rodeo_matches = sum(1 for kw in self.rodeo_keywords if kw in text)
        score += rodeo_matches

        # Count irrelevant keywords (negative score)
        irrelevant_matches = sum(1 for kw in self.irrelevant_keywords if kw in text)
        score -= irrelevant_matches * 2  # Weight irrelevant keywords more

        return score


class ReviewQueue:
    """
    Manages files that need manual review
    """

    def __init__(self):
        logger.info("Initializing ReviewQueue")
        self.queue = []  # In production, use database

    def add_to_review(
        self,
        filename: str,
        reason: str,
        file_hash: str,
        assessment: Dict[str, Any]
    ):
        """
        Add file to review queue

        Args:
            filename: Original filename
            reason: Why it needs review
            file_hash: Content hash
            assessment: Triage/quality assessment
        """
        review_item = {
            "filename": filename,
            "reason": reason,
            "file_hash": file_hash,
            "assessment": assessment,
            "added_at": datetime.now().isoformat(),
            "status": "pending_review"
        }

        self.queue.append(review_item)
        logger.info(f"Added to review queue: {filename} - {reason}")

    def get_review_queue(self) -> List[Dict[str, Any]]:
        """Get all items in review queue"""
        return self.queue


# Singletons
_deduplication_engine: Optional[DeduplicationEngine] = None
_triage_engine: Optional[SmartTriageEngine] = None
_review_queue: Optional[ReviewQueue] = None


def get_deduplication_engine() -> DeduplicationEngine:
    """Get or create DeduplicationEngine singleton"""
    global _deduplication_engine
    if _deduplication_engine is None:
        _deduplication_engine = DeduplicationEngine()
    return _deduplication_engine


def get_triage_engine() -> SmartTriageEngine:
    """Get or create SmartTriageEngine singleton"""
    global _triage_engine
    if _triage_engine is None:
        _triage_engine = SmartTriageEngine()
    return _triage_engine


def get_review_queue() -> ReviewQueue:
    """Get or create ReviewQueue singleton"""
    global _review_queue
    if _review_queue is None:
        _review_queue = ReviewQueue()
    return _review_queue