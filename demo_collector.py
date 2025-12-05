"""
Demonstration of the scam URL collector with example data.
This simulates what the real scrapers would collect.
"""
import json
import os
import sys
from datetime import datetime, timedelta
import random

# Add scam_url_collector to path
sys.path.insert(0, 'scam_url_collector')

# Example scam URLs from public knowledge / common scams
# These are well-documented scam patterns and examples
EXAMPLE_SCAM_URLS = [
    # Crypto scams
    {
        'url': 'http://eiondmuskgiveaway.com',
        'source': 'reddit',
        'context': 'Someone posted this crypto giveaway scam claiming to be Elon Musk. Obvious fake.',
        'scam_type': 'crypto',
        'metadata': {'upvotes': 245, 'subreddit': 'Scams', 'post_title': 'Is this Elon Musk crypto giveaway legit?'}
    },
    {
        'url': 'http://freecryptodrop.net',
        'source': 'twitter',
        'context': 'Twitter bot promoting fake crypto airdrop. Asks for wallet private keys.',
        'scam_type': 'crypto',
        'metadata': {'retweets': 12, 'likes': 45}
    },
    {
        'url': 'http://bitcoin-doubler.online',
        'source': 'reddit',
        'context': 'Classic crypto doubling scam. Send 1 BTC get 2 back. Never works.',
        'scam_type': 'crypto',
        'metadata': {'upvotes': 189, 'subreddit': 'CryptoCurrency'}
    },

    # Phishing scams
    {
        'url': 'http://secure-paypaI-verify.com',  # Note the capital I instead of l
        'source': 'reddit',
        'context': 'Phishing email claiming my PayPal account was suspended. URL uses capital I instead of lowercase L.',
        'scam_type': 'phishing',
        'metadata': {'upvotes': 312, 'subreddit': 'Scams'}
    },
    {
        'url': 'http://amazonn-security-alert.com',
        'source': 'reddit',
        'context': 'Got email saying my Amazon account was compromised. Link goes to fake login page.',
        'scam_type': 'phishing',
        'metadata': {'upvotes': 278, 'subreddit': 'Scams'}
    },
    {
        'url': 'http://netflix-billing-update.net',
        'source': 'twitter',
        'context': 'Fake Netflix payment update phishing. Steals credit card info.',
        'scam_type': 'phishing',
        'metadata': {'retweets': 8, 'likes': 34}
    },
    {
        'url': 'http://apple-id-locked.org',
        'source': 'bbb',
        'context': 'Phishing scam claiming Apple ID was locked. Requests password and security questions.',
        'scam_type': 'phishing',
        'metadata': {'reports': 45, 'location': 'Multiple states'}
    },

    # Romance/Dating scams
    {
        'url': 'http://meet-singles-near-you.online',
        'source': 'reddit',
        'context': 'Dating scam site. Creates fake profiles and asks for money for "travel expenses".',
        'scam_type': 'romance',
        'metadata': {'upvotes': 156, 'subreddit': 'Scams'}
    },
    {
        'url': 'http://military-romance-connection.com',
        'source': 'ftc',
        'context': 'FTC warning about military romance scams. Scammers pretend to be deployed soldiers needing money.',
        'scam_type': 'romance',
        'metadata': {'article_type': 'consumer_alert'}
    },

    # Job/Employment scams
    {
        'url': 'http://work-from-home-easy-money.biz',
        'source': 'reddit',
        'context': 'Work from home scam. Promises $5000/week for simple tasks. Requires upfront "training fee".',
        'scam_type': 'job',
        'metadata': {'upvotes': 201, 'subreddit': 'WorkOnline'}
    },
    {
        'url': 'http://reshipping-agent-jobs.com',
        'source': 'ftc',
        'context': 'FTC alert on reshipping scams. Victims unknowingly help launder stolen goods.',
        'scam_type': 'job',
        'metadata': {'article_type': 'consumer_alert'}
    },
    {
        'url': 'http://package-forwarding-job.net',
        'source': 'reddit',
        'context': 'Got offered a "package forwarding" job. Its a reshipping scam using stolen credit cards.',
        'scam_type': 'job',
        'metadata': {'upvotes': 167, 'subreddit': 'Scams'}
    },

    # Tech support scams
    {
        'url': 'http://microsoft-support-certified.com',
        'source': 'reddit',
        'context': 'Fake Microsoft tech support. Pop-up said my computer has virus. Called number and they wanted $300.',
        'scam_type': 'tech_support',
        'metadata': {'upvotes': 423, 'subreddit': 'Scams'}
    },
    {
        'url': 'http://apple-support-center.online',
        'source': 'bbb',
        'context': 'Tech support scam impersonating Apple. Requests remote access to computer.',
        'scam_type': 'tech_support',
        'metadata': {'reports': 78, 'location': 'National'}
    },

    # Shopping scams
    {
        'url': 'http://designer-handbags-cheap.shop',
        'source': 'reddit',
        'context': 'Fake designer handbag site. Ordered $500 purse, got cheap knockoff worth $10.',
        'scam_type': 'shopping',
        'metadata': {'upvotes': 134, 'subreddit': 'Scams'}
    },
    {
        'url': 'http://limited-time-offer-deals.com',
        'source': 'twitter',
        'context': 'Fake shopping site with too-good-to-be-true deals. Never ships products.',
        'scam_type': 'shopping',
        'metadata': {'retweets': 15, 'likes': 67}
    },
    {
        'url': 'http://holiday-sale-electronics.net',
        'source': 'ftc',
        'context': 'FTC warning about fake online stores during holidays. Sites collect payment but never ship.',
        'scam_type': 'shopping',
        'metadata': {'article_type': 'consumer_alert'}
    },

    # Financial scams
    {
        'url': 'http://irs-tax-refund-claim.gov.com',
        'source': 'reddit',
        'context': 'Fake IRS website for tax refund. Steals SSN and banking info.',
        'scam_type': 'financial',
        'metadata': {'upvotes': 389, 'subreddit': 'personalfinance'}
    },
    {
        'url': 'http://gov-stimulus-payment.org',
        'source': 'bbb',
        'context': 'Fake government stimulus payment site. Identity theft scam.',
        'scam_type': 'financial',
        'metadata': {'reports': 234, 'location': 'National'}
    },
    {
        'url': 'http://loan-approval-guaranteed.com',
        'source': 'reddit',
        'context': 'Advance fee loan scam. Promises guaranteed approval but requires upfront fees.',
        'scam_type': 'financial',
        'metadata': {'upvotes': 198, 'subreddit': 'personalfinance'}
    },

    # Investment scams
    {
        'url': 'http://forex-trading-guaranteed-profits.biz',
        'source': 'reddit',
        'context': 'Forex trading scam promising 200% returns. Classic Ponzi scheme.',
        'scam_type': 'financial',
        'metadata': {'upvotes': 267, 'subreddit': 'investing'}
    },
    {
        'url': 'http://nft-presale-exclusive.io',
        'source': 'twitter',
        'context': 'Fake NFT presale. Discord link leads to wallet draining contract.',
        'scam_type': 'crypto',
        'metadata': {'retweets': 234, 'likes': 892}
    },

    # Charity scams
    {
        'url': 'http://disaster-relief-donations.org',
        'source': 'ftc',
        'context': 'FTC warning about fake charity sites after disasters. Money goes to scammers not victims.',
        'scam_type': 'financial',
        'metadata': {'article_type': 'consumer_alert'}
    },
    {
        'url': 'http://veterans-support-fund.net',
        'source': 'bbb',
        'context': 'Fake veterans charity. BBB warns organization is not registered and keeps donations.',
        'scam_type': 'financial',
        'metadata': {'reports': 156, 'location': 'National'}
    },

    # Utility/Service scams
    {
        'url': 'http://power-company-disconnect-notice.com',
        'source': 'reddit',
        'context': 'Scam call saying electricity will be shut off unless I pay immediately via gift cards.',
        'scam_type': 'financial',
        'metadata': {'upvotes': 145, 'subreddit': 'Scams'}
    },

    # Prize/Lottery scams
    {
        'url': 'http://you-won-million-dollar-prize.com',
        'source': 'reddit',
        'context': 'Email saying I won Publishers Clearing House. Need to pay "processing fee" to claim.',
        'scam_type': 'financial',
        'metadata': {'upvotes': 178, 'subreddit': 'Scams'}
    },
    {
        'url': 'http://international-lottery-winner.org',
        'source': 'bbb',
        'context': 'Foreign lottery scam. Claims you won lottery you never entered. Requests bank details.',
        'scam_type': 'financial',
        'metadata': {'reports': 298, 'location': 'International'}
    }
]

