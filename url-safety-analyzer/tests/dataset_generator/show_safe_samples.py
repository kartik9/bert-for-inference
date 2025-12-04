"""
Display sample safe/legitimate URLs from various sources.
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import json
import time


class TopWebsitesFetcher:
    """Fetch top websites from Tranco list."""

    def fetch(self, count: int = 5) -> List[Dict[str, Any]]:
        """Fetch top websites."""
        print(f"[Top Websites] Fetching top {count} sites...")

        # Tranco Top 1M list (free, no auth required)
        # Using a curated list of well-known sites for demo
        top_sites = [
            {"domain": "google.com", "rank": 1, "category": "search_engine"},
            {"domain": "youtube.com", "rank": 2, "category": "video"},
            {"domain": "facebook.com", "rank": 3, "category": "social_media"},
            {"domain": "twitter.com", "rank": 4, "category": "social_media"},
            {"domain": "wikipedia.org", "rank": 5, "category": "knowledge"},
            {"domain": "amazon.com", "rank": 6, "category": "ecommerce"},
            {"domain": "reddit.com", "rank": 7, "category": "social_media"},
            {"domain": "github.com", "rank": 8, "category": "technology"},
            {"domain": "microsoft.com", "rank": 9, "category": "technology"},
            {"domain": "apple.com", "rank": 10, "category": "technology"},
        ]

        results = []
        for site in top_sites[:count]:
            results.append({
                "url": f"https://{site['domain']}",
                "domain": site["domain"],
                "rank": site["rank"],
                "category": site["category"],
                "source": "top_websites",
                "is_hard_negative": False,
            })

        print(f"[Top Websites] Fetched {len(results)} URLs")
        return results


class YCombinatorFetcher:
    """Fetch Y Combinator startup URLs (hard negatives)."""

    def fetch(self, count: int = 5) -> List[Dict[str, Any]]:
        """Fetch recent YC startup URLs."""
        print(f"[Y Combinator] Fetching {count} recent startup URLs...")

        try:
            # YC companies API endpoint
            url = "https://api.ycombinator.com/v0.1/companies"

            # Try alternative: scrape YC directory
            yc_url = "https://www.ycombinator.com/companies"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(yc_url, headers=headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Parse company cards
            # Note: YC website structure may change, this is a simplified example
            # In production, we'd use a more robust parser or their API if available

            # For demo purposes, using known recent YC companies
            yc_startups = [
                {
                    "name": "Cursor",
                    "url": "https://cursor.sh",
                    "batch": "S22",
                    "description": "AI-first code editor",
                },
                {
                    "name": "Cal.com",
                    "url": "https://cal.com",
                    "batch": "W21",
                    "description": "Open source scheduling",
                },
                {
                    "name": "Vercel",
                    "url": "https://vercel.com",
                    "batch": "S15",
                    "description": "Frontend cloud platform",
                },
                {
                    "name": "Retool",
                    "url": "https://retool.com",
                    "batch": "W17",
                    "description": "Internal tools platform",
                },
                {
                    "name": "Posthog",
                    "url": "https://posthog.com",
                    "batch": "W20",
                    "description": "Product analytics",
                },
            ]

            results = []
            for startup in yc_startups[:count]:
                results.append({
                    "url": startup["url"],
                    "company_name": startup["name"],
                    "yc_batch": startup["batch"],
                    "description": startup["description"],
                    "source": "ycombinator",
                    "is_hard_negative": True,
                    "why_hard": "Relatively new startup, may have minimal web presence",
                })

            print(f"[Y Combinator] Fetched {len(results)} startup URLs")
            return results

        except Exception as e:
            print(f"[Y Combinator] Error: {e}")
            print("[Y Combinator] Using fallback list of known YC companies")

            # Fallback to known YC companies
            return [
                {
                    "url": "https://cursor.sh",
                    "company_name": "Cursor",
                    "yc_batch": "S22",
                    "source": "ycombinator",
                    "is_hard_negative": True,
                },
                {
                    "url": "https://cal.com",
                    "company_name": "Cal.com",
                    "yc_batch": "W21",
                    "source": "ycombinator",
                    "is_hard_negative": True,
                },
                {
                    "url": "https://vercel.com",
                    "company_name": "Vercel",
                    "yc_batch": "S15",
                    "source": "ycombinator",
                    "is_hard_negative": True,
                },
                {
                    "url": "https://retool.com",
                    "company_name": "Retool",
                    "yc_batch": "W17",
                    "source": "ycombinator",
                    "is_hard_negative": True,
                },
                {
                    "url": "https://posthog.com",
                    "company_name": "Posthog",
                    "yc_batch": "W20",
                    "source": "ycombinator",
                    "is_hard_negative": True,
                },
            ][:count]


class Fortune500Fetcher:
    """Fetch Fortune 500 company URLs."""

    def fetch(self, count: int = 5) -> List[Dict[str, Any]]:
        """Fetch Fortune 500 company URLs."""
        print(f"[Fortune 500] Fetching {count} company URLs...")

        fortune_500 = [
            {"name": "Walmart", "url": "https://walmart.com", "rank": 1},
            {"name": "Amazon", "url": "https://amazon.com", "rank": 2},
            {"name": "Apple", "url": "https://apple.com", "rank": 3},
            {"name": "CVS Health", "url": "https://cvshealth.com", "rank": 4},
            {"name": "UnitedHealth Group", "url": "https://unitedhealthgroup.com", "rank": 5},
            {"name": "ExxonMobil", "url": "https://exxonmobil.com", "rank": 6},
            {"name": "Berkshire Hathaway", "url": "https://berkshirehathaway.com", "rank": 7},
            {"name": "Alphabet (Google)", "url": "https://abc.xyz", "rank": 8},
            {"name": "McKesson", "url": "https://mckesson.com", "rank": 9},
            {"name": "AmerisourceBergen", "url": "https://amerisourcebergen.com", "rank": 10},
        ]

        results = []
        for company in fortune_500[:count]:
            results.append({
                "url": company["url"],
                "company_name": company["name"],
                "fortune_rank": company["rank"],
                "source": "fortune_500",
                "is_hard_negative": False,
            })

        print(f"[Fortune 500] Fetched {len(results)} company URLs")
        return results


class GovernmentSitesFetcher:
    """Fetch government (.gov) URLs."""

    def fetch(self, count: int = 5) -> List[Dict[str, Any]]:
        """Fetch .gov domain URLs."""
        print(f"[Government Sites] Fetching {count} .gov URLs...")

        gov_sites = [
            {"name": "USA.gov", "url": "https://usa.gov", "type": "portal"},
            {"name": "IRS", "url": "https://irs.gov", "type": "tax"},
            {"name": "Social Security Administration", "url": "https://ssa.gov", "type": "benefits"},
            {"name": "CDC", "url": "https://cdc.gov", "type": "health"},
            {"name": "NASA", "url": "https://nasa.gov", "type": "space"},
            {"name": "FBI", "url": "https://fbi.gov", "type": "law_enforcement"},
            {"name": "State Department", "url": "https://state.gov", "type": "foreign_affairs"},
        ]

        results = []
        for site in gov_sites[:count]:
            results.append({
                "url": site["url"],
                "agency_name": site["name"],
                "type": site["type"],
                "source": "government",
                "tld": ".gov",
                "is_hard_negative": False,
            })

        print(f"[Government Sites] Fetched {len(results)} .gov URLs")
        return results


class TechCompaniesFetcher:
    """Fetch major tech company URLs."""

    def fetch(self, count: int = 5) -> List[Dict[str, Any]]:
        """Fetch tech company URLs."""
        print(f"[Tech Companies] Fetching {count} tech company URLs...")

        tech_companies = [
            {"name": "GitHub", "url": "https://github.com", "category": "developer_tools"},
            {"name": "Microsoft", "url": "https://microsoft.com", "category": "software"},
            {"name": "Google", "url": "https://google.com", "category": "search"},
            {"name": "OpenAI", "url": "https://openai.com", "category": "ai"},
            {"name": "Anthropic", "url": "https://anthropic.com", "category": "ai"},
            {"name": "Meta", "url": "https://meta.com", "category": "social_media"},
            {"name": "Netflix", "url": "https://netflix.com", "category": "streaming"},
        ]

        results = []
        for company in tech_companies[:count]:
            results.append({
                "url": company["url"],
                "company_name": company["name"],
                "category": company["category"],
                "source": "tech_companies",
                "is_hard_negative": False,
            })

        print(f"[Tech Companies] Fetched {len(results)} tech company URLs")
        return results


class NewsSitesFetcher:
    """Fetch major news outlet URLs."""

    def fetch(self, count: int = 5) -> List[Dict[str, Any]]:
        """Fetch news site URLs."""
        print(f"[News Sites] Fetching {count} news outlet URLs...")

        news_sites = [
            {"name": "CNN", "url": "https://cnn.com", "type": "cable_news"},
            {"name": "BBC", "url": "https://bbc.com", "type": "international"},
            {"name": "Reuters", "url": "https://reuters.com", "type": "wire_service"},
            {"name": "New York Times", "url": "https://nytimes.com", "type": "newspaper"},
            {"name": "The Guardian", "url": "https://theguardian.com", "type": "newspaper"},
            {"name": "Associated Press", "url": "https://apnews.com", "type": "wire_service"},
        ]

        results = []
        for site in news_sites[:count]:
            results.append({
                "url": site["url"],
                "outlet_name": site["name"],
                "type": site["type"],
                "source": "news_sites",
                "is_hard_negative": False,
            })

        print(f"[News Sites] Fetched {len(results)} news outlet URLs")
        return results


def main():
    """Display safe URL samples from all sources."""
    print("=" * 100)
    print("SAFE/LEGITIMATE URL SAMPLES - Multiple Sources")
    print("=" * 100)
    print()

    all_results = {}

    # Source 1: Top Websites
    print("\n" + "=" * 100)
    print("SOURCE 1: Top Websites (Easy Negatives)")
    print("=" * 100)
    top_websites = TopWebsitesFetcher().fetch(5)
    all_results['top_websites'] = top_websites

    for i, entry in enumerate(top_websites, 1):
        print(f"\n{i}. URL: {entry['url']}")
        print(f"   Domain: {entry['domain']}")
        print(f"   Rank: #{entry['rank']}")
        print(f"   Category: {entry['category']}")
        print(f"   Hard Negative: {entry['is_hard_negative']}")

    # Source 2: Y Combinator (HARD NEGATIVES)
    print("\n\n" + "=" * 100)
    print("SOURCE 2: Y Combinator Startups (HARD NEGATIVES)")
    print("=" * 100)
    yc_startups = YCombinatorFetcher().fetch(5)
    all_results['ycombinator'] = yc_startups

    for i, entry in enumerate(yc_startups, 1):
        print(f"\n{i}. URL: {entry['url']}")
        print(f"   Company: {entry['company_name']}")
        print(f"   YC Batch: {entry['yc_batch']}")
        if 'description' in entry:
            print(f"   Description: {entry['description']}")
        if 'why_hard' in entry:
            print(f"   Why Hard Negative: {entry['why_hard']}")
        print(f"   Hard Negative: {entry['is_hard_negative']}")

    # Source 3: Fortune 500
    print("\n\n" + "=" * 100)
    print("SOURCE 3: Fortune 500 Companies")
    print("=" * 100)
    fortune_500 = Fortune500Fetcher().fetch(5)
    all_results['fortune_500'] = fortune_500

    for i, entry in enumerate(fortune_500, 1):
        print(f"\n{i}. URL: {entry['url']}")
        print(f"   Company: {entry['company_name']}")
        print(f"   Fortune Rank: #{entry['fortune_rank']}")

    # Source 4: Government Sites
    print("\n\n" + "=" * 100)
    print("SOURCE 4: Government Sites (.gov)")
    print("=" * 100)
    gov_sites = GovernmentSitesFetcher().fetch(5)
    all_results['government'] = gov_sites

    for i, entry in enumerate(gov_sites, 1):
        print(f"\n{i}. URL: {entry['url']}")
        print(f"   Agency: {entry['agency_name']}")
        print(f"   Type: {entry['type']}")
        print(f"   TLD: {entry['tld']}")

    # Source 5: Tech Companies
    print("\n\n" + "=" * 100)
    print("SOURCE 5: Tech Companies")
    print("=" * 100)
    tech_companies = TechCompaniesFetcher().fetch(5)
    all_results['tech_companies'] = tech_companies

    for i, entry in enumerate(tech_companies, 1):
        print(f"\n{i}. URL: {entry['url']}")
        print(f"   Company: {entry['company_name']}")
        print(f"   Category: {entry['category']}")

    # Source 6: News Sites
    print("\n\n" + "=" * 100)
    print("SOURCE 6: News Sites")
    print("=" * 100)
    news_sites = NewsSitesFetcher().fetch(5)
    all_results['news_sites'] = news_sites

    for i, entry in enumerate(news_sites, 1):
        print(f"\n{i}. URL: {entry['url']}")
        print(f"   Outlet: {entry['outlet_name']}")
        print(f"   Type: {entry['type']}")

    # Summary
    print("\n\n" + "=" * 100)
    print("SUMMARY OF SAFE URL SOURCES")
    print("=" * 100)
    print(f"Top Websites: {len(top_websites)} URLs (Easy Negatives)")
    print(f"Y Combinator Startups: {len(yc_startups)} URLs (HARD NEGATIVES)")
    print(f"Fortune 500: {len(fortune_500)} URLs")
    print(f"Government Sites: {len(gov_sites)} URLs")
    print(f"Tech Companies: {len(tech_companies)} URLs")
    print(f"News Sites: {len(news_sites)} URLs")
    print(f"Total Safe URLs: {sum([len(top_websites), len(yc_startups), len(fortune_500), len(gov_sites), len(tech_companies), len(news_sites)])}")
    print(f"\nHard Negatives: {len(yc_startups)} URLs")

    # Save results
    output = {
        "fetched_at": "2024-12-04",
        "sources": all_results,
        "summary": {
            "top_websites_count": len(top_websites),
            "ycombinator_count": len(yc_startups),
            "fortune_500_count": len(fortune_500),
            "government_count": len(gov_sites),
            "tech_companies_count": len(tech_companies),
            "news_sites_count": len(news_sites),
            "total_count": sum([len(top_websites), len(yc_startups), len(fortune_500), len(gov_sites), len(tech_companies), len(news_sites)]),
            "hard_negatives_count": len(yc_startups),
        }
    }

    output_file = "safe_url_samples.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()
