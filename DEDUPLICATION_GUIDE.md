# Deduplication & Smart Triage Guide

## 🎯 Overview

Your data ingestion pipeline now has **production-grade deduplication and smart triage**:

1. **Deduplication** - Never process the same data twice
2. **Smart Triage** - Reject irrelevant files in <1 second
3. **Quality Assessment** - Ensure data meets standards
4. **Review Queue** - Manual review for uncertain cases

---

## ✅ What Problems This Solves

### Before (Without Deduplication/Triage):
❌ Upload `nfr_results_2024.csv` twice → Process twice, waste GPU time
❌ Upload `my_recipe_collection.csv` → Process, extract nothing useful
❌ Upload corrupt CSV → Push bad data to database
❌ Upload unclear format → Push incomplete data
❌ No way to know which files failed or need review

### After (With Deduplication/Triage):
✅ Upload `nfr_results_2024.csv` twice → **2nd upload rejected instantly**
✅ Upload `my_recipe_collection.csv` → **Rejected in <1 sec (irrelevant)**
✅ Upload corrupt CSV → **Rejected (poor quality), sent to review queue**
✅ Upload unclear format → **Sent to review queue for manual check**
✅ `/review-queue` endpoint shows all files needing attention

---

## 🔄 The 6-Step Processing Pipeline

Every uploaded file goes through this pipeline:

```
┌─────────────────────────────────────────────────────────┐
│  STEP 1: Check Duplicate File                          │
│  - Compute SHA-256 hash of file content                │
│  - Check if hash was seen before                       │
│  - If duplicate → REJECT immediately                   │
└─────────────────────────────────────────────────────────┘
                         ↓ (< 1ms)
┌─────────────────────────────────────────────────────────┐
│  STEP 2: Smart Triage (Relevance Check)                │
│  - Sample first 1000 bytes                             │
│  - Score based on rodeo keywords                       │
│  - If irrelevant → REJECT, send to review queue       │
│  - Fast: ~100ms                                        │
└─────────────────────────────────────────────────────────┘
                         ↓ (If relevant or uncertain)
┌─────────────────────────────────────────────────────────┐
│  STEP 3: Extract Data (GPU Processing)                 │
│  - Parse CSV/Excel/PDF/Image                           │
│  - Extract events, riders, predictions, results        │
│  - Format to Lovable schema                            │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  STEP 4: Check Duplicate Data (Semantic)               │
│  - Hash extracted data (not file)                      │
│  - Catches same data in different formats              │
│  - If duplicate → REJECT                               │
└─────────────────────────────────────────────────────────┘
                         ↓ (If unique data)
┌─────────────────────────────────────────────────────────┐
│  STEP 5: Assess Data Quality                           │
│  - Check for empty results                             │
│  - Validate critical fields present                    │
│  - Score data completeness (0-100)                     │
│  - If poor quality → REJECT, send to review queue     │
│  - If uncertain → Send to review queue (but process)  │
└─────────────────────────────────────────────────────────┘
                         ↓ (If quality >= 60)
┌─────────────────────────────────────────────────────────┐
│  STEP 6: Auto-Push to Lovable                          │
│  - Push events, riders, predictions, results           │
│  - Data appears in rodeoai.app                         │
│  - SUCCESS!                                            │
└─────────────────────────────────────────────────────────┘
```

---

## 🔍 How Deduplication Works

### 1. Exact File Deduplication

**Detects:** Same file uploaded twice

```python
# SHA-256 hash of file content
file_hash = sha256(file_content)

if file_hash in seen_hashes:
    return "DUPLICATE FILE"
```

**Example:**
```bash
# First upload
python upload_local_data.py nfr_results_2024.csv
# ✅ Success

# Second upload (same file)
python upload_local_data.py nfr_results_2024.csv
# ❌ DUPLICATE: This file was already uploaded
```

### 2. Semantic Data Deduplication

**Detects:** Same data in different formats

```python
# Hash the actual data, not the file
data_hash = sha256(canonical_representation(extracted_data))

if data_hash in seen_hashes:
    return "DUPLICATE DATA"
```

**Example:**
```bash
# Upload CSV
python upload_local_data.py nfr_results.csv
# ✅ Success

# Convert to Excel and upload
python upload_local_data.py nfr_results.xlsx
# ❌ DUPLICATE DATA: This data was already uploaded (possibly in different format)
```

---

## 🎯 How Smart Triage Works

### Keyword-Based Scoring

The system maintains two keyword lists:

