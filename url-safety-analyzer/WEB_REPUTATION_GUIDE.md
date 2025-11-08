# Web Reputation Search Integration Guide

## Overview

The URL Safety Analyzer now includes **Web Reputation Search** capabilities that search the internet for:
- Scam reports and fraud complaints
- User reviews and experiences
- Reputation on trusted sites (Reddit, Trustpilot, BBB, etc.)
- News mentions and warnings
- Victim reports and financial loss claims

This adds a crucial real-world intelligence layer to the technical analysis.

## How It Works

### Search Strategy

The system executes multiple targeted search queries for each URL:

**Scam Detection Queries:**
- `"domain.com" scam`
- `"domain.com" fraud`
- `"domain.com" phishing`
- `"domain.com" fake`
- `"domain.com" malware`

**Complaint Queries:**
- `"domain.com" complaint`
- `"domain.com" review`
- `"domain.com" trustworthy`
- `"domain.com" legitimate`

**Victim Report Queries:**
- `"domain.com" "did not receive"`
- `"domain.com" "lost money"`
- `"domain.com" "credit card"`

**Reputation Site Queries:**
- `site:reddit.com "domain.com"`
- `site:trustpilot.com "domain.com"`
- `site:bbb.org "domain.com"`
- `site:sitejabber.com "domain.com"`

### Analysis Process

1. **Query Execution**: All queries run in parallel
2. **Result Parsing**: Extracts titles, snippets, and URLs
3. **Keyword Detection**: Identifies scam/fraud/victim keywords
4. **Severity Assessment**: Classifies findings as high/medium severity
5. **Reputation Scoring**: Calculates 0-100 score (higher = better)
6. **Risk Level**: Assigns LOW/MEDIUM/HIGH/CRITICAL risk

## Supported Search Backends

### Option 1: Brave Search API (Recommended)

**Why Brave:**
- Free tier: 2,000 queries/month
- No credit card required for free tier
- Fast and reliable
- Good result quality
- Privacy-focused

**Setup:**
1. Go to https://api.search.brave.com/
2. Sign up for free account
3. Get your API key
4. Add to `.env`: `BRAVE_SEARCH_API_KEY=your_key_here`

**Pricing:**
- Free: 2,000 queries/month
- Paid: $5/month for 15,000 queries

### Option 2: SerpAPI

**Why SerpAPI:**
- Access to Google search results
- Structured data
- Good result quality
- Reliable service

**Setup:**
1. Go to https://serpapi.com/
2. Sign up (free tier: 100 queries/month)
3. Get your API key
4. Add to `.env`: `SERPAPI_KEY=your_key_here`

**Pricing:**
- Free: 100 queries/month
- Starter: $50/month for 5,000 queries
- Developer: $100/month for 15,000 queries

### Option 3: Google Custom Search API

**Why Google CSE:**
- Direct Google results
- Official Google API
- Good for specific use cases

**Setup:**
1. Go to https://developers.google.com/custom-search/v1/overview
2. Enable Custom Search API
3. Create search engine at https://programmablesearchengine.google.com/
4. Get API key and Search Engine ID
5. Add to `.env`:
   ```
   GOOGLE_CSE_API_KEY=your_api_key
   GOOGLE_CSE_ID=your_search_engine_id
   ```

**Pricing:**
- Free: 100 queries/day
- Paid: $5 per 1,000 queries (up to 10,000/day)

### Option 4: DuckDuckGo (Fallback)

**Why DDG:**
- No API key required
- Works as fallback
- Privacy-focused

**Limitations:**
- Less reliable (HTML scraping)
- May be rate-limited
- Lower result quality
- No official API

**Setup:**
- No setup required
- Automatically used if no API key configured

## Configuration

### Environment Variables

Add to `backend/.env`:

```bash
# Choose ONE of the following:

# Brave Search (Recommended)
BRAVE_SEARCH_API_KEY=BSA...your_key_here

# OR SerpAPI
SERPAPI_KEY=your_serpapi_key_here

# OR Google Custom Search
GOOGLE_CSE_API_KEY=your_google_api_key
GOOGLE_CSE_ID=your_search_engine_id
```

### Query Limits

To avoid hitting rate limits:

**Per URL Analysis:**
- 12 search queries executed
- ~120 search results analyzed
- Takes 5-15 seconds depending on backend

**Recommendations:**
- Brave Free: ~166 URLs/month
- SerpAPI Free: ~8 URLs/month
- Google CSE Free: ~250 URLs/day

## Output Data Structure

### Reputation Score (0-100)

**Calculation:**
```
Base Score: 70
- High-severity scam reports: -15 each
- Medium-severity scam reports: -10 each
- User complaints: -5 each
Minimum: 0, Maximum: 100
```

