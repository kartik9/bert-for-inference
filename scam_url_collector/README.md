# Scam URL Collector

A comprehensive multi-source scraper that collects potentially malicious URLs from various platforms including Reddit, Twitter/X, BBB Scam Tracker, and FTC alerts. The system prioritizes URLs based on multiple factors for efficient investigation.

## Features

- **Multi-Source Collection**: Scrapes from Reddit, Twitter, BBB, and FTC
- **Intelligent Prioritization**: Scores URLs based on source credibility, engagement, recency, and cross-references
- **Deduplication**: Automatically identifies the same URL mentioned across different sources
- **URL Normalization**: Cleans, expands shortened URLs, and removes tracking parameters
- **SQLite Database**: Efficient storage with indexing for fast queries
- **Scheduled Collection**: Run continuously on a schedule or one-time
- **Export to JSON**: Export high-priority URLs for investigation

## Architecture

```
scam_url_collector/
├── scrapers/
│   ├── base_scraper.py       # Base class for all scrapers
│   ├── reddit_scraper.py     # Reddit scraper using PRAW
│   ├── twitter_scraper.py    # Twitter scraper (snscrape/tweepy)
│   ├── bbb_scraper.py        # BBB Scam Tracker scraper
│   └── ftc_scraper.py        # FTC alerts scraper
├── utils/
│   ├── url_extractor.py      # URL extraction and validation
│   ├── database.py           # SQLite database management
│   └── config.py             # Configuration management
├── data/
│   ├── scam_urls.db          # SQLite database (created automatically)
│   └── collector.log         # Log file
├── requirements.txt
├── .env.example
├── main.py                   # Main orchestrator
└── README.md
```

## Installation

### 1. Clone the Repository

```bash
cd scam_url_collector
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Browser for BBB Scraping

BBB scraping requires Playwright:

```bash
playwright install chromium
```

### 5. Configure Environment Variables

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` and add your Reddit API credentials (required).

## Getting API Credentials

### Reddit API (Required)

1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Select "script" as the app type
4. Fill in the details:
   - **name**: ScamURLCollector (or any name)
   - **redirect uri**: http://localhost:8080
5. Click "Create app"
6. Copy the **client ID** (under the app name) and **client secret**
7. Add them to your `.env` file:

```
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
```

### Twitter API (Optional)

Twitter API has strict rate limits and requires approval. **Recommended**: Use snscrape instead (no API needed).

If you want to use the Twitter API:
1. Apply for a developer account at https://developer.twitter.com
2. Create a new app and generate API keys
3. Add credentials to `.env`

**Note**: By default, the scraper uses `snscrape` which doesn't require API credentials.

## Usage

### Validate Configuration

Before running, validate your configuration:

```bash
python -m scam_url_collector.main --validate-config
```

### Run Once

Collect URLs once and exit:

```bash
python -m scam_url_collector.main --once
```

### Run Once with Export

Collect URLs and export to JSON:

```bash
python -m scam_url_collector.main --once --export
```

### Run on Schedule

Run continuously, collecting every 6 hours (configurable):

```bash
python -m scam_url_collector.main
```

### Run with Custom Interval

Collect every 3 hours:

```bash
python -m scam_url_collector.main --interval 3
```

### Skip BBB Scraping

If you don't want to use browser automation:

```bash
python -m scam_url_collector.main --once --skip-bbb
```

### Use Twitter API

If you have Twitter API credentials:

```bash
python -m scam_url_collector.main --once --twitter-api
```

### Print Statistics

View database statistics:

```bash
python -m scam_url_collector.main --stats
```

### Custom Export Path

Export to a custom file:

```bash
python -m scam_url_collector.main --once --export --output my_urls.json
```

## Command-Line Options

| Option | Description |
|--------|-------------|
| `--once` | Run collection once and exit (default: run on schedule) |
| `--export` | Export URLs for investigation after collection |
| `--stats` | Print database statistics and exit |
| `--twitter-api` | Use Twitter API instead of snscrape |
| `--skip-bbb` | Skip BBB scraping (avoids browser automation) |
| `--interval N` | Hours between collection cycles (default: 6) |
| `--output FILE` | Output file for export (default: data/urls_to_investigate.json) |
| `--validate-config` | Validate configuration and exit |

## Configuration

All configuration is done via environment variables in the `.env` file or directly in `utils/config.py`.

### Key Configuration Options

**Scraping Settings:**
- `REDDIT_POST_LIMIT`: Max posts per subreddit (default: 100)
- `REDDIT_DAYS_BACK`: How many days back to scrape (default: 7)
- `TWITTER_TWEET_LIMIT`: Max tweets per query (default: 100)
- `BBB_PAGES_TO_SCRAPE`: BBB pages to scrape (default: 10)
- `FTC_DAYS_BACK`: Days back for FTC articles (default: 30)

**Rate Limiting:**
- `REQUESTS_PER_MINUTE`: Max requests per minute (default: 30)
- `SLEEP_BETWEEN_REQUESTS`: Delay between requests in seconds (default: 2.0)

**Scheduling:**
- `COLLECTION_INTERVAL_HOURS`: Hours between collection cycles (default: 6)

**Export:**
- `EXPORT_LIMIT`: Max URLs to export (default: 500)
- `EXPORT_PATH`: Output JSON file path

