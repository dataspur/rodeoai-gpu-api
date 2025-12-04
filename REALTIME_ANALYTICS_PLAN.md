# Real-Time Analytics & "What If" Scenarios - Implementation Plan

## 🎯 Overview

This document outlines the plan to add:
1. **Real-time analytics** - Live updates as predictions come in
2. **"What if" scenarios** - Interactive simulation of hypothetical matchups
3. **Live event tracking** - Updates during actual events
4. **Interactive dashboards** - Filters, drill-downs, comparisons

---

## 🏗️ Architecture

### Current (Static) Architecture:
```
User opens /analytics
  ↓
Frontend fetches data once
  ↓
Displays static charts
  ↓
User must refresh to see updates
```

### New (Real-Time) Architecture:
```
User opens /analytics
  ↓
Frontend establishes Supabase Realtime connection
  ↓
Listens for changes to predictions/results tables
  ↓
Auto-updates charts as new data arrives
  ↓
No refresh needed!
```

### "What If" Architecture:
```
User adjusts sliders/inputs
  ↓
Frontend calls /what-if endpoint on RunPod
  ↓
GPU generates prediction for hypothetical scenario
  ↓
Returns prediction without saving to database
  ↓
User sees instant result
```

---

## 📋 Implementation Checklist

### Phase 1: "What If" Simulator (High Value, Quick Win)

#### RunPod GPU API Changes:

**Add New Endpoint:** `/what-if`
- **Method:** POST
- **Purpose:** Generate prediction for hypothetical scenario without saving
- **Input:**
  ```json
  {
    "scenario": {
      "event_type": "bull_riding",
      "rider_stats": {
        "wins": 30,
        "win_rate": 75.0,
        "average_score": 88.5
      },
      "animal_stats": {
        "buck_score": 46,
        "difficulty": "extreme"
      },
      "conditions": {
        "weather": "indoor",
        "time_of_day": "evening"
      }
    }
  }
  ```
- **Output:**
  ```json
  {
    "prediction_score": 0.78,
    "confidence": 0.85,
    "odds": 280,
    "factors": {
      "rider_experience": 0.35,
      "animal_difficulty": 0.25,
      "recent_performance": 0.25,
      "conditions": 0.15
    },
    "analysis": "Strong rider with excellent win rate facing a challenging animal...",
    "comparison": {
      "better_than_average": true,
      "percentile": 78.5
    }
  }
  ```

**Add Comparison Endpoint:** `/compare-scenarios`
- **Method:** POST
- **Purpose:** Compare multiple "what if" scenarios side-by-side
- **Input:** Array of scenarios
- **Output:** Comparative analysis

#### Lovable Web App Changes:

**New Page:** `/simulator` or tab on Analytics page
- Interactive form with sliders/inputs
- Real-time prediction as user adjusts values
- Side-by-side comparison mode
- Save favorite scenarios
- Share scenarios via URL

**UI Components:**
- Rider stats sliders (wins, win_rate, average_score)
- Animal difficulty selector
- Conditions dropdown (weather, time, arena)
- Live prediction display
- Confidence meter
- Odds calculator

---

### Phase 2: Real-Time Analytics Dashboard

#### Supabase Realtime Setup:

**Enable Realtime on Tables:**
```sql
-- Enable realtime for predictions table
ALTER PUBLICATION supabase_realtime ADD TABLE predictions;

-- Enable realtime for results table
ALTER PUBLICATION supabase_realtime ADD TABLE results;

-- Enable realtime for events table
ALTER PUBLICATION supabase_realtime ADD TABLE events;
```

#### Lovable Web App Changes:

**Update Analytics Page:**
```typescript
// Subscribe to realtime updates
const subscription = supabase
  .channel('analytics_updates')
  .on('postgres_changes',
    { event: 'INSERT', schema: 'public', table: 'predictions' },
    (payload) => {
      // Update charts in real-time
      updatePredictionChart(payload.new);
    }
  )
  .on('postgres_changes',
    { event: 'INSERT', schema: 'public', table: 'results' },
    (payload) => {
      // Update accuracy metrics in real-time
      updateAccuracyMetrics(payload.new);
    }
  )
  .subscribe();
```

**Visual Feedback:**
- Live pulse indicator when new data arrives
- Smooth chart animations
- Toast notifications for significant updates
- "X new predictions since you opened this page"

---

### Phase 3: Live Event Tracking

#### Database Changes:

**Add event_status field to events table:**
```sql
ALTER TABLE events ADD COLUMN IF NOT EXISTS live_status TEXT DEFAULT 'upcoming';
-- Values: 'upcoming', 'live', 'completed'

ALTER TABLE events ADD COLUMN IF NOT EXISTS current_round INTEGER;
ALTER TABLE events ADD COLUMN IF NOT EXISTS live_data JSONB DEFAULT '{}';
```

#### RunPod GPU API Changes:

