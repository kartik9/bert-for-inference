"""Fix Agent — generates prioritized remediation plans."""

from __future__ import annotations

from typing import Dict, List

from src.models.data_models import (
    CodeSnippet,
    Diagnosis,
    Fix,
    FixPlan,
)


# ---------------------------------------------------------------------------
# Fix template library
# ---------------------------------------------------------------------------

_FIX_TEMPLATES: Dict[str, List[Fix]] = {
    "Bot Detection/Blocking": [
        Fix(
            fix_id="cf-bot-fight-mode",
            title="Disable Cloudflare Bot Fight Mode",
            description="Cloudflare's Bot Fight Mode is blocking legitimate ad-platform crawlers. Disable it or create exceptions for verified bots.",
            category="cloudflare",
            priority=1,
            implementation_steps=[
                "Log in to the Cloudflare dashboard",
                "Select the affected domain",
                "Navigate to Security → Bots",
                "Toggle OFF 'Bot Fight Mode'",
                "Alternatively, enable 'Verified Bots' allow-list to permit Googlebot/Bingbot",
                "Wait 5 minutes for changes to propagate",
                "Test with the verification agent",
            ],
            code_snippets=[],
            estimated_time_minutes=10,
            difficulty="easy",
            requires_developer=False,
            verification_steps=[
                "Access site with Googlebot user-agent — expect HTTP 200",
                "Access site with Bingbot user-agent — expect HTTP 200",
                "Verify no Cloudflare challenge page is served to bots",
            ],
        ),
        Fix(
            fix_id="cf-page-rule",
            title="Create Cloudflare Page Rule for Crawlers",
            description="Create a Page Rule that disables security features for known ad-platform crawler IP ranges.",
            category="cloudflare",
            priority=2,
            implementation_steps=[
                "Log in to the Cloudflare dashboard",
                "Navigate to Rules → Page Rules",
                "Create a new Page Rule for the landing page URL pattern",
                "Set Security Level to 'Essentially Off'",
                "Set Browser Integrity Check to 'Off'",
                "Save and deploy the rule",
            ],
            code_snippets=[],
            estimated_time_minutes=15,
            difficulty="easy",
            requires_developer=False,
            verification_steps=[
                "Test the landing page URL with bot user-agents",
                "Verify 200 response without challenge",
            ],
        ),
        Fix(
            fix_id="waf-exception",
            title="Add WAF Exception for Verified Bots",
            description="Create a WAF rule that allows verified ad-platform bots through the firewall.",
            category="firewall",
            priority=2,
            implementation_steps=[
                "Log in to your WAF provider dashboard",
                "Navigate to custom rules / exceptions",
                "Create a new rule: IF cf.bot_management.verified_bot THEN Allow",
                "Alternatively, whitelist known Googlebot/Bingbot IP ranges",
                "Deploy the rule",
            ],
            code_snippets=[
                CodeSnippet(
                    language="text",
                    filename="waf-rule.txt",
                    code='(cf.bot_management.verified_bot) → Action: Allow',
                    description="Cloudflare WAF rule expression to allow verified bots",
                ),
            ],
            estimated_time_minutes=20,
            difficulty="medium",
            requires_developer=False,
            verification_steps=[
                "Test with Googlebot and Bingbot user-agents",
                "Verify responses are 200 OK",
            ],
        ),
    ],
    "Robots.txt Blocking": [
        Fix(
            fix_id="robots-allow-crawlers",
            title="Update robots.txt to Allow Ad Crawlers",
            description="The robots.txt file currently blocks Googlebot and/or Bingbot. Update it to allow these crawlers.",
            category="robots",
            priority=1,
            implementation_steps=[
                "Open the robots.txt file (usually at website root)",
                "Find any 'Disallow: /' rules under User-agent: Googlebot or Bingbot",
                "Change them to 'Allow: /' or remove the Disallow directive",
                "Add explicit Allow rules for ad crawlers",
                "Deploy the updated robots.txt",
                "Wait for crawlers to re-fetch (usually within 24 hours)",
            ],
            code_snippets=[
                CodeSnippet(
                    language="text",
                    filename="robots.txt",
                    code=(
                        "User-agent: Googlebot\n"
                        "Allow: /\n\n"
                        "User-agent: Bingbot\n"
                        "Allow: /\n\n"
                        "User-agent: AdsBot-Google\n"
                        "Allow: /\n\n"
                        "User-agent: *\n"
                        "Allow: /\n"
                    ),
                    description="Updated robots.txt allowing ad crawlers",
                ),
            ],
            estimated_time_minutes=15,
            difficulty="easy",
            requires_developer=True,
            verification_steps=[
                "Fetch /robots.txt and verify it no longer blocks Googlebot/Bingbot",
                "Test site access with bot user-agents",
            ],
        ),
    ],
    "DNS Resolution Failure": [
        Fix(
            fix_id="dns-fix-records",
            title="Fix DNS Configuration",
            description="DNS records are missing or misconfigured. Add or fix A/AAAA records.",
            category="dns",
            priority=1,
            implementation_steps=[
                "Log in to your domain registrar or DNS provider",
                "Navigate to DNS management for the affected domain",
                "Add an A record pointing to your server's IP address",
                "Verify the nameservers are correctly configured",
                "Wait for DNS propagation (up to 48 hours, typically 1-4 hours)",
                "Test DNS resolution from multiple locations",
            ],
            code_snippets=[
                CodeSnippet(
                    language="text",
                    filename="dns-records.txt",
                    code=(
                        "Type: A\n"
                        "Name: @\n"
                        "Value: <your-server-ip>\n"
                        "TTL: 3600\n\n"
                        "Type: A\n"
                        "Name: www\n"
                        "Value: <your-server-ip>\n"
                        "TTL: 3600"
                    ),
                    description="Example DNS A records to add",
                ),
            ],
            estimated_time_minutes=30,
            difficulty="medium",
            requires_developer=True,
            verification_steps=[
                "Run: nslookup yourdomain.com",
                "Verify A records resolve to the correct IP",
                "Test HTTP access to the domain",
            ],
        ),
    ],
    "Geographic Restriction": [
        Fix(
            fix_id="geo-remove-blocking",
            title="Remove Geographic Restrictions",
            description="The site blocks access from certain geographic regions. Remove or adjust geo-restrictions.",
            category="geo",
            priority=1,
            implementation_steps=[
                "Identify where geo-blocking is configured (CDN, firewall, or application)",
                "Log in to the CDN/firewall dashboard",
                "Remove or relax geographic restrictions",
                "Ensure the ad-platform target regions are allowed",
                "Test access from previously blocked regions",
            ],
            code_snippets=[],
            estimated_time_minutes=20,
            difficulty="medium",
            requires_developer=False,
            verification_steps=[
                "Test from US, EU, and Asia locations",
                "Verify 200 OK from all regions",
            ],
        ),
    ],
    "HTTP 404 Not Found": [
        Fix(
            fix_id="fix-404",
            title="Fix URL or Restore Missing Page",
            description="The landing page returns 404. Either fix the URL in the ad or restore the page.",
            category="content",
            priority=1,
            implementation_steps=[
                "Verify the ad's destination URL is correct",
                "If the page was moved, update the ad to the new URL",
                "If the page was deleted, restore it or create a replacement",
                "Set up a 301 redirect from the old URL to the new one if applicable",
                "Update the ad campaign with the correct URL",
            ],
            code_snippets=[
                CodeSnippet(
                    language="apache",
                    filename=".htaccess",
                    code="Redirect 301 /old-page /new-page",
                    description="Apache redirect from old to new URL",
                ),
                CodeSnippet(
                    language="nginx",
                    filename="nginx.conf",
                    code=(
                        "location /old-page {\n"
                        "    return 301 /new-page;\n"
                        "}"
                    ),
                    description="Nginx redirect from old to new URL",
                ),
            ],
            estimated_time_minutes=15,
            difficulty="easy",
            requires_developer=False,
            verification_steps=[
                "Access the landing page URL — expect HTTP 200",
                "Verify page content loads correctly",
            ],
        ),
    ],
    "Redirect Loop": [
        Fix(
            fix_id="fix-redirect-loop",
            title="Fix Redirect Loop",
            description="The landing page creates an infinite redirect loop. Fix the redirect configuration.",
            category="redirect",
            priority=1,
            implementation_steps=[
                "Identify the redirect rules causing the loop (server config, CMS, or CDN)",
                "Check for conflicting redirect rules (e.g., HTTP→HTTPS and HTTPS→HTTP)",
                "Remove or fix conflicting rules",
                "Ensure only one canonical redirect path exists",
                "Test the full redirect chain",
            ],
            code_snippets=[
                CodeSnippet(
                    language="apache",
                    filename=".htaccess",
                    code=(
                        "# Correct: single redirect to HTTPS\n"
                        "RewriteEngine On\n"
                        "RewriteCond %{HTTPS} off\n"
                        "RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]"
                    ),
                    description="Correct Apache HTTPS redirect (non-looping)",
                ),
            ],
            estimated_time_minutes=45,
            difficulty="hard",
            requires_developer=True,
            verification_steps=[
                "Test redirect chain — expect max 1-2 redirects, no loops",
                "Verify final URL returns HTTP 200",
            ],
        ),
    ],
    "SSL/TLS Certificate Error": [
        Fix(
            fix_id="fix-ssl",
            title="Fix SSL/TLS Certificate",
            description="SSL certificate is invalid, expired, or misconfigured.",
            category="ssl",
            priority=1,
            implementation_steps=[
                "Identify the SSL error (expired, wrong domain, self-signed, etc.)",
                "Renew or reissue the SSL certificate",
                "Install the new certificate on the server",
                "Verify the certificate chain is complete (intermediate certs included)",
                "Test SSL with an online checker (e.g., SSL Labs)",
            ],
            code_snippets=[
                CodeSnippet(
                    language="bash",
                    filename="renew-ssl.sh",
                    code=(
                        "# Using Let's Encrypt / Certbot\n"
                        "sudo certbot renew --force-renewal\n"
                        "sudo systemctl restart nginx  # or apache2"
                    ),
                    description="Renew Let's Encrypt SSL certificate",
                ),
            ],
            estimated_time_minutes=30,
            difficulty="medium",
            requires_developer=True,
            verification_steps=[
                "Run: openssl s_client -connect yourdomain.com:443",
                "Verify certificate is valid and not expired",
                "Check SSL Labs report for the domain",
            ],
        ),
    ],
    "Performance / Timeout": [
        Fix(
            fix_id="fix-performance",
            title="Optimize Server Performance",
            description="Server responds too slowly, causing ad crawlers to time out.",
            category="performance",
            priority=1,
            implementation_steps=[
                "Enable server-side caching (Redis, Memcached, or CDN)",
                "Optimize database queries on the landing page",
                "Enable compression (gzip/brotli)",
                "Consider using a CDN (Cloudflare, AWS CloudFront)",
                "Review and optimize server resources (CPU, memory)",
                "Check for slow third-party scripts blocking page load",
            ],
            code_snippets=[
                CodeSnippet(
                    language="nginx",
                    filename="nginx.conf",
                    code=(
                        "# Enable gzip compression\n"
                        "gzip on;\n"
                        "gzip_types text/html text/css application/javascript;\n"
                        "gzip_min_length 1000;\n\n"
                        "# Enable caching\n"
                        "location ~* \\.(jpg|jpeg|png|gif|ico|css|js)$ {\n"
                        "    expires 30d;\n"
                        "    add_header Cache-Control \"public, immutable\";\n"
                        "}"
                    ),
                    description="Nginx performance optimization config",
                ),
            ],
            estimated_time_minutes=60,
            difficulty="hard",
            requires_developer=True,
            verification_steps=[
                "Test response time — expect < 3 seconds",
                "Verify success rate > 95%",
                "Run 10 consecutive requests without timeout",
            ],
        ),
    ],
    "Tracking Parameter Handling Error": [
        Fix(
            fix_id="fix-tracking-params",
            title="Fix Query Parameter Handling",
            description="Site breaks when ad tracking parameters (gclid, msclkid) are appended to the URL.",
            category="tracking",
            priority=1,
            implementation_steps=[
                "Identify the server-side code that handles query parameters",
                "Ensure the application ignores unknown query parameters gracefully",
                "Test with common tracking parameters: gclid, msclkid, utm_source, etc.",
                "If using a framework, check route configuration for strict parameter matching",
                "Deploy the fix and test",
            ],
            code_snippets=[
                CodeSnippet(
                    language="python",
                    filename="app.py",
                    code=(
                        "# Flask example: ignore unknown query params\n"
                        "@app.route('/landing')\n"
                        "def landing():\n"
                        "    # Only read params you need; ignore the rest\n"
                        "    product_id = request.args.get('id')\n"
                        "    # gclid, msclkid will be in request.args but harmlessly ignored\n"
                        "    return render_template('landing.html', product_id=product_id)"
                    ),
                    description="Example: gracefully handling unknown query parameters",
                ),
                CodeSnippet(
                    language="nginx",
                    filename="nginx.conf",
                    code=(
                        "# Strip tracking params before passing to backend\n"
                        "location / {\n"
                        "    if ($args ~* \"(.*)(?:^|&)(?:gclid|msclkid|utm_[a-z]+)=[^&]*(.*)\") {\n"
                        "        set $args $1$2;\n"
                        "    }\n"
                        "    proxy_pass http://backend;\n"
                        "}"
                    ),
                    description="Nginx: strip tracking params before proxying",
                ),
            ],
            estimated_time_minutes=30,
            difficulty="medium",
            requires_developer=True,
            verification_steps=[
                "Test URL with ?gclid=test — expect HTTP 200",
                "Test URL with ?msclkid=test — expect HTTP 200",
                "Verify page content loads correctly with tracking params",
            ],
        ),
    ],
}


