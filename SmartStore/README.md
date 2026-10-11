# SmartStore — Smart File Organizer & Storage Optimizer

A beginner-friendly desktop file-management project built with Python and Streamlit.

## Features
- Scan a folder selected by path
- Detect exact duplicates using SHA-256 hashes
- Show storage totals, file-type breakdown, and largest files
- Move extra duplicate copies to `SmartStore_Recovery` instead of permanently deleting them
- Organize selected files into `SmartStore_Organized/Keep_Forever`, `Temporary`, or `Review_Later`
- Search the scanned inventory and export it as CSV

## Requirements
- Python 3.10 or later recommended
- Internet connection only for installing the Python packages
- Works locally on macOS, Windows, and Linux

## Setup (Mac)
1. Download and unzip the project.
2. Open Terminal and move into the `SmartStore` folder. For example:
   ```bash
   cd ~/Downloads/SmartStore
   ```
3. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
4. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
5. Start the app:
   ```bash
   python -m streamlit run app.py
   ```
6. The app opens in your browser, usually at `http://localhost:8501`.

## First test (important)
Create a small folder named `SmartStore_Demo`, copy a few non-important sample files into it, and duplicate one or two files. Scan this demo folder first. Confirm that duplicate detection works before using real files.

## How duplicate detection works
SmartStore first groups files by size, then calculates a SHA-256 hash for same-sized files. Files with the same hash are treated as exact duplicates. Visually similar photos that have different file contents are not identified in this basic version.

## Safety notes
- The app only scans the folder entered by the user.
- It skips symlinks and excludes its own output folders from scans.
- Duplicate copies are moved to `SmartStore_Recovery`; they are not permanently deleted.
- The organizer moves files to category folders. Test with sample files and maintain backups.
- Do not scan system folders or the entire disk for your first demo.

## Suggested evaluation demo
1. Show a test folder with 5–10 files and at least two duplicate copies.
2. Scan and explain the dashboard metrics.
3. Open Duplicate Finder and show identical files grouped together.
4. Move an extra copy to the recovery folder.
5. Select a sample document and move it into `Keep_Forever`.
6. Export the file inventory as CSV.

## Known limitations
- Exact duplicates only; no AI-based visual similarity in this version.
- File categories are represented by moving files into folders, not by predicting personal importance.
- The potential recovered space is an estimate and can differ if files change between scanning and cleanup.
