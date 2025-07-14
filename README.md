# 📰 Hindu News Scraper

This repository contains a simple automated news scraper that extracts top headlines from the Hindustan Times website and saves them in a structured JSON format (`hindu-main-news.json`). It is powered by a Python script and runs every 15 minutes using GitHub Actions.

## 🌐 Live JSON Feed

You can access the live JSON output at:

```
https://mrsakshamji.github.io/hindu-news-scraper/hindu-main-news.json
```

---

## 📁 Output Format

Each news item in the JSON file contains:

```json
[
  {
    "title": "News headline",
    "link": "https://example.com/news-link",
    "published": "Mon, 14 Jul 2025 23:12:32 +0530",
    "author": ""
  },
  ...
]
```

---

## 🛠️ Technologies Used

- **Python 3.11+**
- **Requests + BeautifulSoup** for scraping
- **GitHub Actions** for automation (runs every 15 minutes)
- **GitHub Pages** for serving JSON publicly

---

## ⚙️ How It Works

1. The Python script (`main.py`) scrapes latest headlines.
2. The scraped data is saved in `hindu-main-news.json`.
3. A GitHub Actions workflow automatically runs the script every 15 minutes.
4. Changes are committed and pushed back to the repository.
5. GitHub Pages serves the updated JSON file publicly.

---

## 📦 Setup Locally

### Requirements

- Python 3.11 or higher
- `pip install -r requirements.txt`

### Run Locally

```bash
python main.py
```

The JSON file will be saved as `hindu-main-news.json`.

---

## 🤖 GitHub Actions Setup

See `.github/workflows/scrape.yml`:

- Runs every 15 minutes via cron.
- Commits only if content changes.
- Pushes updated JSON to main branch.
- GitHub Pages hosts the latest file.

---

## 🔐 API Integration

You can use this JSON feed with protected APIs:

```bash
GET https://your-api.vercel.app/api/news
Headers: x-api-key: YOUR_SECRET_KEY
```

---

## 📄 License

MIT License – free for personal and commercial use.

---

## 🙋‍♂️ Author

Built with ❤️ by [@mrsakshamji](https://github.com/mrsakshamji)
