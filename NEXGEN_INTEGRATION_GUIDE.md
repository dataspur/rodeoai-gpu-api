# NEXGEN ANALYTICS Integration Guide

## 🎯 Overview

You mentioned you already have a **NEXGEN ANALYTICS** system developed on the same GPU as your predictions engine. This guide explains how to integrate your existing NEXGEN code with the API we just built.

---

## 📁 What We Created

### 1. `nexgen_analytics.py` - Wrapper Class
A Python class that acts as an integration layer between your NEXGEN ANALYTICS and the FastAPI endpoints.

**Current Status:** ⚠️ Contains placeholder logic
**Your Task:** Replace placeholders with your actual NEXGEN ANALYTICS code

### 2. FastAPI Endpoints (in `app.py`)

#### `/nexgen-analytics` (POST)
- **Purpose:** Run NEXGEN ANALYTICS on provided data
- **Input:** Predictions + Results data
- **Output:** Comprehensive analytics report
- **Use Case:** Lovable sends data → GPU processes → Returns analytics

#### `/nexgen-analytics-simple` (GET)
- **Purpose:** Auto-fetch data from Lovable and run analytics
- **Input:** Just a time range
- **Output:** Same comprehensive report
- **Use Case:** Cron job or scheduled analytics

---

## 🔧 How to Integrate Your NEXGEN Code

### Step 1: Locate Your NEXGEN ANALYTICS Code

First, tell me:
- **Where is your NEXGEN ANALYTICS code?**
  - Same directory as predictions?
  - Separate repository?
  - Python files? Jupyter notebooks?

- **What files contain the logic?**
  - Example: `nexgen_core.py`, `analytics_engine.py`, etc.

### Step 2: Replace Placeholders in `nexgen_analytics.py`

Open `nexgen_analytics.py` and replace the placeholder methods with your actual code.

#### Example - Before (Placeholder):

```python
def compute_accuracy_metrics(self, predictions, results, time_range):
    """Placeholder implementation"""
    correct = sum(1 for r in results if r.get("was_correct", False))
    total = len(results)
    accuracy = (correct / total * 100) if total > 0 else 0

    return {
        "overall_accuracy": accuracy,
        "correct_predictions": correct,
        "total_predictions": total,
        "confidence": 85.0,  # ← Placeholder
        "time_range_days": time_range,
        "model_version": self.model_version
    }
```

#### Example - After (Your NEXGEN Code):

```python
def compute_accuracy_metrics(self, predictions, results, time_range):
    """Your actual NEXGEN ANALYTICS implementation"""

    # Import your NEXGEN modules
    from your_nexgen_core import NEXGENEngine

    # Use your actual logic
    engine = NEXGENEngine()
    analysis = engine.analyze_accuracy(
        predictions=predictions,
        results=results,
        window=time_range
    )

    return {
        "overall_accuracy": analysis.accuracy_score,
        "correct_predictions": analysis.correct_count,
        "total_predictions": analysis.total_count,
        "confidence": analysis.confidence_interval,
        "advanced_metrics": analysis.get_all_metrics(),
        "time_range_days": time_range,
        "model_version": self.model_version
    }
```

### Step 3: Methods to Implement

Replace these placeholder methods with your NEXGEN ANALYTICS:

| Method | Purpose | Your NEXGEN Equivalent |
|--------|---------|----------------------|
| `compute_accuracy_metrics()` | Overall accuracy | Your accuracy engine |
| `compute_event_type_breakdown()` | Accuracy by event type | Your event analyzer |
| `compute_roi_metrics()` | ROI calculations | Your ROI engine |
| `compute_trend_analysis()` | Time series trends | Your trend analyzer |
| `compute_rider_analytics()` | Per-rider deep dive | Your rider profiler |
| `generate_comprehensive_report()` | Full report | Your report generator |

### Step 4: Import Your NEXGEN Modules

At the top of `nexgen_analytics.py`, add imports for your actual NEXGEN code:

```python
# Add these imports at the top
from your_nexgen_module import YourAnalyticsEngine
from your_nexgen_module import YourTrendAnalyzer
from your_nexgen_module import YourROICalculator
# etc.
```

### Step 5: Initialize Your NEXGEN Engine

In the `__init__` method:

```python
def __init__(self):
    """Initialize NEXGEN Analytics engine"""
    logger.info("Initializing NEXGEN Analytics engine")

    # TODO: Replace with your actual initialization
    self.nexgen_engine = YourAnalyticsEngine()
    self.nexgen_engine.load_models()
    self.nexgen_engine.configure(gpu=True)

    self.model_version = "nexgen-v1.0"  # Your version
```

---

## 📊 Data Format

### Input Format (What Lovable Sends):

**Predictions:**
```python
[
    {
        "id": "uuid",
        "event_id": "uuid",
        "rider_id": "uuid",
        "event_type": "bull_riding",
        "predicted_value": "Win",
        "confidence": 87.5,
        "odds": 280.0,
        "model_version": "l40s-v1.0.0",
        "created_at": "2024-12-04T..."
    },
    # ... more predictions
]
```

**Results:**
```python
[
    {
        "id": "uuid",
        "event_id": "uuid",
        "rider_id": "uuid",
        "prediction_id": "uuid",
        "actual_value": "Win",
        "score": 91.5,
        "placement": 1,
        "was_correct": true,
        "created_at": "2024-12-04T..."
    },
    # ... more results
]
```

### Output Format (What Your NEXGEN Should Return):

