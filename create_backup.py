"""
Create a portable, standalone ZIP backup of The National Mineral Intelligence Hub
Excludes git histories and pycache.
"""

import os
import zipfile
from datetime import datetime

base_dir = os.path.dirname(os.path.abspath(__file__))
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
zip_filename = f"National_Mineral_Intelligence_Hub_Zimbabwe_2026_Backup.zip"
zip_filepath = os.path.join(base_dir, zip_filename)

EXCLUDE_DIRS = {'.git', '__pycache__', '.gemini', 'node_modules', '.vscode'}
EXCLUDE_EXTS = {'.pyc', '.pyo', '.tmp', '.log'}

print(f"Creating project backup archive: {zip_filename}...")

file_count = 0
with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(base_dir):
        # Exclude specified directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in EXCLUDE_EXTS or file == zip_filename:
                continue
                
            abs_path = os.path.join(root, file)
            rel_path = os.path.relpath(abs_path, base_dir)
            zipf.write(abs_path, rel_path)
            file_count += 1

size_mb = os.path.getsize(zip_filepath) / (1024 * 1024)
print(f"[+] Backup complete: {file_count} files packaged.")
print(f"[+] Archive location: {zip_filepath}")
print(f"[+] Archive size: {size_mb:.2f} MB")