**Add Endpoint:** `/update-live-event`
- **Method:** POST
- **Purpose:** Update predictions during live event
- **Input:**
  ```json
  {
    "event_id": "uuid",
    "current_round": 3,
    "live_scores": [
      {"rider_name": "John Doe", "score": 87.5},
      {"rider_name": "Jane Smith", "score": 89.0}
    ],
    "conditions": {
      "crowd_energy": "high",
      "weather_change": "none"
    }
  }
  ```
- **Output:** Updated predictions with adjusted confidence

**Add Endpoint:** `/confidence-adjustment`
- **Method:** POST
- **Purpose:** Adjust prediction confidence based on live data
- **Logic:** As event progresses, factor in current scores, crowd, conditions

#### Lovable Web App Changes:

**New Component:** `<LiveEventTracker />`
- Shows events currently in progress
- Real-time score updates
- Prediction confidence adjustments
- Live leaderboard
- "Event happening now" badge

**Live Predictions Page:**
- Filter: "Show only live events"
- Auto-refresh every 30 seconds
- Visual indicator of confidence changes
- Alert if prediction is about to be proven wrong/right

---

### Phase 4: Interactive Analytics

#### New Lovable Features:

**Filters:**
- Date range picker (last 7 days, 30 days, custom)
- Event type multi-select
- Rider search/filter
- Min confidence threshold slider
- Show only correct/incorrect predictions toggle

**Drill-Down Views:**
- Click on chart bar → see all predictions for that event type
- Click on rider → see all their predictions and results
- Click on event → see full breakdown with timeline

**Comparison Tools:**
- Compare two riders head-to-head
- Compare model versions (v1.0 vs v2.0 accuracy)
- Compare event types (which are we best at?)

**Export Features:**
- Download analytics as CSV
- Generate PDF report
- Share analytics dashboard link

---

## 🔧 Technical Implementation

### File Structure:

**RunPod GPU API:**
```
rodeoai-gpu-api/
├── app.py (existing)
├── lovable_client.py (existing)
├── what_if_engine.py (NEW)
├── live_event_tracker.py (NEW)
├── confidence_adjuster.py (NEW)
└── scenario_comparator.py (NEW)
```

**Lovable Web App:**
```
src/
├── pages/
│   ├── Simulator.tsx (NEW)
│   ├── LiveEvents.tsx (NEW)
│   └── Analytics.tsx (UPDATED)
├── components/
│   ├── WhatIfForm.tsx (NEW)
│   ├── LiveEventCard.tsx (NEW)
│   ├── ComparisonChart.tsx (NEW)
│   └── AnalyticsFilters.tsx (NEW)
└── hooks/
    ├── useRealtimeAnalytics.ts (NEW)
    ├── useLiveEvents.ts (NEW)
    └── useWhatIfSimulator.ts (NEW)
```

---

## 📊 Data Flow Examples

### Example 1: "What If" Simulation

```
User: "What if [Rider X] with 75% win rate faces [Animal Y] with
       buck score 48 in indoor arena?"

Frontend calls: POST /what-if
{
  "scenario": {
    "event_type": "bull_riding",
    "rider_stats": {"win_rate": 75.0},
    "animal_stats": {"buck_score": 48},
    "conditions": {"weather": "indoor"}
  }
}

RunPod GPU:
1. Extracts features from scenario
2. Runs through ML model
3. Calculates confidence and odds
4. Compares to historical data
5. Returns prediction

Frontend displays:
- Prediction score: 72%
- Confidence: 85%
- Odds: 2.8:1
- "This is better than 78% of similar matchups"
```

### Example 2: Real-Time Analytics Update

```
RunPod pushes new prediction:
POST /ingest-prediction → Supabase

Supabase triggers Realtime event:
"INSERT on predictions table"

All connected clients receive:
{
  "event": "INSERT",
  "table": "predictions",
  "new": {
    "id": "...",
    "confidence": 87.5,
    "event_type": "bull_riding",
    ...
  }
}

Analytics page automatically:
1. Adds data point to chart
2. Updates accuracy metrics
3. Shows toast: "New prediction: John Doe (87.5% confidence)"
4. Animates chart update
```

### Example 3: Live Event Tracking

```
Event starts:
POST /update-live-event
{
  "event_id": "nfr-round-8",
  "live_status": "live"
}

Every round:
POST /update-live-event
{
  "event_id": "nfr-round-8",
  "current_round": 3,
  "live_scores": [...]
}

RunPod:
1. Fetches original predictions
2. Calculates confidence adjustments based on live data
3. Updates predictions table with adjusted confidence

Frontend:
1. Shows "LIVE" badge
2. Updates confidence in real-time
3. Shows comparison: "Original: 85% → Now: 78%"
4. Explains: "Confidence dropped due to lower-than-expected scores"
```

---

## 💡 User Experience Examples

### "What If" Simulator Page:

