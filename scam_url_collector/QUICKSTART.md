# Quick Start Guide

Get the scam URL collector running in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- Reddit account (for API access)

## Step 1: Install Dependencies

```bash
cd scam_url_collector
pip install -r requirements.txt
```

## Step 2: Install Browser (for BBB scraping)

```bash
playwright install chromium
```

If you want to skip BBB scraping for now, you can use the `--skip-bbb` flag later.

## Step 3: Get Reddit API Credentials

1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" → Select "script"
3. Fill in:
   - **name**: ScamURLCollector
   - **redirect uri**: http://localhost:8080
4. Copy the **client_id** (under app name) and **secret**

## Step 4: Configure Environment

```bash
cp .env.example .env
nano .env  # or use your favorite editor
```

Add your Reddit credentials:

```
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_secret_here
```

Save and exit.

## Step 5: Run Your First Collection

### Option A: Simple test run (skip BBB)

```bash
python -m main --once --skip-bbb
```

This will:
- Scrape Reddit, Twitter (via snscrape), and FTC
- Save URLs to the database
- Show statistics

### Option B: Full run with export

```bash
python -m main --once --export
```

This will:
- Scrape all sources (including BBB)
- Export high-priority URLs to `data/urls_to_investigate.json`

## Step 6: View Results

### Check statistics

```bash
python -m main --stats
```

### View the database

```bash
sqlite3 data/scam_urls.db "SELECT url, source, priority_score FROM scam_urls ORDER BY priority_score DESC LIMIT 10;"
```

### View exported JSON

```bash
cat data/urls_to_investigate.json | python -m json.tool | head -50
```

## Step 7: Run Continuously (Optional)

To run the collector every 6 hours:

```bash
# In a screen or tmux session:
python -m main --export
```

Or use a process manager like `systemd` or `supervisor`.

## Troubleshooting

### "Reddit API credentials are required"

Make sure you've set `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` in your `.env` file.

### "snscrape not available"

Install with:
```bash
pip install git+https://github.com/JustAnotherArchivist/snscrape.git
```

### "Playwright not installed"

Run:
```bash
playwright install chromium
```

Or skip BBB scraping with `--skip-bbb`.

## What's Next?

- **Customize sources**: Edit `utils/config.py` to change subreddits, keywords, etc.
- **Adjust scheduling**: Use `--interval N` to change collection frequency
- **Integrate with analysis tools**: Feed `urls_to_investigate.json` to your URL analysis pipeline
- **Add more sources**: Create new scrapers following the pattern in `scrapers/base_scraper.py`

## Example Commands

```bash
# Collect once, export, skip BBB
python -m main --once --export --skip-bbb

# Run every 3 hours with custom export path
python -m main --interval 3 --export --output my_urls.json

# Use Twitter API instead of snscrape
python -m main --once --twitter-api --export

# Just print stats (no collection)
python -m main --stats
```

## Next Steps

1. Review the full README.md for detailed documentation
2. Customize configuration in `utils/config.py`
3. Set up automated scheduling (cron, systemd, etc.)
4. Integrate the JSON output with your analysis pipeline

Happy hunting! 🕵️