#### Rodeo Keywords (Positive Score):
- bull, bronc, barrel, roping, wrestling, steer, calf
- prca, pbr, wpra, nfr, wnfr, rodeo
- las vegas, thomas mack, cowboy, arena
- score, time, seconds, points, rank, standings

#### Irrelevant Keywords (Negative Score):
- recipe, cooking, diet, fashion, weather
- stock market, finance, real estate, invoice
- medical, prescription, resume, cv

### Scoring Logic:

```python
score = 0
score += count(rodeo_keywords in text)
score -= count(irrelevant_keywords in text) * 2  # Weight negative more

if score >= 2:
    verdict = "relevant" → PROCESS
elif score <= -2:
    verdict = "irrelevant" → REJECT
else:
    verdict = "uncertain" → REVIEW QUEUE
```

### Examples:

#### Example 1: Relevant File
```
Filename: nfr_round_7_bull_riding.csv
Content: "Stetson Wright, bull riding, 91.5 points, Las Vegas..."

Rodeo keywords: 5 matches (bull, riding, points, las vegas, wright)
Irrelevant keywords: 0
Score: +5
Verdict: RELEVANT → PROCESS
```

#### Example 2: Irrelevant File
```
Filename: chocolate_cake_recipe.csv
Content: "ingredients, flour, sugar, chocolate, cooking time..."

Rodeo keywords: 0
Irrelevant keywords: 3 matches (recipe, cooking, ingredients)
Score: -6
Verdict: IRRELEVANT → REJECT
```

#### Example 3: Uncertain File
```
Filename: data_2024.csv
Content: "name, location, date, score..."

Rodeo keywords: 1 match (score)
Irrelevant keywords: 0
Score: +1
Verdict: UNCERTAIN → REVIEW QUEUE
```

---

## 📋 Quality Assessment

After data extraction, quality is scored 0-100:

### Quality Score Deductions:

| Issue | Deduction |
|-------|-----------|
| No data extracted | -100 (instant reject) |
| Very few records (< 5) | -30 |
| Missing event names | -20 |
| Missing rider names | -20 |
| Unclear structure | -25 |
| Low extraction confidence | -15 |

### Quality Verdicts:

| Score | Verdict | Action |
|-------|---------|--------|
| 80-100 | Excellent | PROCESS |
| 60-79 | Good | PROCESS |
| 40-59 | Fair | REVIEW QUEUE |
| 20-39 | Poor | REVIEW QUEUE |
| 0-19 | Very Poor | REJECT |

---

## 🗂️ Review Queue

Files sent to review queue can be viewed:

```bash
# View review queue
curl -H "x-api-key: YOUR_KEY" \
  https://YOUR-RUNPOD-URL/review-queue
```

**Response:**
```json
{
  "status": "success",
  "queue_length": 3,
  "items": [
    {
      "filename": "unclear_format.csv",
      "reason": "Uncertain quality or relevance",
      "file_hash": "abc123...",
      "assessment": {
        "verdict": "uncertain",
        "confidence": 45,
        "quality_score": 55
      },
      "added_at": "2024-12-04T...",
      "status": "pending_review"
    },
    {
      "filename": "recipe_book.csv",
      "reason": "File appears irrelevant",
      "assessment": {
        "verdict": "irrelevant",
        "reasons": ["Contains cooking/recipe keywords"]
      }
    }
  ]
}
```

---

## 🎛️ Override Options

### Skip Deduplication (Force Re-upload):

```bash
python upload_local_data.py --skip-dedup nfr_results.csv
```

Or via API:
```bash
curl -X POST "https://YOUR-RUNPOD-URL/ingest-historical-data" \
  -F "file=@data.csv" \
  -F "skip_deduplication=true"
```

**Use case:** You updated the file and want to re-upload

### Skip Triage (Force Process Everything):

```bash
python upload_local_data.py --skip-triage data.csv
```

Or via API:
```bash
curl -X POST "https://YOUR-RUNPOD-URL/ingest-historical-data" \
  -F "file=@data.csv" \
  -F "skip_triage=true"
```

**Use case:** You know the file is relevant but system might flag it

---

## 📊 Enhanced Response Structure

Every upload now returns comprehensive status:

