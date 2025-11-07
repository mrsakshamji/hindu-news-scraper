import feedparser
import requests
from bs4 import BeautifulSoup
import json
import time
import os
from PIL import Image
from io import BytesIO
import base64

# 🔑 ImageKit credentials
IMAGEKIT_PUBLIC_KEY = os.environ.get("IMAGEKIT_PUBLIC_KEY")
IMAGEKIT_PRIVATE_KEY = os.environ.get("IMAGEKIT_PRIVATE_KEY")
IMAGEKIT_UPLOAD_URL = "https://upload.imagekit.io/api/v1/files/upload"

# 📰 RSS feed URL
rss_url = "https://www.thehindu.com/news/national/feeder/default.rss"
feed = feedparser.parse(rss_url)
print(f"🔄 Processing {len(feed.entries)} articles...\n")

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9"
}

output_file = "hindu-main-news.json"
articles = []

# ✅ Load existing articles
existing_links = set()
if os.path.exists(output_file):
    with open(output_file, "r", encoding="utf-8") as f:
        try:
            existing_articles = json.load(f)
            articles = existing_articles
            existing_links = {a["link"] for a in existing_articles}
        except:
            print("⚠️ Starting with a fresh file.")
            articles = []

# 🖼️ Image upload function
def upload_to_imagekit(image_url, filename, folder="/hindu-news"):
    if not IMAGEKIT_PRIVATE_KEY or not IMAGEKIT_PUBLIC_KEY:
        print("⚠️ ImageKit keys not found. Skipping image upload.")
        return image_url
    try:
        response = requests.get(image_url)
        response.raise_for_status()

        img = Image.open(BytesIO(response.content)).convert("RGB")
        buffer = BytesIO()
        img.save(buffer, format="WEBP", quality=80)
        encoded = base64.b64encode(buffer.getvalue()).decode()

        headers = {
            "Authorization": "Basic " + base64.b64encode(f"{IMAGEKIT_PRIVATE_KEY}:".encode()).decode()
        }

        payload = {
            "file": encoded,
            "fileName": filename + ".webp",
            "folder": folder,
            "useUniqueFileName": "true"
        }

        r = requests.post(IMAGEKIT_UPLOAD_URL, headers=headers, data=payload)
        r.raise_for_status()
        return r.json().get("url")
    except Exception as e:
        print(f"⚠️ Image upload failed: {e}")
        return image_url  # fallback

# 🔄 Process new articles
new_count = 0
for i, entry in enumerate(feed.entries):
    title = entry.title
    link = entry.link
    published = entry.published

    if link in existing_links:
        print(f"⏩ Skipped (already exists): {link}")
        continue

    print(f"🔗 [{i+1}] Fetching: {title[:60]}...")

    try:
        page = requests.get(link, headers=headers)
        soup = BeautifulSoup(page.content, "html.parser")

        content_div = (
            soup.find("div", id="schemaDiv") or
            soup.find("div", class_="articlebodycontent") or
            soup.find("div", {"itemprop": "articleBody"})
        )

        if not content_div:
            print("⚠️ Content not found")
            continue

        paragraphs = content_div.find_all("p")
        content = "\n".join(p.get_text(strip=True) for p in paragraphs)

        # Summary
        desc = soup.find("meta", attrs={"name": "description"})
        summary = desc.get("content", "") if desc else ""

        # Author
        author_tag = soup.find("span", class_="authorName") or soup.find("meta", attrs={"name": "author"})
        author = author_tag.get_text(strip=True) if author_tag and author_tag.name == "span" else (author_tag.get("content") if author_tag else "")

        # Image
        image_url = ""
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            image_url = og_image["content"]
            image_url = upload_to_imagekit(image_url, f"hindu_{hash(image_url)}")

        # Tags
        tags = [t.get_text(strip=True) for t in soup.find_all("a", class_="tag")]

        # Add to article list
        articles.append({
            "title": title,
            "link": link,
            "published": published,
            "author": author,
            "summary": summary,
            "tags": tags,
            "image": image_url,
            "content": content
        })

        existing_links.add(link)
        new_count += 1
        print(f"✅ Added: {title[:60]}...")
        time.sleep(1)  # Prevent IP blocking

    except Exception as e:
        print(f"❌ Error: {e}")
        continue

# 💾 Save JSON
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(articles, f, ensure_ascii=False, indent=2)

print(f"\n✅ Completed. {new_count} new articles added.")
print(f"📁 Total articles saved: {len(articles)}")
