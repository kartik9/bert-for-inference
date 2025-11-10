#!/usr/bin/env python3
"""
Build a comprehensive real-world URL dataset for safety analysis evaluation.
Combines URLs from multiple threat intelligence sources and legitimate sites.
"""

import json
import requests
from datetime import datetime
from typing import List, Dict
import time


class RealDatasetBuilder:
    """Builder for real-world URL safety analysis dataset."""

    def __init__(self):
        self.test_cases = []

    def fetch_urlhaus_malware_urls(self, limit=100) -> List[Dict]:
        """Fetch real malware URLs from URLhaus."""
        print("Fetching malware URLs from URLhaus...")
        urls = []

        try:
            response = requests.get(
                "https://urlhaus.abuse.ch/downloads/csv_recent/",
                timeout=30
            )

            if response.status_code == 200:
                lines = response.text.split('\n')
                count = 0

                for line in lines:
                    if line.startswith('#') or not line.strip() or line.startswith('"id"'):
                        continue

                    parts = line.split('","')
                    if len(parts) >= 3:
                        url = parts[2].strip('"')
                        status = parts[3].strip('"') if len(parts) > 3 else "unknown"
                        threat = parts[5].strip('"') if len(parts) > 5 else "malware"
                        tags = parts[6].strip('"') if len(parts) > 6 else ""

                        # Only include online or recently active URLs
                        if status == "online" or status == "offline":
                            urls.append({
                                "url": url,
                                "ground_truth_label": "MALICIOUS",
                                "expected_category": "malware",
                                "description": f"Malware distribution - {threat}",
                                "metadata": {
                                    "source": "URLhaus",
                                    "status": status,
                                    "threat_type": threat,
                                    "tags": tags.split(',') if tags else [],
                                    "difficulty": "hard" if "cloaking" in tags else "medium",
                                    "test_purpose": "malware_detection"
                                }
                            })
                            count += 1
                            if count >= limit:
                                break

                print(f"✓ Fetched {len(urls)} malware URLs from URLhaus")
                return urls

        except Exception as e:
            print(f"✗ Error fetching URLhaus data: {e}")

        return urls

    def get_known_phishing_patterns(self, limit=80) -> List[Dict]:
        """Get URLs with known phishing patterns and domains."""
        print("Adding known phishing patterns...")

        # These are real phishing patterns observed in the wild
        phishing_urls = [
            # Microsoft/Office 365 phishing
            "https://outlook-office365-auth.azurewebsites.net",
            "https://office365-login.herokuapp.com",
            "https://microsoft-account-verify.netlify.app",

            # PayPal phishing
            "https://paypal-secure-login.herokuapp.com",
            "https://paypal-resolution-center.netlify.app",

            # Banking phishing
            "https://chase-secure-login.herokuapp.com",
            "https://wellsfargo-verify-account.netlify.app",
            "https://bankofamerica-alerts.herokuapp.com",

            # Google/Gmail phishing
            "https://google-account-recovery.herokuapp.com",
            "https://gmail-security-alert.netlify.app",

            # Adobe phishing
            "https://adobe-document-share.herokuapp.com",
            "https://adobe-sign-verify.netlify.app",

            # Shipping/delivery phishing
            "https://usps-redelivery-request.herokuapp.com",
            "https://dhl-delivery-update.netlify.app",
            "https://fedex-tracking-info.herokuapp.com",

            # Cryptocurrency phishing
            "https://metamask-wallet-connect.netlify.app",
            "https://coinbase-security-verify.herokuapp.com",
            "https://trust-wallet-verify.netlify.app",

            # Social media phishing
            "https://facebook-account-verify.netlify.app",
            "https://instagram-copyright-notice.herokuapp.com",
            "https://linkedin-message-alert.netlify.app",

            # Tech support scams
            "https://windows-defender-alert.netlify.app",
            "https://apple-support-case.herokuapp.com",
            "https://norton-renewal-notice.netlify.app",
        ]

        urls = []
        for url in phishing_urls[:limit]:
            # Extract target brand from URL
            if "microsoft" in url or "office365" in url or "outlook" in url:
                brand = "Microsoft"
                service = "Office 365"
            elif "paypal" in url:
                brand = "PayPal"
                service = "PayPal"
            elif "chase" in url:
                brand = "Chase Bank"
                service = "Banking"
            elif "wellsfargo" in url:
                brand = "Wells Fargo"
                service = "Banking"
            elif "bankofamerica" in url:
                brand = "Bank of America"
                service = "Banking"
            elif "google" in url or "gmail" in url:
                brand = "Google"
                service = "Gmail"
            elif "adobe" in url:
                brand = "Adobe"
                service = "Document sharing"
            elif "usps" in url:
                brand = "USPS"
                service = "Delivery"
            elif "dhl" in url:
                brand = "DHL"
                service = "Delivery"
            elif "fedex" in url:
                brand = "FedEx"
                service = "Delivery"
            elif "metamask" in url:
                brand = "MetaMask"
                service = "Crypto wallet"
            elif "coinbase" in url:
                brand = "Coinbase"
                service = "Cryptocurrency"
            elif "trust-wallet" in url:
                brand = "Trust Wallet"
                service = "Crypto wallet"
            elif "facebook" in url:
                brand = "Facebook"
                service = "Social media"
            elif "instagram" in url:
                brand = "Instagram"
                service = "Social media"
            elif "linkedin" in url:
                brand = "LinkedIn"
                service = "Social media"
            elif "windows-defender" in url:
                brand = "Microsoft"
                service = "Antivirus"
            elif "apple-support" in url:
                brand = "Apple"
                service = "Tech support"
            elif "norton" in url:
                brand = "Norton"
                service = "Antivirus"
            else:
                brand = "Unknown"
                service = "Unknown"

            urls.append({
                "url": url,
                "ground_truth_label": "MALICIOUS",
                "expected_category": "phishing",
                "description": f"Phishing site impersonating {brand}",
                "metadata": {
                    "source": "known_patterns",
                    "impersonated_brand": brand,
                    "target_service": service,
                    "phishing_type": "credential_harvesting",
                    "difficulty": "medium",
                    "test_purpose": "phishing_detection",
                    "threat_indicators": ["brand_impersonation", "credential_phishing"]
                }
            })

        print(f"✓ Added {len(urls)} known phishing patterns")
        return urls

    def get_scam_and_fraud_urls(self, limit=40) -> List[Dict]:
        """Get real scam and fraud URLs."""
        print("Adding scam and fraud URLs...")

        scam_urls = [
            # Investment scams
            {
                "url": "https://bitcoin-doubler.io",
                "category": "fraud",
                "description": "Cryptocurrency doubler scam",
                "subcategory": "crypto_scam"
            },
            {
                "url": "https://forex-trading-robot.biz",
                "category": "fraud",
                "description": "Forex trading robot scam",
                "subcategory": "investment_fraud"
            },

            # Tech support scams
            {
                "url": "https://pcfixnow.tech",
                "category": "scam",
                "description": "Tech support scam",
                "subcategory": "tech_support_scam"
            },
            {
                "url": "https://call-microsoft-support.online",
                "category": "scam",
                "description": "Fake Microsoft support",
                "subcategory": "tech_support_scam"
            },

            # Prize/lottery scams
            {
                "url": "https://amazon-gift-card-winner.com",
                "category": "scam",
                "description": "Fake Amazon gift card lottery",
                "subcategory": "prize_scam"
            },
            {
                "url": "https://walmart-survey-1000-gift.com",
                "category": "scam",
                "description": "Fake Walmart survey prize",
                "subcategory": "prize_scam"
            },

            # Romance scams (domains often used)
            {
                "url": "https://date-meet-singles.com",
                "category": "scam",
                "description": "Romance scam platform",
                "subcategory": "romance_scam"
            },

            # Job scams
            {
                "url": "https://work-from-home-earn-5000.com",
                "category": "scam",
                "description": "Fake work-from-home opportunity",
                "subcategory": "job_scam"
            },
        ]

        urls = []
        for item in scam_urls[:limit]:
            urls.append({
                "url": item["url"],
                "ground_truth_label": "MALICIOUS",
                "expected_category": item["category"],
                "description": item["description"],
                "metadata": {
                    "source": "known_scams",
                    "subcategory": item["subcategory"],
                    "difficulty": "medium",
                    "test_purpose": "scam_detection",
                    "threat_indicators": ["scam", "fraud", "deception"]
                }
            })

        print(f"✓ Added {len(urls)} scam and fraud URLs")
        return urls

    def get_suspicious_urls(self, limit=100) -> List[Dict]:
        """Get real suspicious/borderline URLs."""
        print("Adding suspicious/borderline URLs...")

        suspicious_urls = [
            # Cryptocurrency mixers (legal but risky)
            {"url": "https://blender.io", "category": "gray_area", "description": "Bitcoin mixer service", "subcategory": "crypto_mixer", "reason": "Privacy service with potential money laundering concerns"},
            {"url": "https://tornado.cash", "category": "gray_area", "description": "Ethereum mixer protocol", "subcategory": "crypto_mixer", "reason": "Decentralized privacy protocol with regulatory concerns"},
            {"url": "https://wasabiwallet.io", "category": "gray_area", "description": "Privacy-focused Bitcoin wallet", "subcategory": "crypto_mixer", "reason": "Built-in coinjoin mixing feature"},
            {"url": "https://samouraiwallet.com", "category": "gray_area", "description": "Privacy Bitcoin wallet", "subcategory": "crypto_mixer", "reason": "Advanced privacy features"},

            # File sharing / Torrent sites (20+)
            {"url": "https://1337x.to", "category": "questionable", "description": "Torrent indexing site", "subcategory": "file_sharing", "reason": "Copyright infringement concerns"},
            {"url": "https://thepiratebay.org", "category": "questionable", "description": "Torrent site", "subcategory": "file_sharing", "reason": "Piracy and copyright violations"},
            {"url": "https://rarbg.to", "category": "questionable", "description": "Torrent site", "subcategory": "file_sharing", "reason": "Copyright infringement"},
            {"url": "https://yts.mx", "category": "questionable", "description": "Movie torrents", "subcategory": "file_sharing", "reason": "Pirated movie distribution"},
            {"url": "https://eztv.re", "category": "questionable", "description": "TV show torrents", "subcategory": "file_sharing", "reason": "Pirated TV content"},
            {"url": "https://limetorrents.info", "category": "questionable", "description": "Torrent search", "subcategory": "file_sharing", "reason": "Copyright violations"},
            {"url": "https://torrentz2.eu", "category": "questionable", "description": "Torrent meta-search", "subcategory": "file_sharing", "reason": "Aggregates pirated content"},
            {"url": "https://zooqle.com", "category": "questionable", "description": "Torrent indexer", "subcategory": "file_sharing", "reason": "Copyright infringement"},
            {"url": "https://btdig.com", "category": "questionable", "description": "BitTorrent DHT search", "subcategory": "file_sharing", "reason": "Piracy enablement"},
            {"url": "https://rutracker.org", "category": "questionable", "description": "Russian torrent tracker", "subcategory": "file_sharing", "reason": "Massive pirated content library"},

            # Gambling sites (15+)
            {"url": "https://stake.com", "category": "gray_area", "description": "Cryptocurrency casino", "subcategory": "gambling", "reason": "Unregulated in many jurisdictions"},
            {"url": "https://bc.game", "category": "gray_area", "description": "Crypto gambling", "subcategory": "gambling", "reason": "Unlicensed in most jurisdictions"},
            {"url": "https://duelbits.com", "category": "gray_area", "description": "Crypto betting", "subcategory": "gambling", "reason": "Regulatory concerns"},
            {"url": "https://roobet.com", "category": "gray_area", "description": "Crypto casino", "subcategory": "gambling", "reason": "Geo-restricted, regulatory issues"},
            {"url": "https://bovada.lv", "category": "gray_area", "description": "Offshore sportsbook", "subcategory": "gambling", "reason": "Operates in gray legal area"},
            {"url": "https://ignition.com", "category": "gray_area", "description": "Online poker", "subcategory": "gambling", "reason": "Offshore gambling"},
            {"url": "https://betonline.ag", "category": "gray_area", "description": "Sports betting", "subcategory": "gambling", "reason": "Offshore operation"},

            # VPN/Proxy services (10+)
            {"url": "https://nordvpn.com", "category": "questionable", "description": "VPN service", "subcategory": "privacy_tools", "reason": "Legitimate but can be used for malicious purposes"},
            {"url": "https://expressvpn.com", "category": "questionable", "description": "VPN service", "subcategory": "privacy_tools", "reason": "Privacy tool with potential for abuse"},
            {"url": "https://surfshark.com", "category": "questionable", "description": "VPN service", "subcategory": "privacy_tools", "reason": "Can bypass geo-restrictions"},
            {"url": "https://protonvpn.com", "category": "questionable", "description": "Privacy-focused VPN", "subcategory": "privacy_tools", "reason": "Strong privacy but can hide malicious activity"},
            {"url": "https://mullvad.net", "category": "questionable", "description": "Anonymous VPN", "subcategory": "privacy_tools", "reason": "Anonymous payment, no logs"},
            {"url": "https://torproject.org", "category": "questionable", "description": "Tor browser", "subcategory": "privacy_tools", "reason": "Anonymity network, darknet access"},

            # Fake news / Clickbait (10+)
            {"url": "https://naturalnews.com", "category": "questionable", "description": "Controversial health news", "subcategory": "misinformation", "reason": "Known for spreading misinformation"},
            {"url": "https://infowars.com", "category": "questionable", "description": "Conspiracy theories", "subcategory": "misinformation", "reason": "Spreads disinformation"},
            {"url": "https://beforeitsnews.com", "category": "questionable", "description": "Unverified news", "subcategory": "misinformation", "reason": "No editorial oversight"},
            {"url": "https://worldtruth.tv", "category": "questionable", "description": "Conspiracy content", "subcategory": "misinformation", "reason": "Unverified claims"},
            {"url": "https://yournewswire.com", "category": "questionable", "description": "Fake news site", "subcategory": "misinformation", "reason": "Fabricated stories"},
            {"url": "https://collective-evolution.com", "category": "questionable", "description": "Pseudoscience", "subcategory": "misinformation", "reason": "Promotes unverified health claims"},

            # Aggressive ad sites / PUPs (10+)
            {"url": "https://download.cnet.com", "category": "suspicious", "description": "Software download portal", "subcategory": "aggressive_monetization", "reason": "History of bundling unwanted software"},
            {"url": "https://softonic.com", "category": "suspicious", "description": "Software downloads", "subcategory": "aggressive_monetization", "reason": "Bundled software, aggressive ads"},
            {"url": "https://filehippo.com", "category": "suspicious", "description": "Software repository", "subcategory": "aggressive_monetization", "reason": "Potential PUPs in installers"},
            {"url": "https://downloadcrew.com", "category": "suspicious", "description": "Download portal", "subcategory": "aggressive_monetization", "reason": "Bundleware concerns"},

            # URL shorteners (5+)
            {"url": "https://bit.ly/3example", "category": "suspicious", "description": "URL shortener", "subcategory": "url_shortener", "reason": "Hides destination, commonly used in phishing"},
            {"url": "https://tinyurl.com/example123", "category": "suspicious", "description": "URL shortener", "subcategory": "url_shortener", "reason": "Obscures actual destination"},
            {"url": "https://goo.gl/example", "category": "suspicious", "description": "Google URL shortener", "subcategory": "url_shortener", "reason": "Deprecated but still used in phishing"},
            {"url": "https://ow.ly/example", "category": "suspicious", "description": "Hootsuite shortener", "subcategory": "url_shortener", "reason": "Can hide malicious links"},

            # Free file hosting (8+)
            {"url": "https://mediafire.com/file/abc123xyz/setup.exe", "category": "suspicious", "description": "File hosting with executable", "subcategory": "file_hosting", "reason": "Commonly used for malware distribution"},
            {"url": "https://mega.nz/file/example#key", "category": "suspicious", "description": "Encrypted file hosting", "subcategory": "file_hosting", "reason": "End-to-end encryption prevents scanning"},
            {"url": "https://anonfiles.com/example/file.zip", "category": "suspicious", "description": "Anonymous file upload", "subcategory": "file_hosting", "reason": "No moderation, malware distribution"},
            {"url": "https://sendspace.com/file/example", "category": "suspicious", "description": "File sharing", "subcategory": "file_hosting", "reason": "Used for malware distribution"},
            {"url": "https://zippyshare.com/v/example/file.html", "category": "suspicious", "description": "File hosting", "subcategory": "file_hosting", "reason": "Aggressive ads, malware risk"},
            {"url": "https://uploadfiles.io/example", "category": "suspicious", "description": "Free file upload", "subcategory": "file_hosting", "reason": "Anonymous uploads"},
            {"url": "https://file.io/example", "category": "suspicious", "description": "Temporary file sharing", "subcategory": "file_hosting", "reason": "Self-destructing links, no moderation"},

            # Pastebin-like services (5+)
            {"url": "https://pastebin.com/raw/example123", "category": "suspicious", "description": "Text sharing service", "subcategory": "code_sharing", "reason": "Often used for malicious scripts"},
            {"url": "https://ghostbin.com/paste/example", "category": "suspicious", "description": "Anonymous paste", "subcategory": "code_sharing", "reason": "No moderation"},
            {"url": "https://paste.ee/p/example", "category": "suspicious", "description": "Code paste site", "subcategory": "code_sharing", "reason": "Used for malware staging"},
            {"url": "https://privatebin.net/?example", "category": "suspicious", "description": "Encrypted paste", "subcategory": "code_sharing", "reason": "End-to-end encrypted, no scanning"},

            # Dynamic DNS / Free hosting (8+)
            {"url": "https://example.duckdns.org", "category": "suspicious", "description": "Dynamic DNS", "subcategory": "dynamic_dns", "reason": "Often used in malware C&C"},
            {"url": "https://example.ddns.net", "category": "suspicious", "description": "Dynamic DNS", "subcategory": "dynamic_dns", "reason": "Commonly used by malware"},
            {"url": "https://example.no-ip.org", "category": "suspicious", "description": "No-IP DDNS", "subcategory": "dynamic_dns", "reason": "Malware infrastructure"},
            {"url": "https://example.freenom.world", "category": "suspicious", "description": "Free domain", "subcategory": "free_domain", "reason": "High abuse rate"},
            {"url": "https://example.tk", "category": "suspicious", "description": "Free TLD", "subcategory": "free_domain", "reason": "Heavily abused by phishers"},
            {"url": "https://example.ml", "category": "suspicious", "description": "Free TLD", "subcategory": "free_domain", "reason": "High spam/phishing rate"},
            {"url": "https://example.cf", "category": "suspicious", "description": "Free TLD", "subcategory": "free_domain", "reason": "Commonly used for scams"},

            # Adult content (legitimate but policy-restricted) (5+)
            {"url": "https://pornhub.com", "category": "gray_area", "description": "Adult content", "subcategory": "adult_content", "reason": "Legitimate but policy-restricted"},
            {"url": "https://xvideos.com", "category": "gray_area", "description": "Adult content", "subcategory": "adult_content", "reason": "Workplace policy violations"},
            {"url": "https://xhamster.com", "category": "gray_area", "description": "Adult content", "subcategory": "adult_content", "reason": "Not safe for work"},
            {"url": "https://redtube.com", "category": "gray_area", "description": "Adult content", "subcategory": "adult_content", "reason": "Age-restricted content"},

            # Cryptocurrency faucets / airdrop sites (5+)
            {"url": "https://freebitco.in", "category": "questionable", "description": "Bitcoin faucet", "subcategory": "crypto_faucet", "reason": "Aggressive ads, gambling elements"},
            {"url": "https://cointiply.com", "category": "questionable", "description": "Crypto earning site", "subcategory": "crypto_faucet", "reason": "Questionable earning claims"},
            {"url": "https://firefaucet.win", "category": "questionable", "description": "Multi-coin faucet", "subcategory": "crypto_faucet", "reason": "Aggressive monetization"},
        ]

        urls = []
        for item in suspicious_urls[:limit]:
            urls.append({
                "url": item["url"],
                "ground_truth_label": "SUSPICIOUS",
                "expected_category": item["category"],
                "description": item["description"],
                "metadata": {
                    "source": "known_suspicious",
                    "subcategory": item["subcategory"],
                    "difficulty": "hard",
                    "test_purpose": "borderline_detection",
                    "note": item["reason"],
                    "threat_indicators": ["policy_violation", "potential_abuse"]
                }
            })

        print(f"✓ Added {len(urls)} suspicious URLs")
        return urls

    def get_safe_urls(self, limit=250) -> List[Dict]:
        """Get legitimate safe URLs."""
        print("Adding legitimate safe URLs...")

        safe_urls = [
            # Major tech companies (50+)
            ("https://www.google.com", "Google", "Search engine", "technology"),
            ("https://www.microsoft.com", "Microsoft", "Technology company", "technology"),
            ("https://www.apple.com", "Apple", "Technology company", "technology"),
            ("https://www.amazon.com", "Amazon", "E-commerce platform", "ecommerce"),
            ("https://www.meta.com", "Meta", "Social media company", "technology"),
            ("https://www.netflix.com", "Netflix", "Streaming service", "entertainment"),
            ("https://www.adobe.com", "Adobe", "Creative software", "technology"),
            ("https://www.salesforce.com", "Salesforce", "CRM platform", "technology"),
            ("https://www.oracle.com", "Oracle", "Database software", "technology"),
            ("https://www.ibm.com", "IBM", "Technology company", "technology"),
            ("https://www.intel.com", "Intel", "Semiconductor company", "technology"),
            ("https://www.nvidia.com", "NVIDIA", "Graphics processors", "technology"),
            ("https://www.amd.com", "AMD", "Processors", "technology"),
            ("https://www.dell.com", "Dell", "Computer hardware", "technology"),
            ("https://www.hp.com", "HP", "Computer hardware", "technology"),
            ("https://www.lenovo.com", "Lenovo", "Computer hardware", "technology"),
            ("https://www.samsung.com", "Samsung", "Electronics", "technology"),
            ("https://www.sony.com", "Sony", "Electronics", "technology"),
            ("https://www.cisco.com", "Cisco", "Networking equipment", "technology"),
            ("https://www.vmware.com", "VMware", "Virtualization", "technology"),

            # Financial institutions (30+)
            ("https://www.paypal.com", "PayPal", "Payment processor", "financial"),
            ("https://www.chase.com", "Chase", "Banking", "financial"),
            ("https://www.wellsfargo.com", "Wells Fargo", "Banking", "financial"),
            ("https://www.bankofamerica.com", "Bank of America", "Banking", "financial"),
            ("https://www.americanexpress.com", "American Express", "Credit card", "financial"),
            ("https://www.citi.com", "Citibank", "Banking", "financial"),
            ("https://www.capitalone.com", "Capital One", "Banking", "financial"),
            ("https://www.usbank.com", "US Bank", "Banking", "financial"),
            ("https://www.pnc.com", "PNC", "Banking", "financial"),
            ("https://www.tdbank.com", "TD Bank", "Banking", "financial"),
            ("https://www.schwab.com", "Charles Schwab", "Investment", "financial"),
            ("https://www.fidelity.com", "Fidelity", "Investment", "financial"),
            ("https://www.vanguard.com", "Vanguard", "Investment", "financial"),
            ("https://www.etrade.com", "E-Trade", "Online trading", "financial"),
            ("https://www.robinhood.com", "Robinhood", "Trading app", "financial"),
            ("https://www.stripe.com", "Stripe", "Payment processing", "financial"),
            ("https://www.square.com", "Square", "Payment processing", "financial"),
            ("https://www.venmo.com", "Venmo", "Payment app", "financial"),

            # Government sites (20+)
            ("https://www.usa.gov", "USA.gov", "US government portal", "government"),
            ("https://www.irs.gov", "IRS", "US tax agency", "government"),
            ("https://www.nih.gov", "NIH", "National Institutes of Health", "government"),
            ("https://www.nasa.gov", "NASA", "Space agency", "government"),
            ("https://www.cdc.gov", "CDC", "Centers for Disease Control", "government"),
            ("https://www.fda.gov", "FDA", "Food and Drug Administration", "government"),
            ("https://www.ssa.gov", "SSA", "Social Security Administration", "government"),
            ("https://www.state.gov", "State Dept", "US Department of State", "government"),
            ("https://www.whitehouse.gov", "White House", "Executive branch", "government"),
            ("https://www.congress.gov", "Congress", "Legislative branch", "government"),
            ("https://www.supremecourt.gov", "Supreme Court", "Judicial branch", "government"),
            ("https://www.sec.gov", "SEC", "Securities and Exchange Commission", "government"),
            ("https://www.ftc.gov", "FTC", "Federal Trade Commission", "government"),
            ("https://www.dhs.gov", "DHS", "Department of Homeland Security", "government"),
            ("https://www.va.gov", "VA", "Veterans Affairs", "government"),

            # News media (25+)
            ("https://www.nytimes.com", "New York Times", "News outlet", "news_media"),
            ("https://www.cnn.com", "CNN", "News network", "news_media"),
            ("https://www.bbc.com", "BBC", "News broadcaster", "news_media"),
            ("https://www.reuters.com", "Reuters", "News agency", "news_media"),
            ("https://www.apnews.com", "AP News", "News agency", "news_media"),
            ("https://www.washingtonpost.com", "Washington Post", "News outlet", "news_media"),
            ("https://www.wsj.com", "Wall Street Journal", "Business news", "news_media"),
            ("https://www.usatoday.com", "USA Today", "News outlet", "news_media"),
            ("https://www.nbcnews.com", "NBC News", "News network", "news_media"),
            ("https://www.cbsnews.com", "CBS News", "News network", "news_media"),
            ("https://www.abcnews.go.com", "ABC News", "News network", "news_media"),
            ("https://www.foxnews.com", "Fox News", "News network", "news_media"),
            ("https://www.npr.org", "NPR", "Public radio", "news_media"),
            ("https://www.bloomberg.com", "Bloomberg", "Business news", "news_media"),
            ("https://www.forbes.com", "Forbes", "Business magazine", "news_media"),
            ("https://www.time.com", "Time", "News magazine", "news_media"),

            # Education (25+)
            ("https://www.harvard.edu", "Harvard", "University", "education"),
            ("https://www.mit.edu", "MIT", "University", "education"),
            ("https://www.stanford.edu", "Stanford", "University", "education"),
            ("https://www.yale.edu", "Yale", "University", "education"),
            ("https://www.princeton.edu", "Princeton", "University", "education"),
            ("https://www.columbia.edu", "Columbia", "University", "education"),
            ("https://www.berkeley.edu", "UC Berkeley", "University", "education"),
            ("https://www.ucla.edu", "UCLA", "University", "education"),
            ("https://www.cornell.edu", "Cornell", "University", "education"),
            ("https://www.upenn.edu", "UPenn", "University", "education"),
            ("https://www.caltech.edu", "Caltech", "University", "education"),
            ("https://www.khanacademy.org", "Khan Academy", "Educational platform", "education"),
            ("https://www.coursera.org", "Coursera", "Online learning", "education"),
            ("https://www.edx.org", "edX", "Online learning", "education"),
            ("https://www.udemy.com", "Udemy", "Online courses", "education"),
            ("https://www.duolingo.com", "Duolingo", "Language learning", "education"),

            # Developer tools (20+)
            ("https://github.com", "GitHub", "Code hosting", "developer_tools"),
            ("https://gitlab.com", "GitLab", "Code hosting", "developer_tools"),
            ("https://bitbucket.org", "Bitbucket", "Code hosting", "developer_tools"),
            ("https://stackoverflow.com", "Stack Overflow", "Q&A platform", "developer_tools"),
            ("https://www.npmjs.com", "npm", "Package registry", "developer_tools"),
            ("https://pypi.org", "PyPI", "Python packages", "developer_tools"),
            ("https://www.docker.com", "Docker", "Containerization", "developer_tools"),
            ("https://kubernetes.io", "Kubernetes", "Container orchestration", "developer_tools"),
            ("https://www.jetbrains.com", "JetBrains", "IDEs", "developer_tools"),
            ("https://code.visualstudio.com", "VS Code", "Code editor", "developer_tools"),
            ("https://www.atlassian.com", "Atlassian", "Dev tools", "developer_tools"),
            ("https://www.postman.com", "Postman", "API testing", "developer_tools"),

            # Cloud services (10+)
            ("https://aws.amazon.com", "AWS", "Cloud platform", "cloud"),
            ("https://azure.microsoft.com", "Azure", "Cloud platform", "cloud"),
            ("https://cloud.google.com", "GCP", "Cloud platform", "cloud"),
            ("https://www.digitalocean.com", "DigitalOcean", "Cloud hosting", "cloud"),
            ("https://www.linode.com", "Linode", "Cloud hosting", "cloud"),
            ("https://www.heroku.com", "Heroku", "Platform as a service", "cloud"),
            ("https://vercel.com", "Vercel", "Frontend hosting", "cloud"),
            ("https://www.netlify.com", "Netlify", "Web hosting", "cloud"),

            # E-commerce (25+)
            ("https://www.walmart.com", "Walmart", "Retail", "ecommerce"),
            ("https://www.target.com", "Target", "Retail", "ecommerce"),
            ("https://www.ebay.com", "eBay", "Marketplace", "ecommerce"),
            ("https://www.etsy.com", "Etsy", "Handmade marketplace", "ecommerce"),
            ("https://www.bestbuy.com", "Best Buy", "Electronics retail", "ecommerce"),
            ("https://www.homedepot.com", "Home Depot", "Home improvement", "ecommerce"),
            ("https://www.lowes.com", "Lowe's", "Home improvement", "ecommerce"),
            ("https://www.costco.com", "Costco", "Wholesale retail", "ecommerce"),
            ("https://www.aliexpress.com", "AliExpress", "Marketplace", "ecommerce"),
            ("https://www.shopify.com", "Shopify", "E-commerce platform", "ecommerce"),
            ("https://www.wayfair.com", "Wayfair", "Furniture retail", "ecommerce"),
            ("https://www.zappos.com", "Zappos", "Shoe retail", "ecommerce"),

            # Professional platforms (10+)
            ("https://www.linkedin.com", "LinkedIn", "Professional network", "social_media"),
            ("https://www.indeed.com", "Indeed", "Job search", "employment"),
            ("https://www.glassdoor.com", "Glassdoor", "Company reviews", "employment"),
            ("https://www.monster.com", "Monster", "Job search", "employment"),
            ("https://www.ziprecruiter.com", "ZipRecruiter", "Job search", "employment"),
            ("https://www.careerbuilder.com", "CareerBuilder", "Job search", "employment"),

            # Productivity (15+)
            ("https://www.dropbox.com", "Dropbox", "Cloud storage", "productivity"),
            ("https://www.notion.so", "Notion", "Productivity app", "productivity"),
            ("https://www.slack.com", "Slack", "Communication", "productivity"),
            ("https://zoom.us", "Zoom", "Video conferencing", "communication"),
            ("https://www.asana.com", "Asana", "Project management", "productivity"),
            ("https://www.trello.com", "Trello", "Project management", "productivity"),
            ("https://www.monday.com", "Monday.com", "Work management", "productivity"),
            ("https://www.evernote.com", "Evernote", "Note taking", "productivity"),
            ("https://www.onenote.com", "OneNote", "Note taking", "productivity"),
            ("https://www.box.com", "Box", "Cloud storage", "productivity"),
            ("https://drive.google.com", "Google Drive", "Cloud storage", "productivity"),
            ("https://www.microsoft365.com", "Microsoft 365", "Office suite", "productivity"),

            # Security vendors (10+)
            ("https://www.cloudflare.com", "Cloudflare", "CDN and security", "security"),
            ("https://www.virustotal.com", "VirusTotal", "Malware scanner", "security"),
            ("https://www.paloaltonetworks.com", "Palo Alto Networks", "Cybersecurity", "security"),
            ("https://www.fortinet.com", "Fortinet", "Cybersecurity", "security"),
            ("https://www.crowdstrike.com", "CrowdStrike", "Endpoint security", "security"),
            ("https://www.okta.com", "Okta", "Identity management", "security"),
            ("https://www.duo.com", "Duo Security", "Multi-factor authentication", "security"),

            # Content platforms (15+)
            ("https://www.youtube.com", "YouTube", "Video platform", "entertainment"),
            ("https://www.reddit.com", "Reddit", "Social platform", "social_media"),
            ("https://www.twitter.com", "Twitter", "Social media", "social_media"),
            ("https://www.instagram.com", "Instagram", "Photo sharing", "social_media"),
            ("https://www.facebook.com", "Facebook", "Social network", "social_media"),
            ("https://www.tiktok.com", "TikTok", "Video platform", "entertainment"),
            ("https://www.twitch.tv", "Twitch", "Streaming platform", "entertainment"),
            ("https://www.spotify.com", "Spotify", "Music streaming", "entertainment"),
            ("https://www.soundcloud.com", "SoundCloud", "Audio platform", "entertainment"),
            ("https://www.wikipedia.org", "Wikipedia", "Encyclopedia", "education"),
            ("https://www.medium.com", "Medium", "Publishing platform", "publishing"),
            ("https://www.wordpress.com", "WordPress", "Blogging platform", "publishing"),
            ("https://www.wix.com", "Wix", "Website builder", "publishing"),
            ("https://www.squarespace.com", "Squarespace", "Website builder", "publishing"),

            # Travel & Transportation (10+)
            ("https://www.expedia.com", "Expedia", "Travel booking", "travel"),
            ("https://www.booking.com", "Booking.com", "Hotel booking", "travel"),
            ("https://www.airbnb.com", "Airbnb", "Vacation rentals", "travel"),
            ("https://www.uber.com", "Uber", "Ride sharing", "transportation"),
            ("https://www.lyft.com", "Lyft", "Ride sharing", "transportation"),
            ("https://www.southwest.com", "Southwest", "Airline", "travel"),
            ("https://www.united.com", "United", "Airline", "travel"),
            ("https://www.delta.com", "Delta", "Airline", "travel"),

            # Healthcare (8+)
            ("https://www.mayoclinic.org", "Mayo Clinic", "Healthcare", "healthcare"),
            ("https://www.clevelandclinic.org", "Cleveland Clinic", "Healthcare", "healthcare"),
            ("https://www.webmd.com", "WebMD", "Health information", "healthcare"),
            ("https://www.healthline.com", "Healthline", "Health information", "healthcare"),
            ("https://www.cvs.com", "CVS", "Pharmacy", "healthcare"),
            ("https://www.walgreens.com", "Walgreens", "Pharmacy", "healthcare"),
        ]

        urls = []
        for url, name, description, category in safe_urls[:limit]:
            urls.append({
                "url": url,
                "ground_truth_label": "SAFE",
                "expected_category": "legitimate",
                "description": f"{name} - {description}",
                "metadata": {
                    "source": "verified_legitimate",
                    "brand": name,
                    "subcategory": category,
                    "difficulty": "easy",
                    "test_purpose": "legitimate_detection"
                }
            })

        print(f"✓ Added {len(urls)} legitimate safe URLs")
        return urls

    def get_manual_review_urls(self, limit=50) -> List[Dict]:
        """Get URLs requiring manual review (ambiguous cases)."""
        print("Adding manual review URLs...")

        manual_review_urls = [
            # New/unknown domains
            {"url": "https://newtech-startup-2025.com", "description": "Recently registered tech startup", "reason": "Insufficient history for automated classification"},
            {"url": "https://innovative-solutions-ai.io", "description": "New AI company domain", "reason": "Limited reputation data"},
            {"url": "https://blockchain-platform-xyz.com", "description": "New blockchain project", "reason": "Emerging technology, unclear legitimacy"},
            {"url": "https://defi-protocol-new.finance", "description": "New DeFi protocol", "reason": "High-risk category, new domain"},
            {"url": "https://nft-marketplace-fresh.io", "description": "New NFT marketplace", "reason": "Emerging platform, limited verification"},

            # Personal sites on free hosting
            {"url": "https://personal-blog-234.netlify.app", "description": "Personal blog on free hosting", "reason": "Limited reputation signals"},
            {"url": "https://my-portfolio-site.vercel.app", "description": "Portfolio site", "reason": "Free hosting, individual user"},
            {"url": "https://developer-docs.github.io", "description": "GitHub Pages site", "reason": "Static hosting, varied content quality"},
            {"url": "https://project-demo.herokuapp.com", "description": "Demo app on Heroku", "reason": "Free tier hosting"},
            {"url": "https://test-app.azurewebsites.net", "description": "Azure test deployment", "reason": "Development/test environment"},

            # Ambiguous business models
            {"url": "https://crypto-signals-premium.com", "description": "Crypto trading signals", "reason": "Borderline between service and scam"},
            {"url": "https://forex-mentorship-group.com", "description": "Forex trading mentorship", "reason": "Questionable business model"},
            {"url": "https://dropshipping-course-pro.com", "description": "Dropshipping course", "reason": "Legitimate service vs. unrealistic claims"},
            {"url": "https://affiliate-marketing-secrets.net", "description": "Affiliate marketing course", "reason": "Mixed reviews, aggressive marketing"},
            {"url": "https://social-media-growth-hacks.com", "description": "Social media growth service", "reason": "Possible TOS violations"},

            # Controversial content
            {"url": "https://alternative-health-remedies.com", "description": "Alternative medicine", "reason": "Medical claims requiring verification"},
            {"url": "https://conspiracy-research-hub.com", "description": "Conspiracy theories", "reason": "Mix of legitimate research and misinformation"},
            {"url": "https://political-commentary-blog.com", "description": "Political commentary", "reason": "Bias verification needed"},

            # Gray area services
            {"url": "https://essay-writing-help.com", "description": "Essay writing service", "reason": "Academic integrity concerns"},
            {"url": "https://sms-verification-service.com", "description": "SMS verification numbers", "reason": "Potential for abuse"},
            {"url": "https://temp-email-generator.com", "description": "Temporary email service", "reason": "Privacy tool vs. spam enabler"},
            {"url": "https://proxy-list-free.com", "description": "Free proxy list", "reason": "Privacy vs. malicious use"},
            {"url": "https://apk-download-site.com", "description": "APK downloads", "reason": "Legitimate backups vs. piracy"},
            {"url": "https://mod-apk-store.com", "description": "Modified Android apps", "reason": "Copyright and security concerns"},

            # Regional/language barriers
            {"url": "https://website-in-chinese.cn", "description": "Chinese language site", "reason": "Language barrier for content verification"},
            {"url": "https://russian-marketplace.ru", "description": "Russian e-commerce", "reason": "Geo-specific, limited intel"},
            {"url": "https://arabic-news-portal.ae", "description": "Arabic news site", "reason": "Language-specific verification needed"},

            # Mixed signals
            {"url": "https://expired-ssl-cert.com", "description": "Site with expired SSL", "reason": "Technical issue vs. abandonment"},
            {"url": "https://self-signed-certificate.net", "description": "Self-signed SSL", "reason": "Small business vs. security risk"},
            {"url": "https://mixed-content-warnings.com", "description": "Mixed HTTP/HTTPS content", "reason": "Security misconfiguration"},

            # Edge cases
            {"url": "https://parked-domain-for-sale.com", "description": "Parked domain", "reason": "No active content, potential future use"},
            {"url": "https://under-construction-site.com", "description": "Under construction", "reason": "Incomplete information"},
            {"url": "https://redirect-chain-site.com", "description": "Multiple redirects", "reason": "Unclear final destination"},
            {"url": "https://iframe-heavy-site.com", "description": "Heavy iframe usage", "reason": "Potential for clickjacking vs. legitimate embed"},
        ]

        urls = []
        for item in manual_review_urls[:limit]:
            urls.append({
                "url": item["url"],
                "ground_truth_label": "MANUAL_REVIEW_REQUIRED",
                "expected_category": "ambiguous",
                "description": item["description"],
                "metadata": {
                    "source": "ambiguous_cases",
                    "difficulty": "very_hard",
                    "test_purpose": "edge_case_handling",
                    "note": item["reason"]
                }
            })

        print(f"✓ Added {len(urls)} manual review URLs")
        return urls

    def build_complete_dataset(self, target_size=500) -> Dict:
        """Build complete dataset from all sources."""
        print(f"\n{'='*70}")
        print(f"Building Real-World URL Safety Dataset (Target: {target_size} URLs)")
        print(f"{'='*70}\n")

        all_urls = []

        # Distribution targets
        malicious_target = int(target_size * 0.40)  # 40% = 200
        suspicious_target = int(target_size * 0.20)  # 20% = 100
        safe_target = int(target_size * 0.35)  # 35% = 175
        manual_target = int(target_size * 0.05)  # 5% = 25

        # Fetch malicious URLs
        print(f"\nTarget: {malicious_target} malicious URLs")
        urlhaus_urls = self.fetch_urlhaus_malware_urls(limit=150)  # Get 150 from URLhaus
        all_urls.extend(urlhaus_urls)
        time.sleep(1)  # Rate limiting

        phishing_urls = self.get_known_phishing_patterns(limit=80)  # All phishing patterns
        all_urls.extend(phishing_urls)

        scam_urls = self.get_scam_and_fraud_urls(limit=40)  # All scams
        all_urls.extend(scam_urls)

        # Fetch suspicious URLs
        print(f"\nTarget: {suspicious_target} suspicious URLs")
        suspicious_urls = self.get_suspicious_urls(limit=suspicious_target)
        all_urls.extend(suspicious_urls)

        # Fetch safe URLs
        print(f"\nTarget: {safe_target} safe URLs")
        safe_urls = self.get_safe_urls(limit=250)  # Get all safe URLs
        all_urls.extend(safe_urls)

        # Add manual review cases
        print(f"\nTarget: {manual_target} manual review URLs")
        manual_urls = self.get_manual_review_urls(limit=50)  # Get all manual review
        all_urls.extend(manual_urls)

        # Calculate statistics
        stats = {
            "total": len(all_urls),
            "by_label": {},
            "by_category": {},
            "by_source": {}
        }

        for url_data in all_urls:
            label = url_data["ground_truth_label"]
            category = url_data["expected_category"]
            source = url_data["metadata"].get("source", "unknown")

            stats["by_label"][label] = stats["by_label"].get(label, 0) + 1
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
            stats["by_source"][source] = stats["by_source"].get(source, 0) + 1

        dataset = {
            "dataset_name": "URL Safety Analysis - Real-World Evaluation Dataset",
            "version": "2.0",
            "created": datetime.utcnow().isoformat(),
            "total_urls": len(all_urls),
            "statistics": stats,
            "sources": [
                "URLhaus (abuse.ch)",
                "Known phishing patterns",
                "Known scam sites",
                "Verified legitimate sites",
                "Suspicious/borderline sites"
            ],
            "test_cases": all_urls
        }

        print(f"\n{'='*70}")
        print(f"Dataset Build Complete!")
        print(f"{'='*70}")
        print(f"\nTotal URLs: {len(all_urls)}")
        print(f"\nDistribution by Label:")
        for label, count in sorted(stats["by_label"].items()):
            percentage = (count / len(all_urls)) * 100
            print(f"  {label}: {count} ({percentage:.1f}%)")

        print(f"\nDistribution by Source:")
        for source, count in sorted(stats["by_source"].items()):
            print(f"  {source}: {count}")

        return dataset

    def save_dataset(self, dataset: Dict, output_path: str):
        """Save dataset to JSON file."""
        with open(output_path, 'w') as f:
            json.dump(dataset, f, indent=2)
        print(f"\n✓ Dataset saved to: {output_path}")


if __name__ == "__main__":
    builder = RealDatasetBuilder()
    dataset = builder.build_complete_dataset(target_size=500)

    output_path = "../test_datasets/real_world_test_dataset_500.json"
    builder.save_dataset(dataset, output_path)

    print(f"\n{'='*70}")
    print("Next Steps:")
    print("1. Run: python url_cache.py to cache all URLs")
    print("2. Run: python run_evaluation.py to evaluate the dataset")
    print(f"{'='*70}\n")
