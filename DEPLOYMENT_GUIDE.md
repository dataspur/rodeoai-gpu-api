# RodeoAI GPU API - Complete Deployment Guide

## 🎯 System Architecture Overview

You have **TWO integrated systems**:

### 1. RodeoAI Web App (Lovable/Supabase)
- **URL:** https://rodeoai.app
- **Database:** Supabase PostgreSQL
- **Frontend:** React/TypeScript
- **Backend:** Supabase Edge Functions
- **Purpose:** User-facing web application with predictions, results, analytics

### 2. RodeoAI GPU API (RunPod)
- **GitHub:** https://github.com/dataspur/rodeoai-gpu-api
- **Stack:** FastAPI + Python
- **Purpose:** GPU-accelerated ML predictions that push data TO Lovable

## 🔄 Data Flow

```
┌────────────────────────────────────────────────────────────────┐
│  Step 1: Generate Prediction                                   │
│  RunPod GPU Server                                             │
│  https://YOUR-RUNPOD-ID.runpod.io/generate-and-push          │
│                                                                │
│  POST request with:                                            │
│  - Event details (name, location, date, type)                 │
│  - Rider stats (name, rank, win_rate)                         │
│  - Optional: animal stats                                     │
└────────────────────────────────────────────────────────────────┘
                         │
                         │ GPU generates prediction
                         │ Confidence, odds, analysis
                         ▼
┌────────────────────────────────────────────────────────────────┐
│  Step 2: Auto-Push to Lovable                                 │
│  Lovable Edge Function                                        │
│  https://utbyiiyghrekahruzywo.supabase.co/functions/v1/      │
│                                                                │
│  POST /ingest-prediction with x-gpu-api-key header            │
│  - Validates API key                                          │
│  - Upserts event & rider to database                          │
│  - Inserts prediction record                                  │
└────────────────────────────────────────────────────────────────┘
                         │
                         │ Writes to database
                         ▼
┌────────────────────────────────────────────────────────────────┐
│  Step 3: Display in Web App                                   │
│  RodeoAI Web App                                              │
│  https://rodeoai.app/predictions                              │
│                                                                │
│  - GET /functions/v1/get-predictions                          │
│  - Fetches from database                                      │
│  - Filters by user's subscription tier                        │
│  - Displays on Predictions page                               │
└────────────────────────────────────────────────────────────────┘
```

## 🔑 API Key Configuration

The **same API key** is used in both systems:

```
23XBc96KOh-fM48QEEBuqdsAZyL76tAt30V5yYC5V8o
```

### Where to Set It:

#### In RunPod (Sender):
Set as environment variable when deploying your endpoint:
- **Name:** `GPU_API_KEY`
- **Value:** `23XBc96KOh-fM48QEEBuqdsAZyL76tAt30V5yYC5V8o`

#### In Lovable (Receiver):
Already set as a secret ✅
- **Name:** `GPU_API_KEY`
- **Value:** Same key as above

## 🚀 RunPod Deployment Steps

### 1. Go to RunPod
- Navigate to https://runpod.io
- Sign in to your account
- Go to **Serverless** → **Endpoints**

### 2. Click "Create Endpoint"

### 3. Configure Your Endpoint

#### Basic Settings:
- **Name:** `rodeoai-gpu-api`
- **GPU Type:** **L40S** (48GB VRAM)
- **Workers:** Start with 0 min, 3 max (scales automatically)

#### Container Configuration:
- **Source:** **GitHub Repository**
- **Repository URL:**
  ```
  https://github.com/dataspur/rodeoai-gpu-api
  ```
- **Branch:** `main`

#### Start Command:
```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

#### Environment Variables:
Add these two variables:

| Name | Value |
|------|-------|
| `GPU_API_KEY` | `23XBc96KOh-fM48QEEBuqdsAZyL76tAt30V5yYC5V8o` |
| `LOVABLE_INGEST_URL` | `https://utbyiiyghrekahruzywo.supabase.co/functions/v1` |

#### Container Settings:
- **Container Disk:** 10GB
- **Docker Build Command:** (leave default)

### 4. Click "Deploy"

The build process will:
1. Clone your GitHub repo
2. Install dependencies from `requirements.txt`
3. Start the FastAPI server
4. Show "Active" status when ready (~2-3 minutes)

### 5. Get Your Endpoint URL

Once active, RunPod will provide a URL like:
```
https://xxxxxx-8000.proxy.runpod.net
```

Save this URL - you'll need it for testing!

## 🧪 Testing Your Deployment

### Test 1: Health Check

```bash
curl https://YOUR-RUNPOD-URL/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "gpu_available": true,
  "model_version": "l40s-v1.0.0",
  "timestamp": "2024-12-04T..."
}
```

### Test 2: Generate Prediction (Local Only)

```bash
curl -X POST "https://YOUR-RUNPOD-URL/predict" \
  -H "Content-Type: application/json" \
  -H "x-api-key: 23XBc96KOh-fM48QEEBuqdsAZyL76tAt30V5yYC5V8o" \
  -d '{
    "event_type": "bull_riding",
    "rider_stats": {
      "wins": 25,
      "win_rate": 68.5
    }
  }'
```