def simulate_collection():
    """Simulate URL collection from multiple sources."""
    print("=" * 70)
    print("Scam URL Collector - Demonstration")
    print("=" * 70)
    print()

    # Add timestamps and simulate discovery
    collected_urls = []
    for i, url_data in enumerate(EXAMPLE_SCAM_URLS):
        # Add normalized URL
        url = url_data['url']
        url_normalized = url.lower().replace('http://', '').replace('https://', '').rstrip('/')

        # Calculate priority score based on factors
        priority = 0

        # Source credibility
        if url_data['source'] in ['bbb', 'ftc']:
            priority += 5

        # Engagement
        metadata = url_data.get('metadata', {})
        upvotes = metadata.get('upvotes', 0)
        retweets = metadata.get('retweets', 0)
        likes = metadata.get('likes', 0)
        reports = metadata.get('reports', 0)

        priority += min((upvotes + retweets + likes + reports) / 10, 10)

        # Scam type severity
        if url_data['scam_type'] in ['financial', 'identity_theft', 'crypto']:
            priority += 15
        elif url_data['scam_type'] in ['phishing']:
            priority += 10

        # Recency (simulate recent discovery)
        days_ago = random.randint(0, 14)
        date_posted = datetime.now() - timedelta(days=days_ago)
        if days_ago < 7:
            priority += 10
        elif days_ago < 30:
            priority += 5

        collected_urls.append({
            'url': url,
            'url_normalized': url_normalized,
            'source': url_data['source'],
            'source_id': f"demo_{i}",
            'source_url': f"https://example.com/{url_data['source']}/post/{i}",
            'context': url_data['context'],
            'scam_type': url_data['scam_type'],
            'date_posted': date_posted.isoformat(),
            'date_found': datetime.now().isoformat(),
            'metadata': metadata,
            'priority_score': round(priority, 2),
            'investigation_status': 'pending'
        })

    # Sort by priority
    collected_urls.sort(key=lambda x: x['priority_score'], reverse=True)

    print(f"✅ Collected {len(collected_urls)} scam URLs from multiple sources")
    print()

    # Statistics
    sources = {}
    scam_types = {}
    for url in collected_urls:
        sources[url['source']] = sources.get(url['source'], 0) + 1
        scam_types[url['scam_type']] = scam_types.get(url['scam_type'], 0) + 1

    print("📊 URLs by Source:")
    for source, count in sources.items():
        print(f"   {source}: {count}")

    print()
    print("🎯 URLs by Scam Type:")
    for scam_type, count in scam_types.items():
        print(f"   {scam_type}: {count}")

    print()
    print("=" * 70)
    print("Top 25 URLs by Priority Score")
    print("=" * 70)
    print()

    for i, url_data in enumerate(collected_urls[:25], 1):
        print(f"{i}. {url_data['url']}")
        print(f"   Priority Score: {url_data['priority_score']:.1f}")
        print(f"   Source: {url_data['source']} | Type: {url_data['scam_type']}")
        print(f"   Context: {url_data['context'][:100]}...")
        print()

    # Save to JSON
    os.makedirs('scam_url_collector/data', exist_ok=True)
    output_file = 'scam_url_collector/data/demo_scam_urls.json'

    with open(output_file, 'w') as f:
        json.dump({
            'collection_date': datetime.now().isoformat(),
            'total_urls': len(collected_urls),
            'sources': sources,
            'scam_types': scam_types,
            'urls': collected_urls
        }, f, indent=2)

    print("=" * 70)
    print(f"✅ Results saved to {output_file}")
    print(f"✅ Total URLs collected: {len(collected_urls)}")
    print("=" * 70)

    return collected_urls

if __name__ == '__main__':
    simulate_collection()
