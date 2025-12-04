# Historical Data Ingestion Guide

## 🎯 Overview

You can now ingest historical rodeo data from your local machine! The complete pipeline is ready:

```
YOUR COMPUTER          →        RUNPOD GPU         →      LOVABLE DATABASE
(historical files)     upload   (text extraction)   push   (rodeoai.app)
```

---

## ✅ What We Built

### Complete Data Pipeline:

1. **Local Upload Script** (`upload_local_data.py`)
   - Easy CLI tool to upload files from your computer
   - Supports single file or batch folder uploads

2. **GPU Processing** (`data_processor.py`)
   - Extracts text from PDFs, CSVs, Excel, images
   - Cleans and formats data
   - Validates against Lovable schema

3. **Auto-Push to Lovable** (`lovable_client.py`)
   - Automatically sends processed data to rodeoai.app
   - Updates database in real-time
   - Data appears immediately in web app

### Supported File Types:
- ✅ CSV files (.csv)
- ✅ Excel files (.xlsx, .xls)
- ✅ Text files (.txt)
- ⏳ PDF files (.pdf) - Ready for PyPDF2 integration
- ⏳ Images (.jpg, .png) - Ready for OCR integration

---

## 🚀 Quick Start (RIGHT NOW!)

### Step 1: Deploy to RunPod (if not already done)

Follow the instructions in `DEPLOYMENT_GUIDE.md` to deploy your API to RunPod.

Once deployed, you'll get a URL like:
```
https://xxxxxx-8000.proxy.runpod.net
```

### Step 2: Set Up Your Local Environment

On your local machine (where your historical data files are):

```bash
# Install required package
pip install requests

# Set your RunPod endpoint URL
export RUNPOD_API_URL="https://YOUR-RUNPOD-ENDPOINT.runpod.io"

# Set your API key (same key as before)
export GPU_API_KEY="23XBc96KOh-fM48QEEBuqdsAZyL76tAt30V5yYC5V8o"
```

### Step 3: Upload Your First File!

```bash
# Upload a single CSV file
python upload_local_data.py /path/to/historical_results.csv
```

**That's it!** The script will:
1. Upload the file to RunPod GPU
2. GPU extracts and processes the data
3. GPU pushes to Lovable database
4. You see results in rodeoai.app immediately!

---

## 📊 File Format Examples

### CSV Format for Results:

```csv
event_name,location,date,event_type,rider_name,rank,score,placement,result
NFR Round 7,Las Vegas NV,2024-12-14,bull_riding,Stetson Wright,1,91.5,1,Win
NFR Round 7,Las Vegas NV,2024-12-14,barrel_racing,Hailey Kinsel,1,13.42,1,Win
```

### CSV Format for Predictions:

```csv
event_name,location,date,event_type,rider_name,prediction,confidence,odds,model_version
NFR Round 8,Las Vegas NV,2024-12-15,bull_riding,Daylon Swearingen,Win,87.5,280,v1.0
```

### CSV Format for Events:

```csv
name,location,date,event_type,prize_pool
NFR Round 7,Las Vegas NV,2024-12-14,bull_riding,500000
NFR Round 7,Las Vegas NV,2024-12-14,barrel_racing,350000
```

**Smart Detection:** The system automatically detects which type of CSV you're uploading!

---

## 📁 Batch Upload (Multiple Files)

### Upload All Files in a Folder:

```bash
python upload_local_data.py --batch /path/to/historical_data/
```

This will:
- Find all CSV, Excel, PDF, image, and text files
- Upload them all in one batch
- Process each file on GPU
- Show aggregate results

### Upload Specific Files:

```bash
python upload_local_data.py file1.csv file2.xlsx file3.pdf
```

---

## 🎛️ Advanced Options

### Review Before Pushing to Lovable:

```bash
# Upload and process but DON'T auto-push to database yet
python upload_local_data.py --no-auto-push historical_data.csv
```

You'll get back the processed data for review, then you can manually push later.

### Override Configuration:

```bash
# Specify URL and API key via command line
python upload_local_data.py \
  --url https://your-endpoint.runpod.io \
  --key your-api-key \
  historical_data.csv
```

---

## 📝 What Happens During Upload

```
┌─────────────────────────────────────────────────────────┐
│  1. YOUR COMPUTER                                       │
│  python upload_local_data.py file.csv                   │
│  ✓ Validates file type                                  │
│  ✓ Uploads to RunPod                                    │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  2. RUNPOD GPU API                                      │
│  POST /ingest-historical-data                           │
│  ✓ Receives file                                        │
│  ✓ Detects file type (CSV, Excel, PDF, etc.)           │
│  ✓ Extracts text/data                                   │
│  ✓ Parses into events, riders, predictions, results    │
│  ✓ Validates data                                       │
│  ✓ Formats for Lovable schema                          │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  3. AUTO-PUSH TO LOVABLE                                │
│  POST /functions/v1/ingest-prediction                   │
│  POST /functions/v1/ingest-result                       │
│  ✓ Upserts events                                       │
│  ✓ Upserts riders                                       │
│  ✓ Inserts predictions                                  │
│  ✓ Inserts results                                      │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  4. LOVABLE DATABASE (Supabase)                         │
│  ✓ Data stored in database                              │
│  ✓ Available to web app                                 │
│  ✓ Real-time analytics updated                          │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  5. RODEOAI.APP                                         │
│  ✓ Predictions page shows new data                      │
│  ✓ Results page updated                                 │
│  ✓ Analytics recalculated                               │
│  ✓ AI chat has new context                             │
└─────────────────────────────────────────────────────────┘
```

---

## 📤 Example Output

### Single File Upload:

```
🚀 RodeoAI Historical Data Uploader
   API URL: https://your-endpoint.runpod.io
   Auto-push: Enabled

📤 Uploading: nfr_results_2024.csv
   Size: 145.32 KB

✅ Success!
   Events: 8
   Riders: 45
   Predictions: 0
   Results: 120
   Pushed to Lovable: 120/120

✨ Upload complete!
```

### Batch Upload:

```
📦 Batch uploading 5 files...
   📄 nfr_results_2024.csv
   📄 pbr_predictions_2024.csv
   📄 historical_data_2023.xlsx
   📄 rider_stats.csv
   📄 event_schedule.csv

✅ Batch upload complete!
   Total events: 156
   Total riders: 234
   Total predictions: 450
   Total results: 789

📊 Per-file results:
   ✅ nfr_results_2024.csv
   ✅ pbr_predictions_2024.csv
   ✅ historical_data_2023.xlsx
   ✅ rider_stats.csv
   ✅ event_schedule.csv

✨ Upload complete!
```

---

## 🔧 Enhancing the Pipeline

### Currently Supported:
- ✅ CSV parsing with smart detection
- ✅ Excel file support (multiple sheets)
- ✅ Data cleaning and validation
- ✅ Auto-push to Lovable
- ✅ Batch uploads

### Ready to Add (TODOs in code):

#### 1. PDF Text Extraction:
```bash
# Add to requirements.txt
pip install PyPDF2
# or
pip install pdfplumber
```

Then update `data_processor.py` method `_extract_pdf_text_placeholder()` to use the library.

#### 2. OCR for Scanned Documents/Images:
```bash
# Add to requirements.txt
pip install pytesseract pillow
```

Then update `data_processor.py` method `_extract_image_text_placeholder()`.

#### 3. RAG/Embeddings for Context:
```bash
# Add to requirements.txt
pip install sentence-transformers
pip install chromadb
```

Add embedding generation in `data_processor.py` and store vectors for AI chat context.

---

## 🎯 Real-World Usage Scenarios

### Scenario 1: Historic NFR Results

You have years of NFR results in CSV files:

```bash
cd ~/rodeo_data/nfr_historical/
python /path/to/upload_local_data.py --batch ./
```

**Result:** All NFR historical data in your rodeoai.app database!

### Scenario 2: Scanned Document PDFs

You have old rodeo results as scanned PDFs:

```bash
# First, add PDF extraction (see above)
# Then upload
python upload_local_data.py old_results_1998.pdf
```

### Scenario 3: Excel Workbooks

You have comprehensive Excel files with multiple sheets:

```bash
python upload_local_data.py comprehensive_2024_data.xlsx
```

The system processes each sheet separately!

### Scenario 4: Mixed File Types

You have a folder with CSVs, Excel files, PDFs, and images:

```bash
python upload_local_data.py --batch ~/rodeo_data/mixed/
```

The system detects and processes each file appropriately!

---

## 🛠️ Troubleshooting

### Issue: "Please set RUNPOD_API_URL environment variable"

**Solution:**
```bash
export RUNPOD_API_URL="https://your-endpoint.runpod.io"
```

Or use `--url` flag:
```bash
python upload_local_data.py --url https://your-endpoint.runpod.io file.csv
```

### Issue: "401 Unauthorized"

**Solution:** Check your API key is correct:
```bash
export GPU_API_KEY="23XBc96KOh-fM48QEEBuqdsAZyL76tAt30V5yYC5V8o"
```

### Issue: "needs_review: true" in output

**Meaning:** The system detected data that might need manual verification.

**Solution:** Check the Lovable database and verify the data looks correct.

### Issue: File not uploading or timing out

**Solution:**
- Check file size (very large files may timeout)
- Check your internet connection
- Try with `--no-auto-push` to process without pushing (faster)

---

## 📊 Monitoring Your Data

### Check in RodeoAI Web App:

1. Go to https://rodeoai.app
2. Navigate to **Predictions** page
3. Your uploaded data should appear!
4. Go to **Results** page to see historical results
5. Check **Analytics** to see updated metrics

### Check in Supabase:

1. Go to Supabase dashboard
2. Navigate to **Table Editor**
3. Check tables: `events`, `riders`, `predictions`, `results`
4. Your data should be there!

---

## 🎯 Next Steps

### Immediate (You Can Do This Now):

1. ✅ Organize your historical data files
2. ✅ Deploy GPU API to RunPod (if not done)
3. ✅ Run `upload_local_data.py` with your first file
4. ✅ Verify data in rodeoai.app
5. ✅ Upload more files!

### Soon (When You Need It):

1. Add PDF extraction library
2. Add OCR for scanned documents
3. Integrate RAG/embeddings
4. Add your NEXGEN ANALYTICS code
5. Set up automated daily uploads

---

## 💡 Pro Tips

1. **Start Small:** Test with one small CSV file first
2. **Batch Wisely:** Upload 10-20 files at a time, not hundreds
3. **Check Results:** Verify first few uploads before doing bulk
4. **Use --no-auto-push:** If unsure, review data before pushing
5. **Keep Backups:** Always keep original files as backup

---

## 🚀 START UPLOADING NOW!

You have everything you need to start ingesting historical data **right now**:

```bash
# 1. Make sure RunPod is deployed

# 2. Set your configuration
export RUNPOD_API_URL="https://your-endpoint.runpod.io"
export GPU_API_KEY="23XBc96KOh-fM48QEEBuqdsAZyL76tAt30V5yYC5V8o"

# 3. Upload your first file!
python upload_local_data.py ~/rodeo_data/first_file.csv

# 4. Watch it appear in rodeoai.app!
```

**Questions?** Check the troubleshooting section or review the code in `data_processor.py` and `upload_local_data.py`!