**Interpretation:**
- **86-100**: Excellent reputation, highly trusted
- **71-85**: Good reputation, generally safe
- **51-70**: Mixed reputation, requires review
- **31-50**: Poor reputation, likely problematic
- **0-30**: Very poor reputation, high risk

### Risk Levels

- **LOW**: No significant issues found, reputation score ≥ 70
- **MEDIUM**: Some concerns, 1-2 scam reports, or score < 50
- **HIGH**: Multiple reports, 3+ scam mentions, or complaints
- **CRITICAL**: Widespread scam reports (≥3 high-severity)

### Data Fields

```json
{
  "search_performed": true,
  "search_backend": "Brave Search API",
  "total_results_analyzed": 95,
  "queries_used": ["domain.com scam", "..."],

  "scam_indicators": [
    {
      "source": "https://reddit.com/...",
      "title": "Warning: domain.com is a scam",
      "snippet": "Lost $500 to this site...",
      "keywords": ["scam", "fraud", "lost money"],
      "severity": "high"
    }
  ],

  "user_complaints": [
    {
      "type": "victim_report",
      "source": "https://...",
      "snippet": "Never received my order...",
      "indicators": ["did not receive", "lost money"]
    }
  ],

  "reputation_score": 35,
  "risk_level": "HIGH"
}
```

## Integration with Analysis

### Technical Analysis Phase

Web reputation search runs during the technical analysis phase (0-30%):

1. URL structure analyzed
2. DNS/SSL checks performed
3. HTTP request sent
4. **Web reputation search executed** ← New
5. Content analyzed
6. Risk indicators compiled

### AI Analysis Phase

The AI receives web reputation data and considers it in the investigation:

```
WEB REPUTATION ANALYSIS:
- Search Backend: Brave Search API
- Total Search Results Analyzed: 95
- Reputation Score: 35/100
- Risk Level: HIGH
- Scam Reports Found: 7
- User Complaints Found: 12

HIGH-SEVERITY SCAM REPORTS (3):
  1. Reddit: Warning about domain.com scam
  2. Trustpilot: Terrible experience, lost money
  3. BBB: Multiple fraud complaints
```

### Final Report

Web reputation findings are incorporated into:
- **Overall verdict** (SAFE/SUSPICIOUS/MALICIOUS)
- **Risk score** calculation
- **Key findings** with scam report citations
- **Threat indicators** list
- **Recommendations** based on complaints

## Example Use Cases

### Case 1: Legitimate Business

**URL:** `https://amazon.com`

**Web Reputation:**
- Reputation Score: 95/100
- Risk Level: LOW
- Scam Reports: 0
- Positive signals on review sites

**Impact:** Confirms legitimacy, lowers risk score

### Case 2: Known Scam Site

**URL:** `https://fake-paypal-login.tk`

**Web Reputation:**
- Reputation Score: 5/100
- Risk Level: CRITICAL
- Scam Reports: 15 (8 high-severity)
- Multiple victim reports of credential theft

**Impact:**
- Elevates risk indicators to CRITICAL
- AI cites specific scam reports in findings
- Verdict: MALICIOUS with high confidence

### Case 3: Unknown New Site

**URL:** `https://brand-new-shop.xyz`

**Web Reputation:**
- Reputation Score: 70/100
- Risk Level: UNKNOWN
- Scam Reports: 0
- No search results found

**Impact:**
- Neutral - no positive or negative signals
- Relies on technical analysis
- AI notes lack of online presence

### Case 4: Mixed Reputation

**URL:** `https://dropship-store.com`

**Web Reputation:**
- Reputation Score: 45/100
- Risk Level: MEDIUM
- Scam Reports: 3 (1 high-severity)
- User Complaints: 8 (delivery issues, refunds)

**Impact:**
- Moderately increases risk score
- AI investigates complaint patterns
- Verdict: SUSPICIOUS, recommends caution

## Performance Considerations

### Query Optimization

**Current:** 12 queries per URL
**Time:** 5-15 seconds depending on backend

**Optimization Options:**
1. Reduce query count for known-safe domains
2. Cache results for repeated analyses
3. Parallel query execution (already implemented)
4. Adjust query timeouts

### Rate Limit Management

**Built-in Protection:**
- Query limit: 12 per URL
- Automatic backend selection
- Graceful fallback to DuckDuckGo
- Error handling for API failures

**Recommendations:**
- Monitor API usage in dashboard
- Set up alerts for near-limit usage
- Consider paid tiers for high volume

### Caching Strategy

**Potential Implementation:**
```python
# Cache results for 24 hours
cache_key = f"reputation:{domain}:{date}"
if cached_result := cache.get(cache_key):
    return cached_result

# Otherwise perform search
result = await search_reputation(domain)
cache.set(cache_key, result, ttl=86400)
```