```
┌─────────────────────────────────────────────────────────────┐
│  🎮 Scenario Simulator                                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Event Type: [Bull Riding ▼]                               │
│                                                             │
│  Rider Stats:                                               │
│  Wins: [════════○─────────] 30                             │
│  Win Rate: [══════════○───] 75%                            │
│  Avg Score: [═════════○────] 88.5                          │
│                                                             │
│  Animal Stats:                                              │
│  Buck Score: [════════════○] 48                            │
│  Difficulty: [Extreme ▼]                                    │
│                                                             │
│  Conditions:                                                │
│  Weather: [Indoor ▼]                                        │
│  Time: [Evening ▼]                                          │
│                                                             │
│  ┌───────────────────────────────────────────────────┐     │
│  │  📊 PREDICTION                                    │     │
│  │                                                   │     │
│  │  Success Probability: 72%                        │     │
│  │  Confidence: 85%                                 │     │
│  │  Odds: 2.8:1                                     │     │
│  │                                                   │     │
│  │  💡 This is better than 78% of similar matchups  │     │
│  └───────────────────────────────────────────────────┘     │
│                                                             │
│  [Compare Another Scenario] [Save Scenario] [Share]        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Live Events Page:

```
┌─────────────────────────────────────────────────────────────┐
│  🔴 LIVE EVENTS                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🔴 NFR Round 8 - Bull Riding                              │
│  Las Vegas, NV • Started 15 minutes ago                     │
│                                                             │
│  Current Round: 3 of 15                                     │
│                                                             │
│  Top Predictions:                                           │
│  1. Stetson Wright    87% → 89% ↑  [LIVE]                 │
│  2. Daylon Swearingen 82% → 78% ↓                          │
│  3. Josh Frost        76% → 76% →                          │
│                                                             │
│  📊 Live Leaderboard:                                       │
│  1. Stetson Wright - 91.5 pts                              │
│  2. Daylon Swearingen - 88.0 pts                           │
│  3. Josh Frost - 87.5 pts                                  │
│                                                             │
│  [View Full Predictions] [Watch Live Stream]                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Priority Recommendation

### **Phase 1: "What If" Simulator (Start Here)**

**Why?**
- High user value - users can experiment
- Quick to implement - just new endpoint + UI
- Doesn't require Realtime infrastructure
- Great marketing feature ("Try our AI predictor!")
- Works immediately without waiting for live events

**Effort:** Medium (2-3 days)
**Value:** High
**Risk:** Low

### Phase 2: Real-Time Analytics

**Why?**
- Makes app feel modern and alive
- Reduces server load (no polling needed)
- Better user engagement

**Effort:** Medium (3-4 days)
**Value:** Medium-High
**Risk:** Low (Supabase Realtime is mature)

### Phase 3: Live Event Tracking

**Why?**
- Highest wow factor
- Most complex to get right
- Requires actual live event data feed

**Effort:** High (1-2 weeks)
**Value:** Very High
**Risk:** Medium (depends on data availability)

### Phase 4: Interactive Analytics

**Why?**
- Nice-to-have improvements
- Can be done incrementally

**Effort:** Medium (1 week)
**Value:** Medium
**Risk:** Low

---

## 🚀 Quick Start: Implementing "What If" Simulator

### Step 1: Add to RunPod GPU API

```python
# what_if_engine.py
class WhatIfEngine:
    def simulate_scenario(self, scenario):
        # Extract features
        # Run through model
        # Return prediction
        pass
```

### Step 2: Add Endpoint to app.py

```python
@app.post("/what-if")
async def what_if_simulator(request: WhatIfRequest):
    engine = WhatIfEngine()
    prediction = engine.simulate_scenario(request.scenario)
    return prediction
```

### Step 3: Create Lovable UI

```typescript
// pages/Simulator.tsx
export default function Simulator() {
  const [scenario, setScenario] = useState({...});
  const [prediction, setPrediction] = useState(null);

  const simulate = async () => {
    const response = await fetch(`${RUNPOD_URL}/what-if`, {
      method: 'POST',
      body: JSON.stringify({ scenario })
    });
    setPrediction(await response.json());
  };

  return (
    <div>
      <ScenarioForm onChange={setScenario} />
      <Button onClick={simulate}>Simulate</Button>
      <PredictionDisplay prediction={prediction} />
    </div>
  );
}
```

---

## 📞 Next Steps

**Immediate (Today):**
1. Review this plan
2. Decide on Phase 1 (What If Simulator)
3. I can implement it right now if you want!

**This Week:**
- Implement "What If" Simulator
- Test with various scenarios
- Deploy to RunPod

**Next Week:**
- Add Real-Time Analytics
- Enable Supabase Realtime
- Update Analytics page

**Future:**
- Live Event Tracking
- Interactive Filters
- Advanced Comparisons

---

**Ready to start building?** Let me know which phase you want to tackle first!