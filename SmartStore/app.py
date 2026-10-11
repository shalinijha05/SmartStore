from pathlib import Path
from collections import defaultdict
from datetime import datetime
import hashlib
import shutil

import pandas as pd
import streamlit as st

APP_NAME = "SmartStore"
CATEGORIES = ["Keep Forever", "Temporary", "Review Later"]
RECOVERY_DIRNAME = "SmartStore_Recovery"
ORGANIZED_DIRNAME = "SmartStore_Organized"
CHUNK_SIZE = 1024 * 1024

st.set_page_config(page_title="SmartStore", page_icon="🗂️", layout="wide")

st.markdown("""
<style>
    .block-container {padding-top: 1.7rem; padding-bottom: 2rem; max-width: 1400px;}
    .hero {padding: 1.35rem 1.5rem; border-radius: 18px;
           background: linear-gradient(120deg, #14213d, #235789); color: white; margin-bottom: 1rem;}
    .hero h1 {margin: 0; font-size: 2.25rem;}
    .hero p {margin: .4rem 0 0; opacity: .9;}
    div[data-testid="stMetric"] {border: 1px solid rgba(128,128,128,.2); padding: 14px; border-radius: 12px;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>🗂️ SmartStore</h1>
  <p>Understand your storage. Find duplicates. Keep important files organized.</p>
</div>
""", unsafe_allow_html=True)

st.warning("Safety first: SmartStore scans only the folder you choose. It does not permanently delete files. Test with a sample folder before using it on important data.")

def format_bytes(size):
    size = float(size or 0)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

