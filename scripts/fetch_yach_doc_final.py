#!/usr/bin/env python3
"""
Fetch Yach documents using correct gettoken endpoint
Based on OpenClaw Yach extension oapi.ts
"""
import requests
import json
import time
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

# Read config
config_path = Path.home() / ".openclaw" / "workspace" / ".yach-config.json"
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

BASE_URL = config['base_url']
APPKEY = config['appkey']
APPSECRET = config['appsecret']

def get_access_token():
    """Get access token using /gettoken endpoint"""
    url = f"{BASE_URL}/gettoken"
    params = {
        "appkey": APPKEY,
        "appsecret": APPSECRET
    }

    print(f"Getting access token from: {url}")
    resp = requests.get(url, params=params)
    resp.raise_for_status()

    data = resp.json()
    print(f"Token response: {json.dumps(data, ensure_ascii=False)}")

    if data.get('code') != 200 or not data.get('obj'):
        raise Exception(f"Failed to get token: {data}")

    access_token = data['obj']['access_token']
    expired_time = data['obj']['expired_time']

    print(f"Got token (expires at {expired_time}): {access_token[:20]}...")
    return access_token

def export_doc(access_token, doc_id, output_path):
    """Export Yach document"""
    # Start export - try with access_token in payload instead of header
    url = f"{BASE_URL}/openapi/v2/doc/export/async"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "file_guid": doc_id,
        "type": "xlsx",
        "access_token": access_token
    }

    print(f"\nStarting export for doc_id: {doc_id}")
    resp = requests.post(url, json=payload, headers=headers)

    if resp.status_code != 200:
        raise Exception(f"Export failed: {resp.status_code} {resp.text}")

    data = resp.json()
    # Yach API uses code=200 for success, not code=0
    if data.get('code') != 200:
        raise Exception(f"Export API error: {data}")

    task_id = data['obj']['task_id']
    print(f"Task ID: {task_id}")

    # Poll for completion
    poll_url = f"{BASE_URL}/openapi/v2/doc/export/async/process"
    # Yach might need access_token in poll request too
    params = {"task_id": task_id, "access_token": access_token}

    print("\nPolling for completion...")
    for i in range(30):  # Max 60 seconds
        time.sleep(2)

        poll_resp = requests.get(poll_url, params=params, headers=headers)
        if poll_resp.status_code != 200:
            print(f"  Poll HTTP error: {poll_resp.status_code}")
            continue

        poll_data = poll_resp.json()
        print(f"  Poll response: {json.dumps(poll_data, ensure_ascii=False)}")

        if poll_data.get('code') != 200:
            print(f"  Poll API error code: {poll_data.get('code')}")
            continue

        result = poll_data['obj']
        progress = result.get('progress', 0)

        # Check if download_url is available (which means it's ready)
        if 'download_url' in result and progress == 100:
            download_url = result['download_url']
            print(f"\nDownload URL: {download_url}")

            # Download
            print(f"Downloading to: {output_path}")
            dl_resp = requests.get(download_url, stream=True)
            dl_resp.raise_for_status()

            with open(output_path, 'wb') as f:
                for chunk in dl_resp.iter_content(chunk_size=8192):
                    f.write(chunk)

            print(f"SUCCESS!")
            return output_path

    raise TimeoutError("Export timed out")

def compare_files(new_file, old_file):
    """Compare two Excel files"""
    if not Path(old_file).exists():
        print(f"\nNo previous file to compare")
        return

    print(f"\n{'='*60}")
    print(f"Comparing with previous version")
    print(f"{'='*60}")

    old_xl = pd.ExcelFile(old_file)
    new_xl = pd.ExcelFile(new_file)

    old_sheets = set(old_xl.sheet_names)
    new_sheets = set(new_xl.sheet_names)

    added = new_sheets - old_sheets
    removed = old_sheets - new_sheets
    common = old_sheets & new_sheets

    print(f"\nSheets: {len(new_sheets)} total")
    if added:
        print(f"  + Added: {', '.join(added)}")
    if removed:
        print(f"  - Removed: {', '.join(removed)}")

    has_changes = False
    for sheet_name in sorted(common):
        old_df = pd.read_excel(old_file, sheet_name=sheet_name)
        new_df = pd.read_excel(new_file, sheet_name=sheet_name)

        if not old_df.equals(new_df):
            has_changes = True
            print(f"\n[{sheet_name}]")
            print(f"  Old: {len(old_df)} rows x {len(old_df.columns)} cols")
            print(f"  New: {len(new_df)} rows x {len(new_df.columns)} cols")

            if len(old_df) != len(new_df):
                diff = len(new_df) - len(old_df)
                print(f"  Rows: {diff:+d}")
            if len(old_df.columns) != len(new_df.columns):
                diff = len(new_df.columns) - len(old_df.columns)
                print(f"  Cols: {diff:+d}")

    if not added and not removed and not has_changes:
        print(f"\nNo changes detected - files are identical")

def main():
    if len(sys.argv) < 2:
        print("Usage: python fetch_yach_doc_final.py <doc_id> [output_name]")
        print("\nExample:")
        print("  python fetch_yach_doc_final.py 47kgJmVE1gS1BOqV resources")
        sys.exit(1)

    doc_id = sys.argv[1]
    output_name = sys.argv[2] if len(sys.argv) > 2 else "yach_export"

    print(f"{'='*60}")
    print(f"Yach Document Exporter")
    print(f"{'='*60}")

    # Get token
    token = get_access_token()

    # Export
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_path = Path("D:/codexProject") / f"{output_name}_{timestamp}.xlsx"
    final_path = Path("D:/codexProject") / f"{output_name}_latest.xlsx"

    export_doc(token, doc_id, temp_path)

    # Compare if previous version exists
    if final_path.exists():
        compare_files(temp_path, final_path)
        # Backup old version
        backup_path = final_path.with_suffix(f".{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        final_path.rename(backup_path)
        print(f"\nOld version backed up to: {backup_path.name}")

    # Move to final location
    temp_path.rename(final_path)

    # Save sheet info
    xl = pd.ExcelFile(final_path)
    sheet_info = {
        "path": str(final_path),
        "sheetnames": xl.sheet_names
    }
    info_path = final_path.with_suffix('.sheetnames.json')
    with open(info_path, 'w', encoding='utf-8') as f:
        json.dump(sheet_info, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"DONE!")
    print(f"{'='*60}")
    print(f"File: {final_path}")
    print(f"Sheets: {len(xl.sheet_names)}")
    for sheet in xl.sheet_names:
        print(f"  - {sheet}")

if __name__ == '__main__':
    main()