```python
{
    "summary": {
        "overall_accuracy": 78.5,
        "correct_predictions": 62,
        "total_predictions": 79,
        "confidence": 85.0,
        "time_range_days": 30,
        "model_version": "nexgen-v1.0"
    },
    "event_breakdown": {
        "bull_riding": {
            "accuracy": 82.3,
            "total_predictions": 45,
            "correct_predictions": 37
        },
        "barrel_racing": {
            "accuracy": 72.5,
            "total_predictions": 34,
            "correct_predictions": 25
        }
    },
    "roi_metrics": {
        "roi_percentage": 15.2,
        "total_bet": 7900.0,
        "total_return": 9100.0,
        "profit": 1200.0,
        "winning_bets": 62,
        "total_bets": 79
    },
    "trends": [
        {
            "period": "2024-10",
            "accuracy": 75.0,
            "prediction_count": 42,
            "confidence": 82.0
        },
        {
            "period": "2024-11",
            "accuracy": 78.5,
            "prediction_count": 37,
            "confidence": 85.0
        }
    ],
    "metadata": {
        "report_generated": "2024-12-04T...",
        "model_version": "nexgen-v1.0",
        "prediction_count": 79,
        "result_count": 79,
        "time_range_days": 30
    }
}
```

---

## 🚀 Integration Options

### Option 1: Direct Integration (Recommended)

If your NEXGEN ANALYTICS is in Python:

1. Copy your NEXGEN files to the `rodeoai-gpu-api` directory
2. Update imports in `nexgen_analytics.py`
3. Replace placeholder methods with calls to your code
4. Test locally
5. Deploy to RunPod

### Option 2: Microservice Architecture

If your NEXGEN ANALYTICS is separate:

1. Keep NEXGEN as a separate service
2. Have `nexgen_analytics.py` make HTTP calls to your NEXGEN API
3. The FastAPI endpoints act as a proxy

### Option 3: Subprocess/CLI Integration

If your NEXGEN ANALYTICS is a CLI tool or different language:

1. Use Python's `subprocess` module
2. Call your NEXGEN CLI from Python
3. Parse the output and return via API

---

## 🧪 Testing Your Integration

### Test Locally First:

```bash
# Start your FastAPI server
cd rodeoai-gpu-api
python app.py

# In another terminal, test the endpoint
curl -X POST "http://localhost:8000/nexgen-analytics" \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_KEY" \
  -d '{
    "predictions": [...],
    "results": [...],
    "time_range": 30,
    "include_trends": true,
    "include_event_breakdown": true,
    "include_roi": true
  }'
```

### Check the Response:

```json
{
  "summary": {
    "overall_accuracy": 78.5,
    ...
  },
  "event_breakdown": {...},
  "roi_metrics": {...},
  "trends": [...],
  "metadata": {...}
}
```

---

## 🔗 Connecting to Lovable Web App

Once your NEXGEN integration is working, update the Lovable Analytics page to call your GPU endpoint instead of the Supabase edge function.

### Current (Supabase):
```typescript
// Lovable calls its own Supabase function
const { data } = await supabase.functions.invoke('get-analytics');
```

### New (Your GPU):
```typescript
// Lovable calls your RunPod GPU NEXGEN ANALYTICS
const response = await fetch('https://YOUR-RUNPOD-URL/nexgen-analytics', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'x-api-key': GPU_API_KEY
  },
  body: JSON.stringify({
    predictions: await fetchPredictions(),
    results: await fetchResults(),
    time_range: 30,
    include_trends: true,
    include_event_breakdown: true,
    include_roi: true
  })
});

const analytics = await response.json();
```

---

## 📋 Checklist

### Before Integration:
- [ ] Locate your NEXGEN ANALYTICS code files
- [ ] Understand your NEXGEN input/output formats
- [ ] Identify which methods map to our placeholders
- [ ] Determine if NEXGEN is Python-compatible

### During Integration:
- [ ] Copy/import your NEXGEN code
- [ ] Replace placeholder methods in `nexgen_analytics.py`
- [ ] Update `__init__` with your engine initialization
- [ ] Test each method individually
- [ ] Test the full `/nexgen-analytics` endpoint

### After Integration:
- [ ] Deploy to RunPod
- [ ] Test from RunPod endpoint
- [ ] Update Lovable to call RunPod instead of Supabase
- [ ] Verify analytics display correctly in web app
- [ ] Monitor performance and logs

---

## 🆘 Common Issues

### Issue: Import Errors
**Cause:** NEXGEN modules not found
**Solution:** Add your NEXGEN code to the same directory or install as package

### Issue: Different Data Format
**Cause:** Your NEXGEN expects different input structure
**Solution:** Add data transformation layer in the endpoint before calling NEXGEN

### Issue: Long Processing Time
**Cause:** NEXGEN analytics take minutes to compute
**Solution:** Add background task processing or caching

### Issue: GPU Not Utilized
**Cause:** NEXGEN not configured for GPU
**Solution:** Ensure your NEXGEN engine has GPU mode enabled

---

## 📞 Next Steps

**Tell me:**
1. Where is your NEXGEN ANALYTICS code located?
2. What language/framework is it in?
3. Can you share a snippet of how it's currently used?

Then I can help you do the actual integration!

Example:
```
"My NEXGEN ANALYTICS is in /path/to/nexgen_core.py
It's Python and I currently call it like:

from nexgen_core import Analytics
engine = Analytics()
results = engine.run(data)
```

With that info, I can give you exact code to integrate it.