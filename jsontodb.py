import json
import time
import datetime
import pymysql
import os  # <-- Import os
from pymysql.constants import CLIENT

# ===== FILE & CONFIG =====
FILE_PATH = "hindu-main-news.json"    # Path to your JSON file
BATCH_SIZE = 200      # Number of records per batch

# ===== Aiven MySQL Credentials (from environment variables) =====
DB_HOST = os.environ.get("AIVEN_DB_HOST")
DB_USER = os.environ.get("AIVEN_DB_USER")
DB_PASS = os.environ.get("AIVEN_DB_PASS")
DB_NAME = os.environ.get("AIVEN_DB_NAME")
DB_PORT = 16166

# ===== SSL Certificate =====
SSL_CA = "ca.pem"  # This file will be created by the GitHub Action

# ===== Check for missing credentials =====
if not all([DB_HOST, DB_USER, DB_PASS, DB_NAME]):
    raise ValueError("❌ CRITICAL: Missing one or more AIVEN environment variables (AIVEN_DB_HOST, AIVEN_DB_USER, AIVEN_DB_PASS, AIVEN_DB_NAME). Please set them in GitHub Secrets.")

# ========== CONNECT ==========
print("🔌 Connecting to MySQL (Aiven)...")

conn = pymysql.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASS,
    database=DB_NAME,
    port=DB_PORT,
    ssl={"ca": SSL_CA},
    charset="utf8mb4",
    autocommit=False,
    client_flag=CLIENT.MULTI_STATEMENTS
)

cursor = conn.cursor()
print("✅ Connected securely via SSL!\n")

# ========== READ JSON ==========
print(f"🔄 Loading {FILE_PATH} ...")
try:
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        articles = json.load(f)
except FileNotFoundError:
    print(f"❌ ERROR: {FILE_PATH} not found. Did main.py run successfully?")
    exit(1)
except json.JSONDecodeError:
    print(f"❌ ERROR: Could not decode {FILE_PATH}. The file might be empty or corrupt.")
    exit(1)


if not isinstance(articles, list):
    raise ValueError("❌ JSON root must be an array of articles!")

total = len(articles)
if total == 0:
    print("🟡 No articles found in JSON. Exiting.")
    cursor.close()
    conn.close()
    exit(0)
    
print(f"✅ Loaded {total} articles\n")

# ========== CREATE TABLE IF NOT EXISTS ==========
print("🧱 Ensuring table structure is correct...")

cursor.execute("""
CREATE TABLE IF NOT EXISTS news_articles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(500),
    link VARCHAR(1000),
    published DATETIME NULL,
    author VARCHAR(255),
    summary TEXT,
    tags JSON,
    image TEXT,
    content LONGTEXT,
    raw_json JSON
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
""")
conn.commit()

# Check if 'link' column is TEXT, then alter it to VARCHAR(1000)
cursor.execute("SHOW COLUMNS FROM news_articles LIKE 'link'")
link_col = cursor.fetchone()

if link_col and "text" in link_col[1].lower():
    print("⚙️ Fixing column type for 'link' (TEXT → VARCHAR(1000))...")
    cursor.execute("ALTER TABLE news_articles MODIFY COLUMN link VARCHAR(1000)")
    conn.commit()
    print("✅ Column 'link' updated successfully!\n")

# Ensure unique index exists (first 255 chars only)
cursor.execute("""
SHOW INDEX FROM news_articles WHERE Key_name = 'unique_link';
""")
if cursor.rowcount == 0:
    print("🔑 Adding unique index on 'link' (first 255 chars)...")
    cursor.execute("ALTER TABLE news_articles ADD UNIQUE KEY unique_link (link(255))")
    conn.commit()
    print("✅ Unique index added!\n")
else:
    print("🔑 Unique index already exists.\n")

# ========== PREPARE SQL ==========
sql = """
INSERT IGNORE INTO news_articles 
(title, link, published, author, summary, tags, image, content, raw_json)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

# ========== IMPORT LOOP ==========
start_time = time.time()
inserted = 0
skipped = 0
record_num = 0

for batch_start in range(0, total, BATCH_SIZE):
    batch = articles[batch_start: batch_start + BATCH_SIZE]
    values = []

    for data in batch:
        record_num += 1
        title = data.get("title", "")
        link = data.get("link", "")

        # Skip empty or invalid links
        if not link:
            print(f"⚠️ Skipping record #{record_num} (no link)")
            continue

        # Handle published date
        published_dt = None
        if data.get("published"):
            try:
                # Parse "Wed, 06 Nov 2025 20:30:00 +0530" format
                # Split at '+' or '-' to remove timezone info, which strptime can struggle with
                date_str = data["published"].split("+")[0].split("-")[0].strip()
                published_dt = datetime.datetime.strptime(
                    date_str,
                    "%a, %d %b %Y %H:%M:%S"
                )
            except Exception as e:
                # print(f"Debug: Failed to parse date '{data.get('published')}'. Error: {e}")
                published_dt = None # Fail silently

        author = data.get("author", "")
        summary = data.get("summary", "")
        tags = json.dumps(data.get("tags", []), ensure_ascii=False)
        image = data.get("image", "")
        content = data.get("content", "")
        raw_json = json.dumps(data, ensure_ascii=False)

        values.append((title, link, published_dt, author, summary, tags, image, content, raw_json))

    if not values:
        continue # Skip if batch was empty (e.g., all invalid links)

    try:
        cursor.executemany(sql, values)
        conn.commit()

        affected = cursor.rowcount
        batch_skipped = len(values) - affected
        inserted += affected
        skipped += batch_skipped

        percent = round((inserted + skipped) / total * 100, 2)
        elapsed = time.time() - start_time
        rate = (inserted + skipped) / elapsed if elapsed > 0 else 0
        eta = (total - (inserted + skipped)) / rate if rate > 0 else 0

        print(f"🟩 Batch done: Inserted {affected}, Skipped {batch_skipped}")
        print(f"    → Total: {inserted} inserted / {skipped} skipped / {total} total ({percent}%)")
        print(f"    → {rate:.1f}/sec — ETA {eta:.0f}s\n")
        
    except Exception as e:
        print(f"❌ ERROR during batch insert: {e}")
        conn.rollback() # Rollback this failed batch


# ========== COMPLETE ==========
end_time = time.time()
print(f"\n✅ Import completed successfully!")
print(f"📦 Inserted: {inserted}")
print(f"🚫 Skipped (already existed): {skipped}")
print(f"⏱️ Time taken: {round(end_time - start_time, 2)} seconds")

cursor.close()
conn.close()
print("🔒 Connection closed securely.")