class FixAgent:
    """Generate prioritized remediation steps based on a diagnosis."""

    async def generate_fixes(
        self, diagnosis: Diagnosis, context: Dict | None = None
    ) -> FixPlan:
        fixes = self._lookup_fixes(diagnosis)
        fixes = self.prioritize_fixes(fixes)

        total_time = sum(f.estimated_time_minutes for f in fixes)
        can_self_serve = all(not f.requires_developer for f in fixes if f.priority <= 2)

        warnings: List[str] = []
        if diagnosis.severity.value == "critical":
            warnings.append("CRITICAL: Ads are currently being disapproved. Fix immediately.")
        if any(f.difficulty == "hard" for f in fixes):
            warnings.append("Some fixes require advanced technical knowledge.")
        if total_time > 60:
            warnings.append(f"Estimated total fix time: {total_time} minutes.")

        return FixPlan(
            diagnosis=diagnosis,
            fixes=fixes,
            total_estimated_time_minutes=total_time,
            can_implement_without_developer=can_self_serve,
            warnings=warnings,
        )

    def prioritize_fixes(self, fixes: List[Fix]) -> List[Fix]:
        return sorted(fixes, key=lambda f: (f.priority, f.estimated_time_minutes))

    def _lookup_fixes(self, diagnosis: Diagnosis) -> List[Fix]:
        templates = _FIX_TEMPLATES.get(diagnosis.primary_issue, [])
        if templates:
            return [self._copy_fix(f) for f in templates]

        # Fallback — generic advice
        return [
            Fix(
                fix_id="generic-investigate",
                title="Investigate Further",
                description=(
                    f"The diagnosis identified '{diagnosis.primary_issue}' but no "
                    f"specific fix template is available. Manual investigation is recommended."
                ),
                category="generic",
                priority=2,
                implementation_steps=[
                    "Review the diagnosis findings in detail",
                    "Check server logs for errors",
                    "Contact your hosting provider if needed",
                    "Re-run the diagnostic suite after making changes",
                ],
                code_snippets=[],
                estimated_time_minutes=60,
                difficulty="hard",
                requires_developer=True,
                verification_steps=["Re-run full diagnostic suite"],
            )
        ]

    @staticmethod
    def _copy_fix(fix: Fix) -> Fix:
        """Return a shallow copy so templates aren't mutated."""
        return Fix(
            fix_id=fix.fix_id,
            title=fix.title,
            description=fix.description,
            category=fix.category,
            priority=fix.priority,
            implementation_steps=list(fix.implementation_steps),
            code_snippets=list(fix.code_snippets),
            estimated_time_minutes=fix.estimated_time_minutes,
            difficulty=fix.difficulty,
            requires_developer=fix.requires_developer,
            verification_steps=list(fix.verification_steps),
        )