**Expected Response:**
```json
{
  "prediction_score": 0.75,
  "confidence": 0.85,
  "factors": {
    "rider_experience": 0.35,
    "recent_performance": 0.25,
    "event_conditions": 0.20,
    "historical_matchup": 0.20
  },
  "timestamp": "2024-12-04T...",
  "model_version": "l40s-v1.0.0"
}
```

### Test 3: Generate AND Push to Lovable (Full Integration)

```bash
curl -X POST "https://YOUR-RUNPOD-URL/generate-and-push" \
  -H "Content-Type: application/json" \
  -H "x-api-key: 23XBc96KOh-fM48QEEBuqdsAZyL76tAt30V5yYC5V8o" \
  -d '{
    "event_name": "NFR Round 8 - Bull Riding",
    "event_location": "Las Vegas, NV",
    "event_date": "2024-12-15T19:00:00Z",
    "event_type": "bull_riding",
    "rider_name": "Daylon Swearingen",
    "rider_rank": 3,
    "rider_stats": {
      "wins": 28,
      "win_rate": 72.5,
      "average_score": 87.3
    }
  }'
```

**Expected Response:**
```json
{
  "prediction": {
    "prediction_score": 0.78,
    "confidence": 0.88,
    "factors": { ... },
    "timestamp": "...",
    "model_version": "l40s-v1.0.0"
  },
  "lovable_response": {
    "success": true,
    "event_id": "...",
    "rider_id": "...",
    "prediction_id": "..."
  },
  "status": "success"
}
```

### Test 4: Verify in Web App

1. Go to https://rodeoai.app
2. Sign in (or create account)
3. Navigate to **Predictions** page
4. You should see your newly pushed prediction!

## 📊 Subscription Tier Filtering

The Lovable web app filters predictions based on user tiers:

| Tier | Delay | Max/Day | History |
|------|-------|---------|---------|
| **Free** | 60 min | 5 | 7 days |
| **Pro** | 15 min | 50 | 30 days |
| **Enterprise** | 0 min | ∞ | 365 days |

## 🔧 Available Endpoints

### RunPod GPU API Endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | API info |
| `/health` | GET | Health check |
| `/predict` | POST | Generate prediction only |
| `/generate-and-push` | POST | Generate + push to Lovable |
| `/batch_predict` | POST | Multiple predictions |
| `/gpu_info` | GET | GPU hardware info |
| `/runsync` | POST | RunPod serverless handler |

### Lovable Edge Function Endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/functions/v1/ingest-prediction` | POST | Receive predictions from GPU |
| `/functions/v1/ingest-result` | POST | Receive actual results |
| `/functions/v1/get-predictions` | GET | Fetch predictions (tier-filtered) |
| `/functions/v1/get-results` | GET | Fetch results (tier-filtered) |
| `/functions/v1/get-analytics` | GET | Fetch analytics data |

## 🎛️ Monitoring & Logs

### RunPod Logs:
1. Go to RunPod dashboard
2. Click your endpoint
3. Click **Logs** tab
4. View real-time logs from FastAPI

### Lovable Logs:
1. Go to Supabase dashboard
2. Navigate to **Edge Functions**
3. Click **Logs** for each function
4. Filter by timestamp or error level

## 🐛 Troubleshooting

### Issue: Build Fails on RunPod
**Cause:** Missing dependencies or syntax error

**Solution:**
1. Check RunPod build logs
2. Verify `requirements.txt` is valid
3. Ensure Python syntax is correct
4. Try rebuilding: **Manage** → **Rebuild**

### Issue: API Key Unauthorized
**Cause:** Mismatch between RunPod and Lovable keys

**Solution:**
1. Verify `GPU_API_KEY` is set in RunPod environment variables
2. Verify same key is set in Lovable secrets
3. Ensure `x-gpu-api-key` header is included in requests

### Issue: Prediction Not Showing in Web App
**Cause:** Multiple possible causes

**Solution:**
1. Check RunPod logs - did push succeed?
2. Check Lovable `ingest-prediction` logs
3. Verify user is logged in to web app
4. Check user's subscription tier (free users have delays)
5. Look for error messages in browser console

### Issue: RunPod Endpoint Shows "Building"
**Cause:** PyTorch or large dependencies (from old code)

**Solution:**
- This shouldn't happen with current lightweight requirements
- If it does, verify you pulled latest code from GitHub
- Should build in ~2-3 minutes

## 🎉 Success Checklist

- [ ] RunPod endpoint shows "Active" status
- [ ] Health check returns 200 OK
- [ ] Generate-and-push returns success response
- [ ] Lovable ingest-prediction logs show successful insert
- [ ] Prediction appears in rodeoai.app/predictions page
- [ ] Analytics page shows updated stats

## 📞 Next Steps

1. **Deploy to RunPod** using instructions above
2. **Test the integration** with example requests
3. **Automate predictions** - Set up cron job or scheduler
4. **Monitor usage** - Check RunPod credits and Supabase limits
5. **Scale workers** - Adjust min/max workers based on demand

## 💡 Pro Tips

- **Use environment variables** for all secrets (never hardcode)
- **Monitor costs** - RunPod charges per GPU second
- **Scale to zero** - Set min workers to 0 when not in use
- **Version your models** - Update `model_version` when ML changes
- **Log everything** - Check logs regularly for errors

---

**Questions?** Check the FastAPI docs at `https://YOUR-RUNPOD-URL/docs` for interactive API documentation!