```json
{
  "status": "success",  // or "duplicate", "rejected", "needs_review"
  "filename": "nfr_2024.csv",
  "file_size": 145320,

  "deduplication": {
    "file_duplicate": false,
    "data_duplicate": false
  },

  "triage": {
    "verdict": "relevant",
    "confidence": 95,
    "reasons": [
      "Filename contains rodeo keywords",
      "Content sample contains rodeo keywords",
      "Data file format (CSV/Excel)"
    ]
  },

  "quality": {
    "verdict": "excellent",
    "score": 95,
    "issues": [],
    "warnings": []
  },

  "processed_data": {
    "events_count": 8,
    "riders_count": 45,
    "predictions_count": 0,
    "results_count": 120
  },

  "action_taken": "process",  // or "review", "reject"
  "review_queue_id": null,  // or queue ID if in review

  "push_results": [
    {"type": "result", "status": "success", "id": "..."},
    ...
  ]
}
```

---

## 💡 Real-World Scenarios

### Scenario 1: Bulk Historical Upload

You're uploading 200 historical CSV files:

```bash
python upload_local_data.py --batch ~/rodeo_data/historical/
```

**Result:**
- 180 files: ✅ Processed successfully
- 5 files: ⚠️  Duplicates (rejected)
- 10 files: ⚠️  Uncertain quality (review queue)
- 5 files: ❌ Irrelevant (rejected)

**You only need to manually review 10 files** instead of all 200!

### Scenario 2: Mixed Quality Folder

Your data folder has:
- Rodeo results CSVs ✅
- Personal notes TXT files ❌
- Recipe spreadsheets ❌
- Some corrupt files ❌

```bash
python upload_local_data.py --batch ~/messy_folder/
```

**Smart triage automatically:**
- Processes only rodeo CSVs
- Rejects recipes and notes instantly
- Flags corrupt files for review
- Saves hours of manual sorting!

### Scenario 3: Re-upload After Fixing

You uploaded a file with issues, fixed it, and want to re-upload:

```bash
# First upload (has issues)
python upload_local_data.py data.csv
# → Sent to review queue

# Fix the file
# ...edit data.csv...

# Re-upload with dedup skip
python upload_local_data.py --skip-dedup data.csv
# → Processes the fixed version
```

---

## 🚀 Performance Benefits

### Without Deduplication/Triage:
- ❌ Process 200 files: ~30 minutes GPU time
- ❌ 15 duplicates: Wasted 4.5 minutes
- ❌ 20 irrelevant files: Wasted 6 minutes
- ❌ Total wasted: 10.5 minutes + database bloat

### With Deduplication/Triage:
- ✅ Reject 15 duplicates: <1 second total
- ✅ Reject 20 irrelevant: <20 seconds total
- ✅ Process only 165 relevant files: ~24.75 minutes
- ✅ Time saved: 10.5 minutes (35% faster!)
- ✅ Database stays clean

---

## 🔧 Customization

### Add Your Own Keywords:

Edit `deduplication.py`:

```python
# Add more rodeo keywords
self.rodeo_keywords = {
    'bull', 'bronc', 'barrel',
    # Add your custom keywords:
    'rope', 'chute', 'bucking', 'spurring', ...
}

# Add more irrelevant keywords
self.irrelevant_keywords = {
    'recipe', 'cooking',
    # Add your custom exclusions:
    'unrelated_keyword', ...
}
```

### Adjust Quality Thresholds:

```python
# In assess_data_quality():
if total_records < 5:  # Change threshold
    quality_score -= 30
```

---

## 📈 Monitoring

### Check Review Queue Regularly:

```bash
curl -H "x-api-key: YOUR_KEY" \
  https://YOUR-RUNPOD-URL/review-queue | jq
```

### Watch Logs:

```
INFO: Triage verdict: relevant (score: 5)
INFO: Quality verdict: excellent (score: 95)
WARNING: DUPLICATE FILE DETECTED: nfr_2024.csv
WARNING: IRRELEVANT FILE: recipes.csv
INFO: NEEDS REVIEW: unclear_data.csv
```

---

## ✅ Best Practices

1. **Run with defaults first** - Let deduplication and triage work
2. **Check review queue daily** - Review flagged files
3. **Use skip flags sparingly** - Only when you're certain
4. **Monitor rejection reasons** - Adjust keywords if needed
5. **Keep backups** - Always keep original files

---

## 🎯 Summary

You now have **production-grade data ingestion**:

✅ **No duplicate processing** - Saves GPU time and money
✅ **Fast irrelevance detection** - Rejects junk in <1 second
✅ **Quality guaranteed** - Only good data reaches database
✅ **Manual review for edge cases** - Human oversight when needed
✅ **Comprehensive logging** - Full transparency
✅ **Override options** - Flexibility when needed

**Result:** Clean, efficient, professional data pipeline! 🚀