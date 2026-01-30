import os
import sqlite3
import shutil
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "backend" / "instance" / "binbin.db"
BACKEND_STATIC = Path(__file__).resolve().parents[1] / "backend" / "static"
OUT_DIR = Path(__file__).resolve().parent / "dataset_binary"

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "recyclable").mkdir(exist_ok=True)
    (OUT_DIR / "non_recyclable").mkdir(exist_ok=True)

    con = sqlite3.connect(str(DB_PATH))
    cur = con.cursor()

    cur.execute("""
        SELECT id, image_path, human_label
        FROM events
        WHERE event_type = 'deposit'
          AND image_path IS NOT NULL
          AND human_label IN ('recyclable', 'non_recyclable')
    """)

    rows = cur.fetchall()
    print(f"Exporting {len(rows)} labeled deposit images...")

    for event_id, image_path, human_label in rows:
        src = BACKEND_STATIC / image_path
        if not src.exists():
            print(f"Missing file for event {event_id}: {src}")
            continue

        ext = src.suffix.lower() if src.suffix else ".jpg"
        dst = OUT_DIR / human_label / f"event_{event_id}{ext}"
        shutil.copy2(src, dst)

    con.close()
    print("Done:", OUT_DIR)

if __name__ == "__main__":
    main()