"""
Dataset Builder for URL Safety Analysis

Generates comprehensive evaluation dataset with:
- 500 diverse URLs
- Ground truth labels
- Balanced categories
- Local content caching
"""

import json
import logging
import asyncio
from typing import List, Dict, Any
from datetime import datetime, timedelta
import random

from url_cache import URLCache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatasetBuilder:
    """Build comprehensive URL safety evaluation dataset"""

    def __init__(self, cache_dir: str = "./url_cache"):
        """Initialize dataset builder"""
        self.cache = URLCache(cache_dir=cache_dir)
        self.dataset = []

    def _create_safe_urls(self) -> List[Dict[str, Any]]:
        """
        Generate SAFE URLs (170 URLs - 34%)

        Categories:
        - Tier 1: Established sites (80)
        - Tier 2: Verified businesses (50)
        - Tier 3: Legitimate startups (40)
        """
        urls = []

        # Tier 1: Established Legitimate Sites (80 URLs)
        tier1_sites = {
            "search_engines": [
                ("https://www.google.com", "Google Search"),
                ("https://www.bing.com", "Bing Search"),
                ("https://duckduckgo.com", "DuckDuckGo"),
                ("https://search.yahoo.com", "Yahoo Search"),
            ],
            "social_media": [
                ("https://www.facebook.com", "Facebook"),
                ("https://www.twitter.com", "Twitter"),
                ("https://www.linkedin.com", "LinkedIn"),
                ("https://www.instagram.com", "Instagram"),
                ("https://www.reddit.com", "Reddit"),
                ("https://www.tiktok.com", "TikTok"),
                ("https://www.pinterest.com", "Pinterest"),
                ("https://www.snapchat.com", "Snapchat"),
            ],
            "ecommerce": [
                ("https://www.amazon.com", "Amazon"),
                ("https://www.ebay.com", "eBay"),
                ("https://www.walmart.com", "Walmart"),
                ("https://www.target.com", "Target"),
                ("https://www.etsy.com", "Etsy"),
                ("https://www.alibaba.com", "Alibaba"),
                ("https://www.shopify.com", "Shopify"),
                ("https://www.bestbuy.com", "Best Buy"),
                ("https://www.costco.com", "Costco"),
                ("https://www.homedepot.com", "Home Depot"),
            ],
            "financial": [
                ("https://www.paypal.com", "PayPal"),
                ("https://www.chase.com", "Chase Bank"),
                ("https://www.bankofamerica.com", "Bank of America"),
                ("https://www.wellsfargo.com", "Wells Fargo"),
                ("https://www.capitalone.com", "Capital One"),
                ("https://www.venmo.com", "Venmo"),
                ("https://www.stripe.com", "Stripe"),
                ("https://www.square.com", "Square"),
            ],
            "technology": [
                ("https://www.microsoft.com", "Microsoft"),
                ("https://www.apple.com", "Apple"),
                ("https://www.github.com", "GitHub"),
                ("https://stackoverflow.com", "Stack Overflow"),
                ("https://www.adobe.com", "Adobe"),
                ("https://www.salesforce.com", "Salesforce"),
                ("https://www.oracle.com", "Oracle"),
                ("https://www.ibm.com", "IBM"),
                ("https://www.dell.com", "Dell"),
                ("https://www.hp.com", "HP"),
            ],
            "news_media": [
                ("https://www.cnn.com", "CNN"),
                ("https://www.bbc.com", "BBC"),
                ("https://www.nytimes.com", "New York Times"),
                ("https://www.washingtonpost.com", "Washington Post"),
                ("https://www.reuters.com", "Reuters"),
                ("https://www.theguardian.com", "The Guardian"),
                ("https://www.wsj.com", "Wall Street Journal"),
                ("https://www.forbes.com", "Forbes"),
            ],
            "education": [
                ("https://www.mit.edu", "MIT"),
                ("https://www.stanford.edu", "Stanford University"),
                ("https://www.harvard.edu", "Harvard University"),
                ("https://www.berkeley.edu", "UC Berkeley"),
                ("https://www.coursera.org", "Coursera"),
                ("https://www.edx.org", "edX"),
                ("https://www.khanacademy.org", "Khan Academy"),
            ],
            "government": [
                ("https://www.irs.gov", "IRS"),
                ("https://www.usa.gov", "USA.gov"),
                ("https://www.cdc.gov", "CDC"),
                ("https://www.nih.gov", "NIH"),
                ("https://www.fda.gov", "FDA"),
                ("https://www.sec.gov", "SEC"),
            ],
            "entertainment": [
                ("https://www.netflix.com", "Netflix"),
                ("https://www.youtube.com", "YouTube"),
                ("https://www.spotify.com", "Spotify"),
                ("https://www.twitch.tv", "Twitch"),
                ("https://www.hulu.com", "Hulu"),
                ("https://www.disney.com", "Disney"),
            ]
        }

        for category, sites in tier1_sites.items():
            for url, name in sites:
                urls.append({
                    "url": url,
                    "ground_truth_label": "SAFE",
                    "expected_category": "legitimate",
                    "description": f"{name} - Established {category.replace('_', ' ')} platform",
                    "metadata": {
                        "tier": 1,
                        "subcategory": category,
                        "brand": name,
                        "test_purpose": "baseline_safe",
                        "difficulty": "easy"
                    }
                })

        # Tier 2: Verified Businesses (50 URLs)
        tier2_sites = [
            # Major retailers
            ("https://www.gap.com", "Gap", "retail"),
            ("https://www.macys.com", "Macy's", "retail"),
            ("https://www.nordstrom.com", "Nordstrom", "retail"),
            ("https://www.kohls.com", "Kohl's", "retail"),
            ("https://www.jcpenney.com", "JCPenney", "retail"),

            # Travel
            ("https://www.expedia.com", "Expedia", "travel"),
            ("https://www.booking.com", "Booking.com", "travel"),
            ("https://www.airbnb.com", "Airbnb", "travel"),
            ("https://www.tripadvisor.com", "TripAdvisor", "travel"),
            ("https://www.southwest.com", "Southwest Airlines", "travel"),

            # Food delivery
            ("https://www.ubereats.com", "Uber Eats", "food_delivery"),
            ("https://www.doordash.com", "DoorDash", "food_delivery"),
            ("https://www.grubhub.com", "Grubhub", "food_delivery"),

            # Professional services
            ("https://www.intuit.com", "Intuit", "software"),
            ("https://www.zoom.us", "Zoom", "software"),
            ("https://www.slack.com", "Slack", "software"),
            ("https://www.dropbox.com", "Dropbox", "software"),

            # Healthcare
            ("https://www.webmd.com", "WebMD", "healthcare"),
            ("https://www.mayoclinic.org", "Mayo Clinic", "healthcare"),
            ("https://www.cvs.com", "CVS Pharmacy", "healthcare"),
            ("https://www.walgreens.com", "Walgreens", "healthcare"),

            # Automotive
            ("https://www.carmax.com", "CarMax", "automotive"),
            ("https://www.autozone.com", "AutoZone", "automotive"),
            ("https://www.toyota.com", "Toyota", "automotive"),
            ("https://www.ford.com", "Ford", "automotive"),

            # Real estate
            ("https://www.zillow.com", "Zillow", "real_estate"),
            ("https://www.redfin.com", "Redfin", "real_estate"),
            ("https://www.realtor.com", "Realtor.com", "real_estate"),

            # Financial tech
            ("https://www.robinhood.com", "Robinhood", "fintech"),
            ("https://www.coinbase.com", "Coinbase", "fintech"),
            ("https://www.sofi.com", "SoFi", "fintech"),

            # Cloud services
            ("https://aws.amazon.com", "AWS", "cloud"),
            ("https://cloud.google.com", "Google Cloud", "cloud"),
            ("https://azure.microsoft.com", "Azure", "cloud"),

            # Communication
            ("https://www.whatsapp.com", "WhatsApp", "communication"),
            ("https://www.telegram.org", "Telegram", "communication"),
            ("https://www.signal.org", "Signal", "communication"),

            # Gaming
            ("https://www.steam.com", "Steam", "gaming"),
            ("https://www.epicgames.com", "Epic Games", "gaming"),
            ("https://www.playstation.com", "PlayStation", "gaming"),
            ("https://www.xbox.com", "Xbox", "gaming"),

            # Developer tools
            ("https://www.gitlab.com", "GitLab", "developer_tools"),
            ("https://www.atlassian.com", "Atlassian", "developer_tools"),
            ("https://www.jetbrains.com", "JetBrains", "developer_tools"),

            # Legal/Professional
            ("https://www.legalzoom.com", "LegalZoom", "legal"),
            ("https://www.hrblock.com", "H&R Block", "accounting"),
            ("https://www.turbotax.com", "TurboTax", "accounting"),

            # Nonprofit
            ("https://www.wikipedia.org", "Wikipedia", "nonprofit"),
            ("https://www.redcross.org", "Red Cross", "nonprofit"),
            ("https://www.salvation army.org", "Salvation Army", "nonprofit"),
        ]

        for url, name, subcategory in tier2_sites:
            urls.append({
                "url": url,
                "ground_truth_label": "SAFE",
                "expected_category": "legitimate",
                "description": f"{name} - Verified {subcategory} business",
                "metadata": {
                    "tier": 2,
                    "subcategory": subcategory,
                    "brand": name,
                    "test_purpose": "verified_business",
                    "difficulty": "easy"
                }
            })

        # Tier 3: Legitimate Startups/New Sites (40 URLs)
        tier3_sites = [
            ("https://www.notion.so", "Notion", "productivity", "Workspace tool"),
            ("https://www.figma.com", "Figma", "design", "Design tool"),
            ("https://www.canva.com", "Canva", "design", "Graphic design"),
            ("https://www.discord.com", "Discord", "communication", "Chat platform"),
            ("https://www.airtable.com", "Airtable", "productivity", "Database tool"),
            ("https://www.miro.com", "Miro", "productivity", "Whiteboard tool"),
            ("https://www.monday.com", "Monday.com", "productivity", "Project management"),
            ("https://www.asana.com", "Asana", "productivity", "Task management"),
            ("https://www.trello.com", "Trello", "productivity", "Kanban boards"),
            ("https://www.clickup.com", "ClickUp", "productivity", "Project management"),
            ("https://www.linear.app", "Linear", "productivity", "Issue tracking"),
            ("https://www.vercel.com", "Vercel", "developer_tools", "Deployment platform"),
            ("https://www.netlify.com", "Netlify", "developer_tools", "Hosting platform"),
            ("https://www.railway.app", "Railway", "developer_tools", "Infrastructure"),
            ("https://www.supabase.com", "Supabase", "developer_tools", "Backend platform"),
            ("https://www.planetscale.com", "PlanetScale", "developer_tools", "Database platform"),
            ("https://www.clerk.dev", "Clerk", "developer_tools", "Authentication"),
            ("https://www.resend.com", "Resend", "developer_tools", "Email API"),
            ("https://www.loom.com", "Loom", "communication", "Video messaging"),
            ("https://www.calendly.com", "Calendly", "productivity", "Scheduling"),
            ("https://www.typeform.com", "Typeform", "productivity", "Forms"),
            ("https://www.mailchimp.com", "Mailchimp", "marketing", "Email marketing"),
            ("https://www.hubspot.com", "HubSpot", "marketing", "CRM"),
            ("https://www.intercom.com", "Intercom", "marketing", "Customer messaging"),
            ("https://www.segment.com", "Segment", "analytics", "Data platform"),
            ("https://www.amplitude.com", "Amplitude", "analytics", "Product analytics"),
            ("https://www.mixpanel.com", "Mixpanel", "analytics", "Analytics"),
            ("https://www.plausible.io", "Plausible", "analytics", "Web analytics"),
            ("https://www.render.com", "Render", "cloud", "Cloud platform"),
            ("https://www.fly.io", "Fly.io", "cloud", "App hosting"),
            ("https://www.doppler.com", "Doppler", "developer_tools", "Secrets manager"),
            ("https://www.replicate.com", "Replicate", "ai", "ML deployment"),
            ("https://www.huggingface.co", "Hugging Face", "ai", "ML models"),
            ("https://www.anthropic.com", "Anthropic", "ai", "AI research"),
            ("https://www.openai.com", "OpenAI", "ai", "AI research"),
            ("https://www.midjourney.com", "Midjourney", "ai", "AI art"),
            ("https://www.runway.ml", "Runway", "ai", "Creative AI"),
            ("https://www.beehiiv.com", "Beehiiv", "publishing", "Newsletter platform"),
            ("https://www.substack.com", "Substack", "publishing", "Newsletter platform"),
            ("https://www.ghost.org", "Ghost", "publishing", "CMS platform"),
        ]

        for url, name, subcategory, description in tier3_sites:
            urls.append({
                "url": url,
                "ground_truth_label": "SAFE",
                "expected_category": "legitimate",
                "description": f"{name} - {description}",
                "metadata": {
                    "tier": 3,
                    "subcategory": subcategory,
                    "brand": name,
                    "test_purpose": "legitimate_startup",
                    "difficulty": "medium",
                    "note": "Newer domain but verified legitimate"
                }
            })

        logger.info(f"Generated {len(urls)} SAFE URLs")
        return urls

    def _create_malicious_phishing_urls(self) -> List[Dict[str, Any]]:
        """
        Generate PHISHING URLs (60 URLs)

        Categories:
        - Brand impersonation (25)
        - Credential harvesting (20)
        - Typosquatting (15)
        """
        urls = []

        # Brand impersonation - Major brands (25 URLs)
        phishing_patterns = [
            # PayPal variations
            ("https://paypal-secure-login.com", "PayPal", "login_page"),
            ("https://paypal-verify-account.net", "PayPal", "verification"),
            ("https://secure-paypal-update.com", "PayPal", "account_update"),
            ("https://paypal-resolution-center.net", "PayPal", "dispute"),
            ("https://paypal-customer-security.com", "PayPal", "security_alert"),

            # Amazon variations
            ("https://amazon-account-verify.com", "Amazon", "verification"),
            ("https://amazon-security-alert.net", "Amazon", "security"),
            ("https://amazon-prize-winner.com", "Amazon", "prize_scam"),
            ("https://amazon-customer-service-help.net", "Amazon", "support"),
            ("https://amazon-order-confirmation.com", "Amazon", "order_scam"),

            # Microsoft variations
            ("https://microsoft-account-security.com", "Microsoft", "security"),
            ("https://microsoft-support-center.net", "Microsoft", "tech_support"),
            ("https://microsoft-office-renewal.com", "Microsoft", "subscription"),
            ("https://windows-security-update.net", "Microsoft", "update_scam"),

            # Apple variations
            ("https://apple-id-verify.com", "Apple", "id_verification"),
            ("https://apple-security-alert.net", "Apple", "security"),
            ("https://icloud-storage-upgrade.com", "Apple", "storage_scam"),

            # Bank variations
            ("https://chase-online-banking.net", "Chase", "banking"),
            ("https://bankofamerica-secure.com", "Bank of America", "banking"),
            ("https://wellsfargo-online.net", "Wells Fargo", "banking"),

            # Cryptocurrency
            ("https://coinbase-security-verify.com", "Coinbase", "crypto"),
            ("https://binance-account-recovery.net", "Binance", "crypto"),
            ("https://metamask-wallet-connect.com", "MetaMask", "crypto_wallet"),

            # Social media
            ("https://facebook-security-check.com", "Facebook", "social"),
            ("https://instagram-verify-account.net", "Instagram", "social"),
        ]

        for url, brand, pattern_type in phishing_patterns:
            urls.append({
                "url": url,
                "ground_truth_label": "MALICIOUS",
                "expected_category": "phishing",
                "description": f"Phishing site impersonating {brand} - {pattern_type}",
                "metadata": {
                    "subcategory": "brand_impersonation",
                    "impersonated_brand": brand,
                    "phishing_type": pattern_type,
                    "threat_indicators": ["brand_impersonation", "credential_phishing"],
                    "test_purpose": "phishing_detection",
                    "difficulty": "medium"
                }
            })

        # Credential harvesting (20 URLs)
        credential_phishing = [
            ("https://secure-login-verify.com", "Generic", "generic_login"),
            ("https://account-verification-required.net", "Generic", "verification"),
            ("https://update-your-payment-method.com", "Generic", "payment_update"),
            ("https://confirm-your-identity.net", "Generic", "identity_verify"),
            ("https://urgent-security-alert.com", "Generic", "urgency"),
            ("https://email-account-expiring.net", "Email", "email_expiry"),
            ("https://webmail-storage-full.com", "Email", "storage_scam"),
            ("https://dropbox-file-share-login.net", "Dropbox", "file_share"),
            ("https://docusign-document-ready.com", "DocuSign", "document"),
            ("https://fedex-package-delivery.net", "FedEx", "delivery"),
            ("https://ups-tracking-update.com", "UPS", "delivery"),
            ("https://usps-redelivery-schedule.net", "USPS", "delivery"),
            ("https://netflix-payment-update.com", "Netflix", "subscription"),
            ("https://spotify-account-suspended.net", "Spotify", "subscription"),
            ("https://linkedin-profile-viewed.com", "LinkedIn", "social_engineering"),
            ("https://zoom-meeting-invitation.net", "Zoom", "meeting_scam"),
            ("https://teams-meeting-link.com", "Microsoft Teams", "meeting_scam"),
            ("https://google-drive-shared-doc.net", "Google Drive", "file_share"),
            ("https://onedrive-file-access.com", "OneDrive", "file_share"),
            ("https://slack-workspace-invite.net", "Slack", "workspace_scam"),
        ]

        for url, target, phish_type in credential_phishing:
            urls.append({
                "url": url,
                "ground_truth_label": "MALICIOUS",
                "expected_category": "phishing",
                "description": f"Credential harvesting - {target} {phish_type}",
                "metadata": {
                    "subcategory": "credential_harvesting",
                    "target_service": target,
                    "phishing_type": phish_type,
                    "threat_indicators": ["credential_phishing", "fake_login"],
                    "test_purpose": "credential_phishing_detection",
                    "difficulty": "medium"
                }
            })

        # Typosquatting (15 URLs)
        typosquat_urls = [
            ("https://gooogle.com", "Google", "doubled_letter"),
            ("https://micr0soft.com", "Microsoft", "number_substitution"),
            ("https://paypa1.com", "PayPal", "number_substitution"),
            ("https://arnaz0n.com", "Amazon", "character_swap"),
            ("https://faceb00k.com", "Facebook", "number_substitution"),
            ("https://yah00.com", "Yahoo", "number_substitution"),
            ("https://netfIix.com", "Netflix", "character_substitution"),
            ("https://app1e.com", "Apple", "number_substitution"),
            ("https://twltter.com", "Twitter", "character_swap"),
            ("https://linkedln.com", "LinkedIn", "character_substitution"),
            ("https://amaz0n.com", "Amazon", "number_substitution"),
            ("https://go0gle.com", "Google", "number_substitution"),
            ("https://rnicr0s0ft.com", "Microsoft", "character_substitution"),
            ("https://githuh.com", "GitHub", "typo"),
            ("https://instaqram.com", "Instagram", "character_substitution"),
        ]

        for url, brand, typo_type in typosquat_urls:
            urls.append({
                "url": url,
                "ground_truth_label": "MALICIOUS",
                "expected_category": "phishing",
                "description": f"Typosquatting {brand} - {typo_type}",
                "metadata": {
                    "subcategory": "typosquatting",
                    "impersonated_brand": brand,
                    "typo_technique": typo_type,
                    "threat_indicators": ["typosquatting", "brand_impersonation"],
                    "test_purpose": "typosquatting_detection",
                    "difficulty": "easy"
                }
            })

        logger.info(f"Generated {len(urls)} PHISHING URLs")
        return urls

    def _create_malicious_scam_urls(self) -> List[Dict[str, Any]]:
        """
        Generate SCAM URLs (50 URLs)

        Categories:
        - Tech support scams (12)
        - Romance scams (8)
        - Investment fraud (15)
        - Prize/lottery scams (10)
        - Fake products (5)
        """
        urls = []

        # Tech support scams (12)
        tech_support = [
            ("https://microsoft-support-helpdesk.com", "Microsoft", "support_scam"),
            ("https://windows-defender-alert.net", "Windows", "fake_alert"),
            ("https://apple-tech-support-center.com", "Apple", "support_scam"),
            ("https://mcafee-renewal-required.net", "McAfee", "antivirus_scam"),
            ("https://norton-subscription-expired.com", "Norton", "antivirus_scam"),
            ("https://computer-virus-detected.net", "Generic", "virus_alert"),
            ("https://system-warning-critical-error.com", "Generic", "fake_warning"),
            ("https://pc-repair-tech-support.net", "Generic", "repair_scam"),
            ("https://call-microsoft-support-now.com", "Microsoft", "urgency_scam"),
            ("https://windows-license-expired.net", "Windows", "license_scam"),
            ("https://your-computer-infected.com", "Generic", "malware_warning"),
            ("https://remove-virus-now.net", "Generic", "removal_scam"),
        ]

        for url, target, scam_type in tech_support:
            urls.append({
                "url": url,
                "ground_truth_label": "MALICIOUS",
                "expected_category": "scam",
                "description": f"Tech support scam - {target} {scam_type}",
                "metadata": {
                    "subcategory": "tech_support_scam",
                    "impersonated_brand": target,
                    "scam_type": scam_type,
                    "threat_indicators": ["tech_support_scam", "fake_alert", "urgency"],
                    "test_purpose": "tech_support_scam_detection",
                    "difficulty": "medium"
                }
            })

        # Romance scams (8)
        romance_scams = [
            ("https://dating-singles-near-you.com", "Dating", "fake_dating"),
            ("https://meet-local-singles-tonight.net", "Dating", "fake_dating"),
            ("https://lonely-hearts-connection.com", "Dating", "romance_scam"),
            ("https://international-dating-service.net", "Dating", "foreign_romance"),
            ("https://mature-singles-dating.com", "Dating", "age_targeted"),
            ("https://military-singles-connect.net", "Dating", "military_romance"),
            ("https://christian-dating-network.com", "Dating", "religious_targeted"),
            ("https://wealthy-singles-club.net", "Dating", "wealth_scam"),
        ]

        for url, category, scam_type in romance_scams:
            urls.append({
                "url": url,
                "ground_truth_label": "MALICIOUS",
                "expected_category": "scam",
                "description": f"Romance scam - {scam_type}",
                "metadata": {
                    "subcategory": "romance_scam",
                    "scam_category": category,
                    "scam_type": scam_type,
                    "threat_indicators": ["romance_scam", "fake_dating_site"],
                    "test_purpose": "romance_scam_detection",
                    "difficulty": "medium"
                }
            })

        # Investment fraud (15)
        investment_fraud = [
            ("https://crypto-guaranteed-returns.com", "Crypto", "guaranteed_returns"),
            ("https://bitcoin-doubler-investment.net", "Crypto", "doubling_scam"),
            ("https://get-rich-quick-trading.com", "Trading", "unrealistic_promise"),
            ("https://forex-trading-signals-premium.net", "Forex", "signal_scam"),
            ("https://nft-early-access-presale.com", "NFT", "presale_scam"),
            ("https://crypto-airdrop-free-tokens.net", "Crypto", "airdrop_scam"),
            ("https://investment-passive-income.com", "Investment", "passive_income"),
            ("https://high-yield-investment-program.net", "HYIP", "ponzi"),
            ("https://binary-options-trading-pro.com", "Binary Options", "options_scam"),
            ("https://stock-market-insider-tips.net", "Stocks", "insider_scam"),
            ("https://cryptocurrency-mining-profit.com", "Crypto Mining", "mining_scam"),
            ("https://real-estate-investment-deals.net", "Real Estate", "property_scam"),
            ("https://automated-trading-bot.com", "Trading Bot", "bot_scam"),
            ("https://forex-signals-guaranteed.net", "Forex", "guaranteed_profits"),
            ("https://invest-and-earn-daily.com", "Investment", "daily_returns"),
        ]

        for url, investment_type, fraud_type in investment_fraud:
            urls.append({
                "url": url,
                "ground_truth_label": "MALICIOUS",
                "expected_category": "fraud",
                "description": f"Investment fraud - {investment_type} {fraud_type}",
                "metadata": {
                    "subcategory": "investment_fraud",
                    "investment_type": investment_type,
                    "fraud_type": fraud_type,
                    "threat_indicators": ["investment_fraud", "unrealistic_returns", "get_rich_quick"],
                    "test_purpose": "investment_fraud_detection",
                    "difficulty": "medium"
                }
            })

        # Prize/lottery scams (10)
        prize_scams = [
            ("https://you-won-prize-claim-now.com", "Prize", "generic_prize"),
            ("https://amazon-gift-card-winner.net", "Amazon", "gift_card"),
            ("https://walmart-survey-reward.com", "Walmart", "survey_scam"),
            ("https://iphone-giveaway-winner.net", "iPhone", "device_giveaway"),
            ("https://sweepstakes-winner-notification.com", "Sweepstakes", "lottery"),
            ("https://congratulations-prize-winner.net", "Generic", "winner_scam"),
            ("https://claim-your-reward-immediately.com", "Generic", "urgency_reward"),
            ("https://lottery-international-winner.net", "Lottery", "foreign_lottery"),
            ("https://unclaimed-prize-notification.com", "Generic", "unclaimed_scam"),
            ("https://exclusive-member-reward.net", "Membership", "fake_reward"),
        ]

        for url, prize_type, scam_type in prize_scams:
            urls.append({
                "url": url,
                "ground_truth_label": "MALICIOUS",
                "expected_category": "scam",
                "description": f"Prize scam - {prize_type} {scam_type}",
                "metadata": {
                    "subcategory": "prize_scam",
                    "prize_type": prize_type,
                    "scam_type": scam_type,
                    "threat_indicators": ["prize_scam", "fake_winner", "urgency"],
                    "test_purpose": "prize_scam_detection",
                    "difficulty": "easy"
                }
            })

        # Fake products (5)
        fake_products = [
            ("https://designer-handbags-discount.com", "Luxury Goods", "counterfeit"),
            ("https://authentic-watches-cheap.net", "Watches", "counterfeit"),
            ("https://brand-shoes-wholesale.com", "Shoes", "counterfeit"),
            ("https://replica-sunglasses-cheap.net", "Sunglasses", "replica"),
            ("https://discount-electronics-wholesale.com", "Electronics", "fake_products"),
        ]

        for url, product_type, fraud_type in fake_products:
            urls.append({
                "url": url,
                "ground_truth_label": "MALICIOUS",
                "expected_category": "scam",
                "description": f"Fake product site - {product_type} {fraud_type}",
                "metadata": {
                    "subcategory": "fake_products",
                    "product_type": product_type,
                    "fraud_type": fraud_type,
                    "threat_indicators": ["counterfeit", "fraud", "fake_products"],
                    "test_purpose": "fake_product_detection",
                    "difficulty": "medium"
                }
            })

        logger.info(f"Generated {len(urls)} SCAM URLs")
        return urls

    def _create_malicious_malware_urls(self) -> List[Dict[str, Any]]:
        """
        Generate MALWARE URLs (40 URLs)

        Categories:
        - Fake software downloads (15)
        - Drive-by downloads (10)
        - Trojan distribution (10)
        - Exploit kits (5)
        """
        urls = []

        # Fake software downloads (15)
        fake_software = [
            ("https://download-adobe-reader-free.com", "Adobe Reader", "pdf_reader"),
            ("https://free-microsoft-office-download.net", "Microsoft Office", "office_suite"),
            ("https://windows-10-free-download.com", "Windows", "os_download"),
            ("https://ccleaner-pro-crack.net", "CCleaner", "cracked_software"),
            ("https://photoshop-free-full-version.com", "Photoshop", "cracked_software"),
            ("https://antivirus-free-download.net", "Antivirus", "fake_av"),
            ("https://codec-required-download.com", "Codec", "codec_scam"),
            ("https://flash-player-update-required.net", "Flash Player", "fake_update"),
            ("https://java-update-download.com", "Java", "fake_update"),
            ("https://video-downloader-free.net", "Video Downloader", "tool_scam"),
            ("https://pdf-converter-download.com", "PDF Converter", "tool_scam"),
            ("https://file-recovery-software-free.net", "File Recovery", "tool_scam"),
            ("https://driver-update-software.com", "Driver Updater", "pup"),
            ("https://pc-cleaner-speed-booster.net", "PC Cleaner", "pup"),
            ("https://free-vpn-download-unlimited.com", "VPN", "fake_vpn"),
        ]

        for url, software_name, malware_type in fake_software:
            urls.append({
                "url": url,
                "ground_truth_label": "MALICIOUS",
                "expected_category": "malware",
                "description": f"Fake software download - {software_name}",
                "metadata": {
                    "subcategory": "fake_software",
                    "software_type": software_name,
                    "malware_type": malware_type,
                    "threat_indicators": ["malware", "fake_download", "trojan"],
                    "test_purpose": "malware_detection",
                    "difficulty": "medium"
                }
            })

        # Drive-by downloads (10)
        drive_by = [
            ("https://watch-free-movies-online.net", "Streaming", "video_scam"),
            ("https://free-mp3-music-download.com", "Music", "download_scam"),
            ("https://sports-live-stream-free.net", "Sports", "streaming_scam"),
            ("https://adult-content-verify-age.com", "Adult", "malvertising"),
            ("https://click-to-continue-reading.net", "News", "clickbait_malware"),
            ("https://survey-complete-continue.com", "Survey", "survey_malware"),
            ("https://download-file-rapidshare.net", "File Sharing", "fake_file_host"),
            ("https://torrent-download-movies.com", "Torrent", "piracy_malware"),
            ("https://game-hacks-cheats-download.net", "Gaming", "game_malware"),
            ("https://ebook-pdf-free-download.com", "Ebook", "document_malware"),
        ]

        for url, category, malware_type in drive_by:
            urls.append({
                "url": url,
                "ground_truth_label": "MALICIOUS",
                "expected_category": "malware",
                "description": f"Drive-by download - {category}",
                "metadata": {
                    "subcategory": "drive_by_download",
                    "content_category": category,
                    "malware_type": malware_type,
                    "threat_indicators": ["malware", "drive_by_download", "exploit"],
                    "test_purpose": "drive_by_detection",
                    "difficulty": "hard"
                }
            })

        # Trojan distribution (10)
        trojans = [
            ("https://system-update-critical.com", "System", "fake_update"),
            ("https://security-patch-required.net", "Security", "fake_patch"),
            ("https://activate-windows-product-key.com", "Activation", "keygen"),
            ("https://unlock-premium-features.net", "Crack", "software_crack"),
            ("https://remove-watermark-tool.com", "Tool", "trojan_tool"),
            ("https://password-recovery-free.net", "Recovery", "password_stealer"),
            ("https://keylogger-monitoring-software.com", "Monitoring", "keylogger"),
            ("https://remote-access-tool-free.net", "RAT", "remote_access"),
            ("https://email-password-hack-tool.com", "Hacking", "credential_stealer"),
            ("https://facebook-account-hacker.net", "Social Hack", "account_stealer"),
        ]

        for url, trojan_type, specific_type in trojans:
            urls.append({
                "url": url,
                "ground_truth_label": "MALICIOUS",
                "expected_category": "malware",
                "description": f"Trojan distribution - {trojan_type}",
                "metadata": {
                    "subcategory": "trojan",
                    "trojan_type": trojan_type,
                    "specific_type": specific_type,
                    "threat_indicators": ["trojan", "malware", "credential_theft"],
                    "test_purpose": "trojan_detection",
                    "difficulty": "hard"
                }
            })

        # Exploit kits (5)
        exploit_kits = [
            ("https://browser-plugin-update-required.com", "Browser", "exploit"),
            ("https://javascript-error-fix.net", "JavaScript", "exploit"),
            ("https://media-player-codec-install.com", "Media", "exploit"),
            ("https://certificate-error-bypass.net", "Certificate", "exploit"),
            ("https://security-warning-override.com", "Security", "exploit"),
        ]

        for url, exploit_target, exploit_type in exploit_kits:
            urls.append({
                "url": url,
                "ground_truth_label": "MALICIOUS",
                "expected_category": "malware",
                "description": f"Exploit kit - {exploit_target}",
                "metadata": {
                    "subcategory": "exploit_kit",
                    "exploit_target": exploit_target,
                    "exploit_type": exploit_type,
                    "threat_indicators": ["exploit_kit", "malware", "vulnerability"],
                    "test_purpose": "exploit_detection",
                    "difficulty": "hard"
                }
            })

        logger.info(f"Generated {len(urls)} MALWARE URLs")
        return urls

    def _create_suspicious_urls(self) -> List[Dict[str, Any]]:
        """
        Generate SUSPICIOUS URLs (90 URLs)

        Categories:
        - Borderline/questionable (40)
        - Gray area (30)
        - Potentially compromised (20)
        """
        urls = []

        # Borderline/questionable (40)
        borderline = [
            # Low-quality affiliate/marketing
            ("https://click-here-best-deals.com", "affiliate", "Aggressive affiliate marketing"),
            ("https://earn-money-from-home-now.net", "work_from_home", "Questionable work-from-home"),
            ("https://weight-loss-miracle-supplement.com", "health", "Dubious health claims"),
            ("https://anti-aging-secret-formula.net", "health", "Unverified health product"),
            ("https://make-money-online-easy.com", "money", "Questionable income claims"),
            ("https://followers-instagram-free.net", "social_media", "Social media manipulation"),
            ("https://likes-facebook-buy-cheap.com", "social_media", "Fake engagement service"),
            ("https://seo-backlinks-instant.net", "seo", "Black-hat SEO"),
            ("https://website-traffic-boost.com", "marketing", "Traffic manipulation"),
            ("https://email-list-purchase.net", "marketing", "Spam email lists"),

            # Clickbait content
            ("https://shocking-news-you-wont-believe.com", "clickbait", "Clickbait news"),
            ("https://celebrity-scandal-leaked.net", "clickbait", "Celebrity gossip"),
            ("https://doctors-hate-this-one-trick.com", "clickbait", "Health clickbait"),
            ("https://local-moms-discover-secret.net", "clickbait", "Local clickbait"),
            ("https://weird-trick-reveals.com", "clickbait", "Trick clickbait"),

            # Unverified services
            ("https://essay-writing-service-cheap.com", "academic", "Academic dishonesty"),
            ("https://term-paper-buy-online.net", "academic", "Paper mill"),
            ("https://cheap-prescription-no-doctor.com", "pharmacy", "Unverified pharmacy"),
            ("https://online-pharmacy-discount.net", "pharmacy", "Questionable pharmacy"),
            ("https://background-check-anyone.com", "surveillance", "Privacy violation"),

            # Gambling/betting (gray area)
            ("https://online-casino-free-bonus.net", "gambling", "Online casino"),
            ("https://sports-betting-guaranteed.com", "gambling", "Sports betting"),
            ("https://poker-online-real-money.net", "gambling", "Online poker"),

            # Debt/loans
            ("https://payday-loans-instant-approval.com", "loans", "Predatory lending"),
            ("https://bad-credit-loans-guaranteed.net", "loans", "Subprime lending"),
            ("https://debt-consolidation-fast.com", "debt", "Debt service"),

            # Cryptocurrency (unverified)
            ("https://new-crypto-token-launch.com", "crypto", "Unverified token"),
            ("https://crypto-signals-premium.net", "crypto", "Paid signals"),
            ("https://nft-marketplace-new.com", "nft", "New NFT platform"),

            # Downloads (questionable)
            ("https://mod-apk-android-games.com", "mobile", "Modified apps"),
            ("https://cracked-games-download.net", "gaming", "Pirated games"),
            ("https://ebook-torrents-free.com", "ebooks", "Pirated content"),

            # Services
            ("https://background-removal-ai.com", "tools", "Unverified AI tool"),
            ("https://resume-writing-guarantee.net", "career", "Resume service"),
            ("https://tax-refund-maximizer.com", "finance", "Tax service"),

            # Domain parking
            ("https://this-domain-for-sale.com", "parking", "Domain parking"),
            ("https://coming-soon-launching.net", "parking", "Under construction"),
            ("https://page-not-found-redirect.com", "error", "Error page farm"),

            # Misc questionable
            ("https://cheap-followers-buy.com", "social", "Social manipulation"),
            ("https://vpn-free-unlimited-fast.net", "vpn", "Free VPN (data harvesting)"),
        ]

        for url, category, description in borderline:
            urls.append({
                "url": url,
                "ground_truth_label": "SUSPICIOUS",
                "expected_category": "questionable",
                "description": description,
                "metadata": {
                    "subcategory": "borderline",
                    "category": category,
                    "threat_indicators": ["poor_reputation", "questionable_practices"],
                    "test_purpose": "borderline_detection",
                    "difficulty": "hard",
                    "note": "Not definitively malicious but concerning"
                }
            })

        # Gray area (30)
        gray_area = [
            # Adult content (policy-dependent)
            ("https://adult-dating-network.com", "adult", "Adult dating"),
            ("https://webcam-models-live.net", "adult", "Webcam service"),
            ("https://adult-entertainment-premium.com", "adult", "Adult content"),

            # Unregulated crypto
            ("https://decentralized-exchange-dex.com", "defi", "Unregulated DEX"),
            ("https://yield-farming-protocol.net", "defi", "DeFi protocol"),
            ("https://token-swap-platform.com", "crypto", "Token swap"),

            # File sharing
            ("https://file-upload-anonymous.com", "file_sharing", "Anonymous uploads"),
            ("https://torrent-tracker-site.net", "torrents", "Torrent tracker"),
            ("https://cloud-storage-unlimited.com", "storage", "Unlimited storage"),

            # Privacy tools (dual use)
            ("https://encrypted-email-service.net", "privacy", "Encrypted email"),
            ("https://anonymous-browsing-vpn.com", "privacy", "Privacy VPN"),
            ("https://temp-email-disposable.net", "privacy", "Disposable email"),

            # Cryptocurrency mixing
            ("https://bitcoin-mixer-anonymous.com", "crypto", "Coin mixer"),
            ("https://crypto-tumbler-service.net", "crypto", "Tumbler service"),

            # Offshore services
            ("https://offshore-hosting-provider.com", "hosting", "Offshore hosting"),
            ("https://privacy-domain-registration.net", "domains", "Anonymous registration"),

            # Alternative medicine
            ("https://natural-health-remedies.com", "health", "Alternative medicine"),
            ("https://holistic-healing-center.net", "health", "Holistic health"),
            ("https://crystal-healing-shop.com", "health", "Crystal therapy"),

            # Psychic/astrology
            ("https://psychic-readings-online.com", "psychic", "Psychic service"),
            ("https://tarot-card-reading.net", "psychic", "Tarot readings"),
            ("https://astrology-predictions.com", "astrology", "Astrology"),

            # Supplements (unverified)
            ("https://bodybuilding-supplements.com", "supplements", "Bodybuilding"),
            ("https://nootropics-brain-boost.net", "supplements", "Nootropics"),
            ("https://testosterone-booster.com", "supplements", "Hormone supplement"),

            # Replica/look-alike
            ("https://inspired-by-designer.com", "fashion", "Designer inspired"),
            ("https://similar-to-brand.net", "products", "Brand lookalike"),

            # Survey sites
            ("https://paid-surveys-rewards.com", "surveys", "Paid surveys"),
            ("https://opinion-rewards-cash.net", "surveys", "Survey rewards"),
            ("https://gift-cards-earn-free.com", "rewards", "Reward program"),
        ]

        for url, category, description in gray_area:
            urls.append({
                "url": url,
                "ground_truth_label": "SUSPICIOUS",
                "expected_category": "gray_area",
                "description": description,
                "metadata": {
                    "subcategory": "gray_area",
                    "category": category,
                    "threat_indicators": ["policy_violation", "unregulated"],
                    "test_purpose": "gray_area_classification",
                    "difficulty": "hard",
                    "note": "Legal but policy-questionable"
                }
            })

        # Potentially compromised (20)
        compromised = [
            ("https://old-wordpress-blog.com", "wordpress", "Outdated WordPress"),
            ("https://abandoned-forum-site.net", "forum", "Unmaintained forum"),
            ("https://legacy-php-application.com", "webapp", "Legacy app"),
            ("https://personal-blog-2010.net", "blog", "Old personal blog"),
            ("https://small-business-website.com", "business", "Small business site"),
            ("https://community-forum-archived.net", "community", "Archived forum"),
            ("https://photo-gallery-old.com", "gallery", "Old photo gallery"),
            ("https://free-web-hosting-site.net", "hosting", "Free hosting"),
            ("https://geocities-style-page.com", "retro", "Retro website"),
            ("https://flash-based-website.net", "flash", "Flash site"),
            ("https://joomla-cms-site.com", "joomla", "Joomla CMS"),
            ("https://drupal-community-site.net", "drupal", "Drupal site"),
            ("https://phpbb-forum.com", "phpbb", "phpBB forum"),
            ("https://vbulletin-board.net", "vbulletin", "vBulletin forum"),
            ("https://old-ecommerce-store.com", "ecommerce", "Legacy store"),
            ("https://expired-ssl-certificate.net", "ssl", "SSL expired"),
            ("https://shared-hosting-cheap.com", "hosting", "Shared hosting"),
            ("https://free-subdomain-site.net", "subdomain", "Free subdomain"),
            ("https://development-staging-site.com", "dev", "Staging environment"),
            ("https://test-environment-public.net", "test", "Test environment"),
        ]

        for url, platform, description in compromised:
            urls.append({
                "url": url,
                "ground_truth_label": "SUSPICIOUS",
                "expected_category": "potentially_compromised",
                "description": description,
                "metadata": {
                    "subcategory": "potentially_compromised",
                    "platform": platform,
                    "threat_indicators": ["outdated_software", "security_risk"],
                    "test_purpose": "compromised_detection",
                    "difficulty": "hard",
                    "note": "Legitimate but potentially vulnerable"
                }
            })

        logger.info(f"Generated {len(urls)} SUSPICIOUS URLs")
        return urls

    def _create_manual_review_urls(self) -> List[Dict[str, Any]]:
        """
        Generate MANUAL_REVIEW_REQUIRED URLs (50 URLs)

        Categories:
        - New/unknown domains (25)
        - Ambiguous cases (15)
        - Limited data (10)
        """
        urls = []

        # New/unknown domains (25)
        new_domains = [
            ("https://brand-new-startup-2024.com", "startup", "Newly registered domain"),
            ("https://just-launched-product.net", "product", "New product launch"),
            ("https://fresh-content-platform.com", "platform", "New platform"),
            ("https://emerging-technology-ai.net", "tech", "New tech company"),
            ("https://local-business-new.com", "local", "New local business"),
            ("https://indie-game-developer.net", "gaming", "Indie developer"),
            ("https://personal-portfolio-site.com", "portfolio", "Personal portfolio"),
            ("https://small-consultancy-firm.net", "consulting", "Small consultancy"),
            ("https://freelancer-services.com", "freelance", "Freelancer site"),
            ("https://niche-blog-topic.net", "blog", "Niche blog"),
            ("https://regional-news-outlet.com", "news", "Local news"),
            ("https://community-project-initiative.net", "community", "Community project"),
            ("https://nonprofit-organization-new.com", "nonprofit", "New nonprofit"),
            ("https://educational-resource-free.net", "education", "Educational resource"),
            ("https://open-source-project.com", "opensource", "Open source project"),
            ("https://artist-portfolio-gallery.net", "art", "Artist portfolio"),
            ("https://musician-band-official.com", "music", "Band website"),
            ("https://photography-portfolio.net", "photography", "Photographer site"),
            ("https://writer-author-page.com", "writing", "Author website"),
            ("https://podcast-show-official.net", "podcast", "Podcast site"),
            ("https://youtube-creator-merch.com", "creator", "Creator merchandise"),
            ("https://twitch-streamer-page.net", "streaming", "Streamer page"),
            ("https://discord-community-server.com", "community", "Discord community"),
            ("https://telegram-group-official.net", "community", "Telegram group"),
            ("https://reddit-subreddit-wiki.com", "community", "Subreddit wiki"),
        ]

        for url, category, description in new_domains:
            urls.append({
                "url": url,
                "ground_truth_label": "MANUAL_REVIEW_REQUIRED",
                "expected_category": "unknown",
                "description": description,
                "metadata": {
                    "subcategory": "new_domain",
                    "category": category,
                    "reason": "Insufficient reputation data",
                    "test_purpose": "new_domain_handling",
                    "difficulty": "hard",
                    "note": "Requires human judgment"
                }
            })

        # Ambiguous cases (15)
        ambiguous = [
            ("https://mixed-reviews-product.com", "product", "Conflicting user reviews"),
            ("https://controversial-content-site.net", "content", "Controversial but legal"),
            ("https://parody-brand-satire.com", "parody", "Parody/satire site"),
            ("https://look-alike-brand.net", "brand", "Similar to known brand"),
            ("https://affiliate-review-site.com", "affiliate", "Heavy affiliate links"),
            ("https://comparison-shopping.net", "shopping", "Price comparison"),
            ("https://coupon-deals-aggregator.com", "coupons", "Coupon aggregator"),
            ("https://free-trial-offers.net", "trials", "Free trial aggregator"),
            ("https://sponsored-content-hub.com", "sponsored", "Sponsored content"),
            ("https://native-advertising.net", "advertising", "Native ads"),
            ("https://user-generated-content.com", "ugc", "User content platform"),
            ("https://marketplace-peer-to-peer.net", "marketplace", "P2P marketplace"),
            ("https://classified-ads-local.com", "classifieds", "Local classifieds"),
            ("https://second-hand-marketplace.net", "resale", "Resale marketplace"),
            ("https://dropshipping-store.com", "ecommerce", "Dropshipping"),
        ]

        for url, category, description in ambiguous:
            urls.append({
                "url": url,
                "ground_truth_label": "MANUAL_REVIEW_REQUIRED",
                "expected_category": "ambiguous",
                "description": description,
                "metadata": {
                    "subcategory": "ambiguous",
                    "category": category,
                    "reason": "Conflicting signals",
                    "test_purpose": "ambiguous_classification",
                    "difficulty": "hard",
                    "note": "Requires contextual analysis"
                }
            })

        # Limited data (10)
        limited_data = [
            ("https://private-membership-site.com", "private", "Private/members only"),
            ("https://access-restricted-content.net", "restricted", "Access restricted"),
            ("https://invitation-only-platform.com", "invite", "Invitation only"),
            ("https://beta-testing-closed.net", "beta", "Closed beta"),
            ("https://under-construction-page.com", "construction", "Under construction"),
            ("https://coming-soon-launch.net", "coming_soon", "Coming soon page"),
            ("https://temporary-landing-page.com", "temporary", "Temporary page"),
            ("https://redirect-placeholder.net", "redirect", "Redirect page"),
            ("https://parked-domain-page.com", "parked", "Parked domain"),
            ("https://dns-error-page.net", "error", "DNS error page"),
        ]

        for url, category, description in limited_data:
            urls.append({
                "url": url,
                "ground_truth_label": "MANUAL_REVIEW_REQUIRED",
                "expected_category": "limited_data",
                "description": description,
                "metadata": {
                    "subcategory": "limited_data",
                    "category": category,
                    "reason": "Insufficient technical data",
                    "test_purpose": "limited_data_handling",
                    "difficulty": "hard",
                    "note": "Cannot access or analyze content"
                }
            })

        logger.info(f"Generated {len(urls)} MANUAL_REVIEW_REQUIRED URLs")
        return urls

    def _create_ad_fraud_urls(self) -> List[Dict[str, Any]]:
        """Generate AD FRAUD URLs (40 URLs)"""
        urls = []

        # Cloaking (20)
        cloaking = [
            ("https://ad-shows-different-content.com", "cloaking", "Ad cloaking"),
            ("https://advertiser-redirect-chain.net", "redirect", "Redirect cloaking"),
            ("https://user-agent-detection.com", "detection", "UA detection"),
            ("https://geo-based-content-switch.net", "geo", "Geo cloaking"),
            ("https://bot-vs-human-content.com", "bot_detection", "Bot detection"),
            ("https://ad-platform-shows-different.net", "platform_cloak", "Platform cloaking"),
            ("https://landing-page-bait-switch.com", "bait_switch", "Bait and switch"),
            ("https://initial-compliant-then-redirect.net", "delayed_redirect", "Delayed redirect"),
            ("https://clean-ad-malicious-landing.com", "landing_page", "Malicious landing"),
            ("https://fake-product-page.net", "fake_product", "Fake product page"),
            ("https://misleading-advertisement.com", "misleading", "Misleading ad"),
            ("https://unrealistic-claims-ad.net", "false_claims", "False claims"),
            ("https://before-after-fake-results.com", "fake_results", "Fake results"),
            ("https://celebrity-endorsement-fake.net", "fake_endorsement", "Fake endorsement"),
            ("https://limited-time-offer-scam.com", "urgency_scam", "Urgency scam"),
            ("https://countdown-timer-pressure.net", "pressure", "Pressure tactics"),
            ("https://popup-trap-advertising.com", "popup_trap", "Popup trap"),
            ("https://click-bait-ad-content.net", "clickbait", "Clickbait ad"),
            ("https://forced-subscription-ad.com", "forced_sub", "Forced subscription"),
            ("https://hidden-charges-checkout.net", "hidden_fees", "Hidden fees"),
        ]

        for url, ad_fraud_type, description in cloaking:
            urls.append({
                "url": url,
                "ground_truth_label": "MALICIOUS",
                "expected_category": "ad_fraud",
                "description": description,
                "metadata": {
                    "subcategory": "ad_fraud_cloaking",
                    "fraud_type": ad_fraud_type,
                    "threat_indicators": ["ad_fraud", "cloaking", "deception"],
                    "test_purpose": "ad_fraud_detection",
                    "difficulty": "hard"
                }
            })

        # Click fraud (10)
        click_fraud = [
            ("https://auto-redirect-click.com", "auto_redirect", "Auto-redirect"),
            ("https://iframe-click-hijacking.net", "clickjacking", "Clickjacking"),
            ("https://invisible-overlay-click.com", "overlay", "Invisible overlay"),
            ("https://pop-under-ads.net", "popunder", "Pop-under ads"),
            ("https://forced-click-tracking.com", "forced_click", "Forced click"),
            ("https://cookie-stuffing-affiliate.net", "cookie_stuffing", "Cookie stuffing"),
            ("https://impression-fraud-bot.com", "impression_fraud", "Impression fraud"),
            ("https://click-farm-traffic.net", "click_farm", "Click farm"),
            ("https://bot-generated-clicks.com", "bot_clicks", "Bot clicks"),
            ("https://incentivized-clicks.net", "incentivized", "Incentivized clicks"),
        ]

        for url, fraud_type, description in click_fraud:
            urls.append({
                "url": url,
                "ground_truth_label": "MALICIOUS",
                "expected_category": "ad_fraud",
                "description": description,
                "metadata": {
                    "subcategory": "click_fraud",
                    "fraud_type": fraud_type,
                    "threat_indicators": ["ad_fraud", "click_fraud"],
                    "test_purpose": "click_fraud_detection",
                    "difficulty": "hard"
                }
            })

        # Arbitrage (10)
        arbitrage = [
            ("https://cheap-traffic-arbitrage.com", "traffic_arbitrage", "Traffic arbitrage"),
            ("https://ad-to-ad-redirect.net", "ad_redirect", "Ad-to-ad redirect"),
            ("https://low-quality-traffic.com", "low_quality", "Low quality traffic"),
            ("https://incentive-traffic-source.net", "incentive", "Incentive traffic"),
            ("https://bot-traffic-source.com", "bot_traffic", "Bot traffic"),
            ("https://expired-domain-traffic.net", "expired_domain", "Expired domain"),
            ("https://typo-traffic-monetization.com", "typo_traffic", "Typo traffic"),
            ("https://toolbar-redirect-traffic.net", "toolbar", "Toolbar traffic"),
            ("https://browser-extension-ads.com", "extension", "Extension ads"),
            ("https://notification-spam-ads.net", "notification", "Notification spam"),
        ]

        for url, fraud_type, description in arbitrage:
            urls.append({
                "url": url,
                "ground_truth_label": "SUSPICIOUS",
                "expected_category": "ad_fraud",
                "description": description,
                "metadata": {
                    "subcategory": "arbitrage",
                    "fraud_type": fraud_type,
                    "threat_indicators": ["ad_fraud", "low_quality_traffic"],
                    "test_purpose": "arbitrage_detection",
                    "difficulty": "hard"
                }
            })

        logger.info(f"Generated {len(urls)} AD FRAUD URLs")
        return urls

    def build_complete_dataset(self) -> List[Dict[str, Any]]:
        """
        Build complete 500-URL dataset

        Distribution:
        - SAFE: 170 URLs (34%)
        - MALICIOUS: 190 URLs (38%)
        - SUSPICIOUS: 90 URLs (18%)
        - MANUAL_REVIEW: 50 URLs (10%)
        """
        logger.info("Building complete 500-URL dataset...")

        all_urls = []

        # SAFE (170)
        all_urls.extend(self._create_safe_urls())

        # MALICIOUS (190)
        all_urls.extend(self._create_malicious_phishing_urls())  # 60
        all_urls.extend(self._create_malicious_scam_urls())  # 50
        all_urls.extend(self._create_malicious_malware_urls())  # 40
        all_urls.extend(self._create_ad_fraud_urls())  # 40

        # SUSPICIOUS (90)
        all_urls.extend(self._create_suspicious_urls())

        # MANUAL_REVIEW (50)
        all_urls.extend(self._create_manual_review_urls())

        logger.info(f"Total URLs generated: {len(all_urls)}")

        # Shuffle to mix categories
        random.shuffle(all_urls)

        self.dataset = all_urls
        return all_urls

    def get_dataset_statistics(self) -> Dict[str, Any]:
        """Get dataset statistics"""
        if not self.dataset:
            return {}

        stats = {
            "total": len(self.dataset),
            "by_label": {},
            "by_category": {},
            "by_difficulty": {},
            "by_subcategory": {}
        }

        for entry in self.dataset:
            # By label
            label = entry["ground_truth_label"]
            stats["by_label"][label] = stats["by_label"].get(label, 0) + 1

            # By category
            category = entry["expected_category"]
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1

            # By difficulty
            difficulty = entry["metadata"].get("difficulty", "unknown")
            stats["by_difficulty"][difficulty] = stats["by_difficulty"].get(difficulty, 0) + 1

            # By subcategory
            subcategory = entry["metadata"].get("subcategory", "unknown")
            stats["by_subcategory"][subcategory] = stats["by_subcategory"].get(subcategory, 0) + 1

        return stats

    def export_dataset(self, output_file: str):
        """Export dataset to JSON file"""
        if not self.dataset:
            logger.error("No dataset to export. Build dataset first.")
            return

        stats = self.get_dataset_statistics()

        export_data = {
            "dataset_name": "URL Safety Analysis - Comprehensive Evaluation Dataset",
            "version": "1.0",
            "created": datetime.utcnow().isoformat(),
            "total_urls": len(self.dataset),
            "statistics": stats,
            "test_cases": self.dataset
        }

        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Dataset exported to {output_file}")
        logger.info(f"Statistics:\n{json.dumps(stats, indent=2)}")

    async def cache_all_urls(self, max_concurrent: int = 5):
        """
        Cache all URLs in dataset

        Args:
            max_concurrent: Maximum concurrent fetches
        """
        if not self.dataset:
            logger.error("No dataset to cache. Build dataset first.")
            return

        logger.info(f"Caching {len(self.dataset)} URLs...")

        semaphore = asyncio.Semaphore(max_concurrent)
        cached_count = 0
        error_count = 0

        async def cache_single_url(entry: Dict[str, Any]):
            nonlocal cached_count, error_count

            async with semaphore:
                url = entry["url"]

                # Check if already cached
                if self.cache.has_cached(url):
                    logger.info(f"Already cached: {url}")
                    cached_count += 1
                    return

                try:
                    # Note: For synthetic/example URLs, we'll create placeholder cache entries
                    # In production, you would actually fetch these
                    logger.info(f"Creating cache entry for: {url}")

                    # Create synthetic cache entry
                    await self.cache.save_to_cache(
                        url=url,
                        status_code=200,
                        headers={"content-type": "text/html"},
                        content=f"<html><head><title>{entry['description']}</title></head><body><h1>{entry['description']}</h1></body></html>"
                    )

                    cached_count += 1
                    logger.info(f"Cached ({cached_count}/{len(self.dataset)}): {url}")

                except Exception as e:
                    error_count += 1
                    logger.error(f"Error caching {url}: {str(e)}")

        # Cache all URLs
        tasks = [cache_single_url(entry) for entry in self.dataset]
        await asyncio.gather(*tasks)

        logger.info(f"Caching complete. Cached: {cached_count}, Errors: {error_count}")


async def main():
    """Main entry point for dataset building"""
    builder = DatasetBuilder(cache_dir="./url_cache")

    # Build dataset
    logger.info("Step 1: Building dataset...")
    builder.build_complete_dataset()

    # Export dataset
    logger.info("\nStep 2: Exporting dataset...")
    builder.export_dataset("../test_datasets/comprehensive_test_dataset_500.json")

    # Cache URLs
    logger.info("\nStep 3: Caching URLs...")
    await builder.cache_all_urls(max_concurrent=10)

    # Export cache metadata
    logger.info("\nStep 4: Exporting cache metadata...")
    builder.cache.export_cache_metadata("../test_datasets/cache_metadata.json")

    logger.info("\n" + "="*80)
    logger.info("DATASET BUILDING COMPLETE")
    logger.info("="*80)
    logger.info(f"Dataset file: test_datasets/comprehensive_test_dataset_500.json")
    logger.info(f"Cache directory: url_cache/")
    logger.info(f"Cache metadata: test_datasets/cache_metadata.json")


if __name__ == "__main__":
    asyncio.run(main())
