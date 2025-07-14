import feedparser
import requests
from bs4 import BeautifulSoup
import json
import time
import os

# RSS feed URL
rss_url = "https://www.thehindu.com/news/national/feeder/default.rss"

# Parse the RSS feed
feed = feedparser.parse(rss_url)

print("🔄 Processing articles...\n")
print(f"📥 Total entries in RSS feed: {len(feed.entries)}\n")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com"
}

output_file = "hindu-main-news.json"
articles = []

# ✅ Load existing articles if file exists
existing_links = set()
if os.path.exists(output_file):
    with open(output_file, "r", encoding="utf-8") as f:
        try:
            existing_articles = json.load(f)
            articles = existing_articles
            existing_links = {a["link"] for a in existing_articles}
        except json.JSONDecodeError:
            print("⚠️ Invalid or empty existing file. Starting fresh.")
            articles = []

new_count = 0

# Process feed entries
for index, entry in enumerate(feed.entries):
    title = entry.title
    link = entry.link
    published = entry.published

    if link in existing_links:
        print(f"⏩ Skipping (Already Exists): {link}")
        continue

    print(f"🔗 [{index + 1}] Fetching: {link}")

    try:
        response = requests.get(link, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # ✅ Updated content block selector
        content_block = (
            soup.find("div", class_="schemaDiv", id="schemaDiv") or
            soup.find("div", class_="articlebodycontent") or
            soup.find("div", {"itemprop": "articleBody"})
        )

        if not content_block:
            print(f"⚠️ No content block found. Saving HTML for debugging: debug_{index + 1}.html")
            with open(f"debug_{index + 1}.html", "w", encoding="utf-8") as debug_file:
                debug_file.write(soup.prettify())
            continue

        # Extract article paragraphs
        paragraphs = content_block.find_all("p")
        if not paragraphs:
            print(f"⚠️ No paragraphs inside content block: {link}")
            continue
        content = "\n".join(p.get_text(strip=True) for p in paragraphs)

        # Featured image
        image_url = ""
        image_tag = soup.find("meta", property="og:image")
        if image_tag and image_tag.get("content"):
            image_url = image_tag["content"]

        # Author
        author = ""
        author_tag = soup.find("span", class_="authorName") or soup.find("meta", attrs={"name": "author"})
        if author_tag:
            author = author_tag.get_text(strip=True) if author_tag.name == "span" else author_tag.get("content", "")

        # Summary
        summary = ""
        desc_tag = soup.find("meta", attrs={"name": "description"})
        if desc_tag and desc_tag.get("content"):
            summary = desc_tag["content"]

        # Tags
        tags = []
        tag_elements = soup.find_all("a", class_="tag")
        if tag_elements:
            tags = [t.get_text(strip=True) for t in tag_elements]

        # Save final article
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

        time.sleep(1)  # Prevent IP block

    except Exception as e:
        print(f"❌ Error fetching {link}: {e}")
        continue

# Save final JSON
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(articles, f, ensure_ascii=False, indent=2)

print(f"\n✅ Done. Added {new_count} new articles.")
print(f"🗂️ Total articles saved: {len(articles)}")

# Preview
print("\n=== Final JSON Preview (First 3 Articles) ===\n")
print(json.dumps(articles[:3], indent=2, ensure_ascii=False))