## Error Handling

### API Failures

**Behavior:**
- Falls back to next available backend
- If all fail, returns error message
- Analysis continues without reputation data
- AI notes absence of web reputation data

**Error Messages:**
```json
{
  "search_performed": false,
  "error": "No search API configured. Set BRAVE_SEARCH_API_KEY, SERPAPI_KEY, or GOOGLE_CSE_API_KEY"
}
```

### Rate Limiting

**Behavior:**
- HTTP 429 errors handled gracefully
- Partial results returned if available
- Error logged for monitoring
- Suggests API key configuration

## Privacy & Ethics

### Data Handling

✅ **We DO:**
- Search only public information
- Use official APIs
- Respect robots.txt
- Follow API terms of service

❌ **We DON'T:**
- Store personal information from search results
- Scrape aggressively
- Bypass rate limits
- Share raw search data

### User Consent

**Important:** When deploying for production:
1. Inform users that web searches are performed
2. Explain what data is collected
3. Provide opt-out mechanisms
4. Comply with privacy regulations (GDPR, CCPA)

### Responsible Use

**Appropriate:**
- Security research
- Fraud prevention
- Trust & safety investigations
- Due diligence for business decisions

**Inappropriate:**
- Harassment or doxxing
- Competitive intelligence (grey area)
- Bulk scraping for datasets
- Evading detection systems

## Troubleshooting

### "Web reputation search not configured"

**Solution:** Add API key to `.env` file
```bash
cd backend
cp .env.example .env
nano .env
# Add: BRAVE_SEARCH_API_KEY=your_key
```

### "API rate limit exceeded"

**Solutions:**
1. Wait for rate limit to reset
2. Upgrade to paid tier
3. Switch to different backend
4. Implement caching

### "No search results found"

**Possible Causes:**
- Domain is very new (no online presence)
- Domain is uncommon or regional
- Search API is down
- Query syntax issues

**Not necessarily a problem** - just means no reputation data available

### "DuckDuckGo fallback unreliable"

**Solution:** Configure a proper search API
- DDG scraping is best-effort only
- Get a free Brave API key for reliability

## Future Enhancements

### Planned Features

1. **Historical Tracking**
   - Track reputation score over time
   - Detect sudden reputation drops
   - Alert on negative trend changes

2. **Custom Query Templates**
   - User-defined search queries
   - Industry-specific keywords
   - Language-specific searches

3. **Sentiment Analysis**
   - Analyze tone of mentions
   - Positive vs negative sentiment
   - Review star rating extraction

4. **Source Weighting**
   - Trust different sources differently
   - BBB reports = higher weight
   - Reddit = medium weight
   - Unknown blogs = lower weight

5. **Automated Reporting**
   - Export scam reports to authorities
   - Integration with PhishTank
   - Contribute to community databases

## Cost Analysis

### Per-Analysis Cost

**Brave Search (Free Tier):**
- 12 queries per URL
- 2,000 queries/month = ~166 URLs/month
- Cost: $0 (free)

**Brave Search (Paid Tier):**
- $5/month = 15,000 queries
- Cost per URL: $0.004
- 1,250 URLs/month

**SerpAPI:**
- $50/month = 5,000 queries
- Cost per URL: $0.12
- ~416 URLs/month

**Google CSE:**
- 100 queries/day free = ~8 URLs/day
- Paid: $5 per 1,000 queries
- Cost per URL: $0.06 (paid)

### Recommendations by Volume

- **< 100 URLs/month**: Brave Free Tier
- **100-1000 URLs/month**: Brave Paid ($5/month)
- **1000-5000 URLs/month**: Brave or SerpAPI
- **> 5000 URLs/month**: Enterprise solution + caching

## API Key Security

### Best Practices

✅ **DO:**
- Store keys in `.env` file (git-ignored)
- Use environment variables in production
- Rotate keys periodically
- Monitor usage for anomalies

❌ **DON'T:**
- Commit keys to version control
- Share keys in documentation
- Use keys in client-side code
- Reuse keys across projects

### Key Rotation

**Recommended Schedule:**
- Every 90 days for production
- After any suspected compromise
- When team members leave

## Support

### Getting Help

1. Check this guide first
2. Review error messages in backend logs
3. Test API keys with curl
4. Check API provider status pages

### Common Issues

**Issue:** Searches timing out
**Fix:** Increase timeout in `web_reputation_search.py`

**Issue:** Too many false positives
**Fix:** Adjust keyword sensitivity

**Issue:** Missing relevant results
**Fix:** Add more search queries

---

**Documentation Version:** 1.0
**Last Updated:** 2024
**Module:** `backend/web_reputation_search.py`