## Database Schema

The SQLite database stores URLs with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `id` | INTEGER | Primary key |
| `url` | TEXT | Original URL |
| `url_normalized` | TEXT | Normalized URL for deduplication |
| `source` | TEXT | Source platform (reddit, twitter, bbb, ftc) |
| `source_id` | TEXT | ID from source (post_id, tweet_id, etc.) |
| `source_url` | TEXT | Link back to source |
| `context` | TEXT | Surrounding text (truncated to 500 chars) |
| `scam_type` | TEXT | Classified scam type |
| `date_found` | TIMESTAMP | When added to database |
| `date_posted` | TIMESTAMP | When originally posted |
| `metadata` | JSON | Source-specific metadata |
| `priority_score` | REAL | Calculated priority score |
| `validated` | BOOLEAN | Whether confirmed as scam |
| `investigation_status` | TEXT | Status (pending, completed) |

## Priority Scoring

URLs are scored based on:

- **Multiple Sources**: +10 points per additional independent source
- **Recency**: +10 if < 7 days old, +5 if < 30 days, -5 if > 90 days
- **Engagement**: Up to +10 based on upvotes/retweets/likes
- **Scam Type Severity**: +15 for financial/identity theft, +10 for phishing/malware
- **Source Credibility**: +5 for BBB and FTC (vetted sources)

## Output Format

The exported JSON file contains:

```json
{
  "collection_date": "2025-12-05T10:30:00Z",
  "total_urls": 342,
  "urls": [
    {
      "url": "https://suspicious-site.com",
      "priority_score": 45.0,
      "sources": ["reddit", "twitter"],
      "first_seen": "2025-12-04T15:22:00Z",
      "scam_type": "phishing",
      "context": "Someone posted asking if this is legit...",
      "metadata": {
        "reddit_posts": 3,
        "twitter_mentions": 2,
        "avg_engagement": 156
      }
    }
  ]
}
```

## Targeted Subreddits

- r/Scams
- r/scambait
- r/phishing
- r/cybersecurity
- r/antiMLM
- r/personalfinance
- r/scambusters
- r/netsec
- r/privacy

## Search Keywords

The scrapers look for posts/tweets containing:
- "is this legit"
- "suspicious link"
- "got this url"
- "phishing site"
- "scam website"
- "fake website"
- "is this a scam"
- "sketchy website"
- "fraudulent site"
- "malicious link"

## Troubleshooting

### snscrape Installation Issues

If `snscrape` installation fails:

```bash
pip install git+https://github.com/JustAnotherArchivist/snscrape.git
```

### Playwright Browser Installation

If BBB scraping fails:

```bash
playwright install chromium
# Or use Firefox/WebKit
playwright install firefox
```

Set `BROWSER_TYPE=firefox` in `.env` if needed.

### Rate Limiting

If you encounter rate limiting:
- Increase `SLEEP_BETWEEN_REQUESTS` in `.env`
- Decrease `REDDIT_POST_LIMIT` and `TWITTER_TWEET_LIMIT`
- Reduce `COLLECTION_INTERVAL_HOURS` (run less frequently)

### Database Locked Errors

If you see "database is locked" errors:
- Ensure only one instance is running
- Check file permissions on `data/scam_urls.db`

## Logging

Logs are written to:
- `scam_url_collector/data/collector.log` (file)
- Console output (stdout)

Log level can be adjusted in `main.py` (default: INFO).

## Example Workflow

1. **Initial Setup**:
   ```bash
   cp .env.example .env
   # Edit .env with Reddit credentials
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Validate Configuration**:
   ```bash
   python -m scam_url_collector.main --validate-config
   ```

3. **Test Run**:
   ```bash
   python -m scam_url_collector.main --once --skip-bbb
   ```

4. **Full Collection with Export**:
   ```bash
   python -m scam_url_collector.main --once --export
   ```

5. **Review Results**:
   ```bash
   python -m scam_url_collector.main --stats
   # Check data/urls_to_investigate.json
   ```

6. **Run Continuously**:
   ```bash
   nohup python -m scam_url_collector.main --export &
   ```

## Integration with Aurora

The exported JSON file is designed to be ingested by analysis tools like Aurora for further investigation:

1. Run collector with `--export`
2. Feed `data/urls_to_investigate.json` to your URL analysis pipeline
3. High-priority URLs (top scores) should be investigated first

## Performance Considerations

- **Reddit**: Fast, well-documented API
- **Twitter (snscrape)**: Slower, may break if Twitter changes HTML
- **Twitter (API)**: Fast but strict rate limits
- **BBB**: Slower (browser automation), can be skipped with `--skip-bbb`
- **FTC**: Fast, but fewer URLs typically found

**Recommended for quick testing**: `--skip-bbb`

**Recommended for production**: Run all sources on a schedule

## Contributing

To add a new source:

1. Create a new scraper in `scrapers/` inheriting from `BaseScraper`
2. Implement the `scrape()` method
3. Add configuration to `utils/config.py`
4. Integrate in `main.py`

## License

MIT License - See LICENSE file for details

## Disclaimer

This tool is for security research and threat intelligence purposes only. Always respect the terms of service of the platforms you're scraping and applicable laws. Do not use collected URLs for malicious purposes.
