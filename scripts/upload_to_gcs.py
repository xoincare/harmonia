#!/usr/bin/env python3
"""
Harmonia GCS Uploader
Uploads harmonia.db and all MIDI datasets to Google Cloud Storage.
Usage: python3 scripts/upload_to_gcs.py
"""
import os, sys
from google.cloud import storage

BUCKET_NAME = "harmonia-midi"
DB_FILE = "harmonia.db"
DATASETS_DIR = "/home/cyclomethane/.openclaw/workspace/midi/datasets"

def upload_file(bucket, local_path, remote_path):
    print(f"Uploading {local_path} to gs://{BUCKET_NAME}/{remote_path}...")
    blob = bucket.blob(remote_path)
    blob.upload_from_filename(local_path)

def main():
    try:
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        if not bucket.exists():
            print(f"❌ Bucket {BUCKET_NAME} does not exist. Please create it first.")
            return

        # 1. Upload Database
        if os.path.exists(DB_FILE):
            upload_file(bucket, DB_FILE, DB_FILE)
        
        # 2. Upload Datasets
        count = 0
        for root, dirs, files in os.walk(DATASETS_DIR):
            for f in files:
                if f.endswith(('.mid', '.midi')):
                    local_path = os.path.join(root, f)
                    rel_path = os.path.relpath(local_path, DATASETS_DIR)
                    remote_path = f"datasets/{rel_path}"
                    upload_file(bucket, local_path, remote_path)
                    count += 1
                    if count % 100 == 0:
                        print(f"  Uploaded {count} files...")

        print(f"✅ Successfully uploaded {count} files and the database.")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
