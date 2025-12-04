#!/usr/bin/env python3
"""
Local Data Upload Script for RodeoAI

This script uploads historical data files from your local machine to the RunPod GPU API
for processing and ingestion into the Lovable database.

Usage:
    python upload_local_data.py /path/to/data/file.csv
    python upload_local_data.py /path/to/data/folder/*.csv
    python upload_local_data.py --batch /path/to/data/folder/

Requirements:
    pip install requests

"""

import os
import sys
import argparse
import requests
from pathlib import Path
from typing import List
import json

# Configuration
RUNPOD_API_URL = os.getenv("RUNPOD_API_URL", "https://YOUR-RUNPOD-ENDPOINT.runpod.io")
GPU_API_KEY = os.getenv("GPU_API_KEY", "23XBc96KOh-fM48QEEBuqdsAZyL76tAt30V5yYC5V8o")

# Supported file types
SUPPORTED_EXTENSIONS = ['.pdf', '.csv', '.xlsx', '.xls', '.txt', '.jpg', '.jpeg', '.png']


def upload_single_file(file_path: str, auto_push: bool = True) -> dict:
    """
    Upload a single file to the GPU API

    Args:
        file_path: Path to the file
        auto_push: If True, automatically push to Lovable after processing

    Returns:
        Response from API
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {file_path.suffix}. Supported: {SUPPORTED_EXTENSIONS}")

    print(f"\n📤 Uploading: {file_path.name}")
    print(f"   Size: {file_path.stat().st_size / 1024:.2f} KB")

    url = f"{RUNPOD_API_URL}/ingest-historical-data"

    with open(file_path, 'rb') as f:
        files = {'file': (file_path.name, f, 'application/octet-stream')}
        params = {'auto_push': str(auto_push).lower()}
        headers = {'x-api-key': GPU_API_KEY}

        try:
            response = requests.post(url, files=files, params=params, headers=headers, timeout=300)
            response.raise_for_status()

            result = response.json()

            print(f"✅ Success!")
            print(f"   Events: {result['processed_data']['events_count']}")
            print(f"   Riders: {result['processed_data']['riders_count']}")
            print(f"   Predictions: {result['processed_data']['predictions_count']}")
            print(f"   Results: {result['processed_data']['results_count']}")

            if result.get('needs_review'):
                print(f"   ⚠️  Needs manual review")

            if auto_push and result.get('push_results'):
                success_count = sum(1 for r in result['push_results'] if r['status'] == 'success')
                total_count = len(result['push_results'])
                print(f"   Pushed to Lovable: {success_count}/{total_count}")

            return result

        except requests.exceptions.RequestException as e:
            print(f"❌ Error uploading {file_path.name}: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(f"   Details: {error_detail.get('detail', 'Unknown error')}")
                except:
                    print(f"   Response: {e.response.text[:200]}")
            raise


def upload_batch(file_paths: List[str], auto_push: bool = True) -> dict:
    """
    Upload multiple files using the batch endpoint

    Args:
        file_paths: List of file paths
        auto_push: If True, automatically push to Lovable after processing

    Returns:
        Aggregated response from API
    """
    print(f"\n📦 Batch uploading {len(file_paths)} files...")

    url = f"{RUNPOD_API_URL}/ingest-batch"

    files = []
    file_objects = []

    try:
        for file_path in file_paths:
            file_path = Path(file_path)
            if file_path.exists() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                f = open(file_path, 'rb')
                file_objects.append(f)
                files.append(('files', (file_path.name, f, 'application/octet-stream')))
                print(f"   📄 {file_path.name}")

        params = {'auto_push': str(auto_push).lower()}
        headers = {'x-api-key': GPU_API_KEY}

        response = requests.post(url, files=files, params=params, headers=headers, timeout=600)
        response.raise_for_status()

        result = response.json()

        print(f"\n✅ Batch upload complete!")
        print(f"   Total events: {result['totals']['events']}")
        print(f"   Total riders: {result['totals']['riders']}")
        print(f"   Total predictions: {result['totals']['predictions']}")
        print(f"   Total results: {result['totals']['results']}")

        # Show per-file status
        print(f"\n📊 Per-file results:")
        for file_result in result['file_results']:
            status = "✅" if file_result['status'] == 'success' else "❌"
            print(f"   {status} {file_result['filename']}")
            if file_result['status'] == 'error':
                print(f"      Error: {file_result.get('error', 'Unknown')}")

        return result

    except requests.exceptions.RequestException as e:
        print(f"❌ Error in batch upload: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"   Details: {error_detail.get('detail', 'Unknown error')}")
            except:
                print(f"   Response: {e.response.text[:200]}")
        raise

    finally:
        # Close all file objects
        for f in file_objects:
            f.close()


def main():
    parser = argparse.ArgumentParser(
        description='Upload historical rodeo data to RodeoAI GPU API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload a single file
  python upload_local_data.py data/results_2024.csv

  # Upload multiple files
  python upload_local_data.py data/results_2024.csv data/predictions_2024.csv

  # Upload all CSVs in a folder (batch mode)
  python upload_local_data.py --batch data/historical_data/

  # Upload without auto-pushing to Lovable (review first)
  python upload_local_data.py --no-auto-push data/results_2024.csv

Environment Variables:
  RUNPOD_API_URL - Your RunPod endpoint URL
  GPU_API_KEY    - Your GPU API key
        """
    )

    parser.add_argument('files', nargs='*', help='Files to upload')
    parser.add_argument('--batch', '-b', metavar='FOLDER', help='Upload all supported files in a folder')
    parser.add_argument('--no-auto-push', action='store_true', help='Disable auto-push to Lovable')
    parser.add_argument('--url', help='Override RUNPOD_API_URL')
    parser.add_argument('--key', help='Override GPU_API_KEY')

    args = parser.parse_args()

    # Override config if provided
    global RUNPOD_API_URL, GPU_API_KEY
    if args.url:
        RUNPOD_API_URL = args.url
    if args.key:
        GPU_API_KEY = args.key

    # Validate configuration
    if "YOUR-RUNPOD-ENDPOINT" in RUNPOD_API_URL:
        print("❌ Error: Please set RUNPOD_API_URL environment variable or use --url")
        print("   Example: export RUNPOD_API_URL=https://your-endpoint.runpod.io")
        sys.exit(1)

    auto_push = not args.no_auto_push

    print("🚀 RodeoAI Historical Data Uploader")
    print(f"   API URL: {RUNPOD_API_URL}")
    print(f"   Auto-push: {'Enabled' if auto_push else 'Disabled'}")

    try:
        if args.batch:
            # Batch mode: Upload all files in folder
            folder = Path(args.batch)
            if not folder.exists() or not folder.is_dir():
                print(f"❌ Error: Folder not found: {args.batch}")
                sys.exit(1)

            file_paths = []
            for ext in SUPPORTED_EXTENSIONS:
                file_paths.extend(folder.glob(f"*{ext}"))

            if not file_paths:
                print(f"❌ No supported files found in {args.batch}")
                sys.exit(1)

            upload_batch([str(f) for f in file_paths], auto_push=auto_push)

        elif args.files:
            if len(args.files) == 1:
                # Single file mode
                upload_single_file(args.files[0], auto_push=auto_push)
            else:
                # Multiple files via batch endpoint
                upload_batch(args.files, auto_push=auto_push)

        else:
            parser.print_help()
            sys.exit(1)

        print("\n✨ Upload complete!")

    except KeyboardInterrupt:
        print("\n\n⚠️  Upload cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()