def file_hash(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()

def scan_folder(root_path):
    root = Path(root_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError("That folder does not exist or is not a directory.")
    rows = []
    errors = 0
    for current, dirs, files in os.walk(root):
        # Avoid rescanning SmartStore's own output folders.
        dirs[:] = [d for d in dirs if d not in {RECOVERY_DIRNAME, ORGANIZED_DIRNAME, ".git", ".venv"}]
        for name in files:
            p = Path(current) / name
            try:
                if p.is_symlink() or not p.is_file():
                    continue
                stat = p.stat()
                rows.append({
                    "Name": p.name,
                    "Path": str(p),
                    "Extension": p.suffix.lower() or "(no extension)",
                    "Size (bytes)": stat.st_size,
                    "Modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    "Modified timestamp": stat.st_mtime,
                })
            except (OSError, PermissionError):
                errors += 1
    return rows, errors

def find_duplicates(rows):
    by_size = defaultdict(list)
    for row in rows:
        if row["Size (bytes)"] > 0:
            by_size[row["Size (bytes)"]].append(row)
    groups = []
    for same_size in by_size.values():
        if len(same_size) < 2:
            continue
        by_hash = defaultdict(list)
        for row in same_size:
            try:
                by_hash[file_hash(row["Path"])].append(row)
            except (OSError, PermissionError):
                continue
        for digest, matches in by_hash.items():
            if len(matches) > 1:
                groups.append({"hash": digest, "files": matches, "size": matches[0]["Size (bytes)"]})
    return groups

def safe_destination(folder, filename):
    dest = folder / filename
    if not dest.exists():
        return dest
    stem, suffix = Path(filename).stem, Path(filename).suffix
    counter = 1
    while True:
        candidate = folder / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1

def move_to_folder(source, target_folder):
    src = Path(source)
    target_folder.mkdir(parents=True, exist_ok=True)
    dest = safe_destination(target_folder, src.name)
    shutil.move(str(src), str(dest))
    return dest

with st.sidebar:
    st.header("Scan settings")
    default_path = str(Path.home() / "Downloads")
    folder_text = st.text_input("Folder path", value=default_path, help="Example on Mac: /Users/yourname/Downloads")
    st.caption("Tip: Start with a small test folder containing copies of a few files.")
    scan_clicked = st.button("🔎 Scan selected folder", type="primary", use_container_width=True)
    st.divider()
    st.markdown("**How it works**")
    st.caption("Exact duplicates are detected by comparing SHA-256 file hashes. Similar-looking photos are not considered duplicates unless their file contents match.")

if "scan_rows" not in st.session_state:
    st.session_state.scan_rows = []
if "scan_root" not in st.session_state:
    st.session_state.scan_root = ""
if "duplicate_groups" not in st.session_state:
    st.session_state.duplicate_groups = []
if "scan_errors" not in st.session_state:
    st.session_state.scan_errors = 0

if scan_clicked:
    try:
        with st.spinner("Scanning files and checking duplicates…"):
            rows, errors = scan_folder(folder_text)
            groups = find_duplicates(rows)
        st.session_state.scan_rows = rows
        st.session_state.scan_root = str(Path(folder_text).expanduser().resolve())
        st.session_state.duplicate_groups = groups
        st.session_state.scan_errors = errors
        st.success(f"Scan complete: {len(rows):,} files checked.")
    except Exception as exc:
        st.error(f"Could not scan that folder: {exc}")

rows = st.session_state.scan_rows
root = st.session_state.scan_root
groups = st.session_state.duplicate_groups

if not rows:
    st.info("Enter a folder path in the sidebar and select **Scan selected folder** to begin.")
    st.markdown("### Your first demo")
    st.markdown("1. Create a folder called `SmartStore_Demo`.\n2. Put a few sample documents or photos inside.\n3. Copy one or two files so there are exact duplicates.\n4. Scan that folder in SmartStore.")
    st.stop()

total_bytes = sum(r["Size (bytes)"] for r in rows)
duplicate_extra_bytes = sum((len(g["files"]) - 1) * g["size"] for g in groups)
largest = sorted(rows, key=lambda r: r["Size (bytes)"], reverse=True)[:10]

tab_overview, tab_duplicates, tab_organize, tab_files = st.tabs(
    ["📊 Overview", "🧬 Duplicate Finder", "🗃️ Organize Files", "📁 All Files"]
)

with tab_overview:
    st.subheader("Storage overview")
    st.caption(f"Scanned folder: `{root}`")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Files scanned", f"{len(rows):,}")
    c2.metric("Total file size", format_bytes(total_bytes))
    c3.metric("Duplicate groups", f"{len(groups):,}")
    c4.metric("Potential space to recover", format_bytes(duplicate_extra_bytes))
    if st.session_state.scan_errors:
        st.caption(f"{st.session_state.scan_errors} item(s) could not be read due to permissions or file-system errors.")
    st.markdown("#### File types by storage used")
    df = pd.DataFrame(rows)
    type_summary = df.groupby("Extension", as_index=False)["Size (bytes)"].sum().sort_values("Size (bytes)", ascending=False)
    type_summary["Storage used"] = type_summary["Size (bytes)"].map(format_bytes)
    st.bar_chart(type_summary.set_index("Extension")["Size (bytes)"])
    st.dataframe(type_summary[["Extension", "Storage used"]], use_container_width=True, hide_index=True)
    st.markdown("#### 10 largest files")
    large_df = pd.DataFrame(largest)[["Name", "Size (bytes)", "Modified", "Path"]].copy()
    large_df["Size"] = large_df["Size (bytes)"].map(format_bytes)
    st.dataframe(large_df[["Name", "Size", "Modified", "Path"]], use_container_width=True, hide_index=True)

with tab_duplicates:
    st.subheader("Exact duplicate files")
    st.write("Each group contains files with identical contents. Keep one copy and move the other copies to the recovery folder.")
    if not groups:
        st.success("No exact duplicates found in this scan.")
    else:
        st.metric("Potential duplicate space", format_bytes(duplicate_extra_bytes))
        for i, group in enumerate(groups, start=1):
            with st.expander(f"Group {i} · {len(group['files'])} copies · {format_bytes(group['size'])} each", expanded=(i == 1)):
                ddf = pd.DataFrame([{
                    "File name": item["Name"],
                    "Size": format_bytes(item["Size (bytes)"]),
                    "Full path": item["Path"],
                } for item in group["files"]])
                st.dataframe(ddf, use_container_width=True, hide_index=True)
                keep_path = st.selectbox(
                    "Choose the copy to keep",
                    options=[item["Path"] for item in group["files"]],
                    format_func=lambda p: str(Path(p).name) + " — " + str(Path(p).parent),
                    key=f"keep_{group['hash']}",
                )
                move_paths = [item["Path"] for item in group["files"] if item["Path"] != keep_path]
                if st.button(f"Move {len(move_paths)} extra copy/copies to recovery", key=f"recover_{group['hash']}"):
                    recovery = Path(root) / RECOVERY_DIRNAME
                    moved, failed = 0, []
                    for source in move_paths:
                        try:
                            move_to_folder(source, recovery)
                            moved += 1
                        except Exception as exc:
                            failed.append(f"{source}: {exc}")
                    if moved:
                        st.success(f"Moved {moved} file(s) to {recovery}. They were not permanently deleted.")
                    if failed:
                        st.error("Some files could not be moved: " + "; ".join(failed))
                    st.info("Rescan the folder to refresh the dashboard.")
    st.caption(f"Recovery folder: `{Path(root) / RECOVERY_DIRNAME}`")

with tab_organize:
    st.subheader("Organize selected files")
    st.write("Select files and move them into a dedicated category folder inside your scanned folder.")
    st.caption("This moves files from their original locations. For your first test, use sample files you can safely move.")
    file_options = [r["Path"] for r in rows]
    selected = st.multiselect(
        "Choose files to organize",
        options=file_options,
        format_func=lambda p: f"{Path(p).name}  ·  {Path(p).parent}",
        help="You can select more than one file.",
    )
    category = st.radio("Choose a category", CATEGORIES, horizontal=True)
    st.caption(f"Destination: `{Path(root) / ORGANIZED_DIRNAME / category.replace(' ', '_')}`")
    if st.button("Move selected files into category", type="primary", disabled=not selected):
        destination = Path(root) / ORGANIZED_DIRNAME / category.replace(" ", "_")
        moved, failed = 0, []
        for source in selected:
            try:
                # Prevent moving files into the organizer's own output area again.
                if Path(source).resolve().is_relative_to((Path(root) / ORGANIZED_DIRNAME).resolve()):
                    failed.append(f"{source}: already inside SmartStore_Organized")
                    continue
                move_to_folder(source, destination)
                moved += 1
            except Exception as exc:
                failed.append(f"{source}: {exc}")
        if moved:
            st.success(f"Moved {moved} file(s) to {destination}.")
        if failed:
            st.error("Some files could not be moved: " + "; ".join(failed))
        st.info("Rescan the folder to refresh the file list.")

with tab_files:
    st.subheader("All scanned files")
    filter_text = st.text_input("Search by file name or path")
    file_df = pd.DataFrame(rows)
    if filter_text:
        mask = file_df["Name"].str.contains(filter_text, case=False, na=False) | file_df["Path"].str.contains(filter_text, case=False, na=False)
        file_df = file_df[mask]
    file_df["Size"] = file_df["Size (bytes)"].map(format_bytes)
    st.dataframe(file_df[["Name", "Extension", "Size", "Modified", "Path"]], use_container_width=True, hide_index=True)
    csv = file_df[["Name", "Extension", "Size", "Modified", "Path"]].to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Export file inventory as CSV", data=csv, file_name="smartstore_file_inventory.csv", mime="text/csv")

st.divider()
st.caption("SmartStore project prototype · Files are only moved after you press an action button. Always keep a separate backup of important files.")
