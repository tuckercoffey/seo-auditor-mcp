"""
Technical SEO analyzer
Handles mobile-friendliness, structured data, security, and technical optimization analysis
"""

import asyncio
import httpx
import json
import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
from asyncio_throttle import Throttler

from config import Config
from database.models import AuditResult, save_audit_result

logger = logging.getLogger(__name__)

class TechnicalSEOAnalyzer:
    """Analyzer for technical SEO factors."""
    
    def __init__(self):
        self.session = None
        self.throttler = Throttler(rate_limit=Config.REQUESTS_PER_SECOND, period=1.0)
        
    async def _get_session(self):
        """Get or create HTTP session."""
        if not self.session:
            self.session = httpx.AsyncClient(
                timeout=Config.REQUEST_TIMEOUT,
                headers={'User-Agent': Config.DEFAULT_USER_AGENT},
                follow_redirects=True
            )
        return self.session

    async def _make_request(self, url: str) -> Tuple[Optional[httpx.Response], Optional[str]]:
        """Make throttled HTTP request with error handling."""
        try:
            async with self.throttler:
                session = await self._get_session()
                response = await session.get(url)
                return response, None
        except Exception as e:
            logger.error(f"Request failed for {url}: {str(e)}")
            return None, str(e)

    async def analyze_technical_seo(self, url: str, include_security: bool = True) -> Dict[str, Any]:
        """
        Comprehensive technical SEO analysis.
        
        Args:
            url: URL to analyze
            include_security: Whether to include security analysis
            
        Returns:
            Dict containing technical SEO analysis results
        """
        logger.info(f"Starting technical SEO analysis for {url}")
        
        results = {
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "https_analysis": {},
            "mobile_analysis": {},
            "structured_data": {},
            "canonical_analysis": {},
            "meta_tags": {},
            "issues": [],
            "recommendations": [],
            "score": 0
        }
        
        response, error = await self._make_request(url)
        
        if error or not response:
            results["error"] = error or "Could not fetch page"
            return results
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # HTTPS Analysis
        results["https_analysis"] = await self._analyze_https(url, response)
        
        # Mobile-friendliness
        results["mobile_analysis"] = await self._analyze_mobile_friendliness(soup)
        
        # Structured data
        results["structured_data"] = await self._analyze_structured_data(soup)
        
        # Canonical analysis
        results["canonical_analysis"] = await self._analyze_canonical(url, soup)
        
        # Meta tags analysis
        results["meta_tags"] = await self._analyze_meta_tags(soup)
        
        # Security headers (if requested)
        if include_security:
            results["security_analysis"] = await self._analyze_security_headers(response)
            
        # Calculate overall score and recommendations
        results["score"] = self._calculate_technical_score(results)
        results["issues"], results["recommendations"] = self._generate_technical_recommendations(results)
        
        # Save to database
        audit_result = AuditResult(
            url=url,
            audit_type="technical_seo",
            timestamp=datetime.now(),
            results=results,
            score=results["score"],
            issues=results["issues"],
            recommendations=results["recommendations"]
        )
        await save_audit_result(audit_result)
        
        return results

    async def _analyze_https(self, url: str, response: httpx.Response) -> Dict[str, Any]:
        """Analyze HTTPS implementation and security."""
        parsed_url = urlparse(url)
        
        analysis = {
            "uses_https": parsed_url.scheme == "https",
            "has_hsts": "strict-transport-security" in response.headers,
            "redirect_http_to_https": False,
            "mixed_content_issues": []
        }
        
        # Check if HTTP redirects to HTTPS
        if parsed_url.scheme == "https":
            http_url = url.replace("https://", "http://")
            http_response, _ = await self._make_request(http_url)
            
            if http_response and http_response.status_code in [301, 302]:
                redirect_location = http_response.headers.get("location", "")
                if redirect_location.startswith("https://"):
                    analysis["redirect_http_to_https"] = True
        
        # Check for mixed content (HTTPS pages loading HTTP resources)
        if parsed_url.scheme == "https":
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check images
            for img in soup.find_all('img', src=True):
                src = img.get('src')
                if src and src.startswith('http://'):
                    analysis["mixed_content_issues"].append(f"HTTP image: {src}")
            
            # Check scripts
            for script in soup.find_all('script', src=True):
                src = script.get('src')
                if src and src.startswith('http://'):
                    analysis["mixed_content_issues"].append(f"HTTP script: {src}")
            
            # Check stylesheets
            for link in soup.find_all('link', href=True):
                href = link.get('href')
                if href and href.startswith('http://') and link.get('rel') == ['stylesheet']:
                    analysis["mixed_content_issues"].append(f"HTTP stylesheet: {href}")
        
        return analysis

    async def _analyze_mobile_friendliness(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze mobile-friendliness indicators."""
        analysis = {
            "has_viewport_meta": False,
            "viewport_content": "",
            "has_responsive_design": False,
            "uses_mobile_css": False,
            "font_size_issues": [],
            "touch_target_issues": []
        }
        
        # Check viewport meta tag
        viewport_meta = soup.find('meta', attrs={'name': 'viewport'})
        if viewport_meta:
            analysis["has_viewport_meta"] = True
            analysis["viewport_content"] = viewport_meta.get('content', '')
            
            # Check for responsive indicators in viewport
            if 'width=device-width' in analysis["viewport_content"]:
                analysis["has_responsive_design"] = True
        
        # Check for mobile-specific CSS
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href', '')
            media = link.get('media', '')
            if 'mobile' in href.lower() or 'responsive' in href.lower():
                analysis["uses_mobile_css"] = True
            if 'screen' in media and 'max-width' in media:
                analysis["uses_mobile_css"] = True
                
        # Check for CSS media queries in style tags
        for style in soup.find_all('style'):
            if style.string and '@media' in style.string:
                analysis["uses_mobile_css"] = True
        
        return analysis

    async def _analyze_structured_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze structured data implementation."""
        analysis = {
            "json_ld_count": 0,
            "microdata_count": 0,
            "rdfa_count": 0,
            "schemas_found": [],
            "errors": []
        }
        
        # JSON-LD structured data
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        analysis["json_ld_count"] = len(json_ld_scripts)
        
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and '@type' in data:
                    analysis["schemas_found"].append(data['@type'])
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and '@type' in item:
                            analysis["schemas_found"].append(item['@type'])
            except json.JSONDecodeError:
                analysis["errors"].append("Invalid JSON-LD syntax found")
        
        # Microdata
        microdata_elements = soup.find_all(attrs={'itemtype': True})
        analysis["microdata_count"] = len(microdata_elements)
        
        for element in microdata_elements:
            itemtype = element.get('itemtype', '')
            if itemtype:
                schema_type = itemtype.split('/')[-1]
                analysis["schemas_found"].append(f"Microdata: {schema_type}")
        
        # RDFa
        rdfa_elements = soup.find_all(attrs={'typeof': True})
        analysis["rdfa_count"] = len(rdfa_elements)
        
        for element in rdfa_elements:
            typeof = element.get('typeof', '')
            if typeof:
                analysis["schemas_found"].append(f"RDFa: {typeof}")
        
        return analysis

    async def _analyze_canonical(self, url: str, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze canonical URL implementation."""
        analysis = {
            "has_canonical": False,
            "canonical_url": "",
            "self_referencing": False,
            "issues": []
        }
        
        canonical_link = soup.find('link', rel='canonical')
        
        if canonical_link:
            analysis["has_canonical"] = True
            canonical_href = canonical_link.get('href', '')
            
            if canonical_href:
                # Convert relative URL to absolute
                canonical_url = urljoin(url, canonical_href)
                analysis["canonical_url"] = canonical_url
                
                # Check if self-referencing
                parsed_original = urlparse(url)
                parsed_canonical = urlparse(canonical_url)
                
                if (parsed_original.netloc == parsed_canonical.netloc and 
                    parsed_original.path == parsed_canonical.path):
                    analysis["self_referencing"] = True
            else:
                analysis["issues"].append("Canonical link tag has empty href attribute")
        else:
            analysis["issues"].append("No canonical link tag found")
            
        return analysis

    async def _analyze_meta_tags(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze important meta tags."""
        analysis = {
            "title": "",
            "title_length": 0,
            "meta_description": "",
            "meta_description_length": 0,
            "meta_keywords": "",
            "robots_meta": "",
            "og_tags": {},
            "twitter_tags": {},
            "issues": []
        }
        
        # Title tag
        title_tag = soup.find('title')
        if title_tag:
            analysis["title"] = title_tag.get_text().strip()
            analysis["title_length"] = len(analysis["title"])
        else:
            analysis["issues"].append("Missing title tag")
        
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            analysis["meta_description"] = meta_desc.get('content', '').strip()
            analysis["meta_description_length"] = len(analysis["meta_description"])
        else:
            analysis["issues"].append("Missing meta description")
        
        # Meta keywords (deprecated but still analyzed)
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords:
            analysis["meta_keywords"] = meta_keywords.get('content', '')
        
        # Robots meta tag
        robots_meta = soup.find('meta', attrs={'name': 'robots'})
        if robots_meta:
            analysis["robots_meta"] = robots_meta.get('content', '')
        
        # Open Graph tags
        og_tags = soup.find_all('meta', attrs={'property': re.compile(r'^og:')})
        for tag in og_tags:
            property_name = tag.get('property', '')
            content = tag.get('content', '')
            if property_name and content:
                analysis["og_tags"][property_name] = content
        
        # Twitter Card tags
        twitter_tags = soup.find_all('meta', attrs={'name': re.compile(r'^twitter:')})
        for tag in twitter_tags:
            name = tag.get('name', '')
            content = tag.get('content', '')
            if name and content:
                analysis["twitter_tags"][name] = content
        
        return analysis

    async def _analyze_security_headers(self, response: httpx.Response) -> Dict[str, Any]:
        """Analyze security-related HTTP headers."""
        headers = response.headers
        
        analysis = {
            "hsts": headers.get("strict-transport-security"),
            "csp": headers.get("content-security-policy"),
            "x_frame_options": headers.get("x-frame-options"),
            "x_content_type": headers.get("x-content-type-options"),
            "referrer_policy": headers.get("referrer-policy"),
            "permissions_policy": headers.get("permissions-policy"),
            "security_score": 0,
            "missing_headers": []
        }
        
        # Check for missing security headers
        security_headers = [
            ("strict-transport-security", "HSTS"),
            ("x-frame-options", "X-Frame-Options"),
            ("x-content-type-options", "X-Content-Type-Options"),
            ("referrer-policy", "Referrer-Policy")
        ]
        
        for header_name, display_name in security_headers:
            if header_name not in headers:
                analysis["missing_headers"].append(display_name)
        
        # Calculate security score
        total_headers = len(security_headers)
        present_headers = total_headers - len(analysis["missing_headers"])
        analysis["security_score"] = (present_headers / total_headers) * 100
        
        return analysis

    def _calculate_technical_score(self, results: Dict[str, Any]) -> float:
        """Calculate overall technical SEO score."""
        score = 0
        max_score = 100
        
        # HTTPS (20 points)
        https = results.get("https_analysis", {})
        if https.get("uses_https"):
            score += 10
        if https.get("redirect_http_to_https"):
            score += 5
        if https.get("has_hsts"):
            score += 5
        
        # Mobile-friendliness (20 points)
        mobile = results.get("mobile_analysis", {})
        if mobile.get("has_viewport_meta"):
            score += 10
        if mobile.get("has_responsive_design"):
            score += 10
        
        # Structured data (15 points)
        structured = results.get("structured_data", {})
        if structured.get("json_ld_count", 0) > 0:
            score += 15
        elif structured.get("microdata_count", 0) > 0:
            score += 10
        
        # Canonical (10 points)
        canonical = results.get("canonical_analysis", {})
        if canonical.get("has_canonical"):
            score += 10
        
        # Meta tags (20 points)
        meta = results.get("meta_tags", {})
        if meta.get("title"):
            score += 10
        if meta.get("meta_description"):
            score += 10
        
        # Security (15 points)
        security = results.get("security_analysis", {})
        if security:
            score += (security.get("security_score", 0) / 100) * 15
        
        return min(score, max_score)

    def _generate_technical_recommendations(self, results: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Generate issues and recommendations based on analysis."""
        issues = []
        recommendations = []
        
        # HTTPS issues
        https = results.get("https_analysis", {})
        if not https.get("uses_https"):
            issues.append("Site not using HTTPS")
            recommendations.append("Implement HTTPS with SSL certificate")
        
        if not https.get("redirect_http_to_https"):
            issues.append("HTTP does not redirect to HTTPS")
            recommendations.append("Set up 301 redirects from HTTP to HTTPS")
        
        if not https.get("has_hsts"):
            recommendations.append("Implement HSTS header for enhanced security")
        
        if https.get("mixed_content_issues"):
            issues.append(f"Mixed content issues found: {len(https['mixed_content_issues'])}")
            recommendations.append("Fix mixed content by using HTTPS for all resources")
        
        # Mobile issues
        mobile = results.get("mobile_analysis", {})
        if not mobile.get("has_viewport_meta"):
            issues.append("Missing viewport meta tag")
            recommendations.append("Add viewport meta tag for mobile responsiveness")
        
        if not mobile.get("has_responsive_design"):
            issues.append("No responsive design indicators found")
            recommendations.append("Implement responsive design with CSS media queries")
        
        # Structured data
        structured = results.get("structured_data", {})
        if structured.get("json_ld_count", 0) == 0 and structured.get("microdata_count", 0) == 0:
            recommendations.append("Add structured data markup to enhance search results")
        
        # Canonical issues
        canonical = results.get("canonical_analysis", {})
        if not canonical.get("has_canonical"):
            issues.append("Missing canonical URL")
            recommendations.append("Add canonical link tag to prevent duplicate content issues")
        
        # Meta tag issues
        meta = results.get("meta_tags", {})
        if not meta.get("title"):
            issues.append("Missing title tag")
            recommendations.append("Add descriptive title tag to every page")
        elif meta.get("title_length", 0) > 60:
            issues.append("Title tag too long")
            recommendations.append("Keep title tags under 60 characters")
        
        if not meta.get("meta_description"):
            issues.append("Missing meta description")
            recommendations.append("Add compelling meta description to improve click-through rates")
        elif meta.get("meta_description_length", 0) > 160:
            issues.append("Meta description too long")
            recommendations.append("Keep meta descriptions under 160 characters")
        
        return issues, recommendations

    async def check_mobile_friendliness(self, url: str) -> Dict[str, Any]:
        """Focused mobile-friendliness analysis."""
        response, error = await self._make_request(url)
        
        if error or not response:
            return {
                "url": url,
                "error": error or "Could not fetch page",
                "mobile_friendly": False
            }
        
        soup = BeautifulSoup(response.text, 'html.parser')
        analysis = await self._analyze_mobile_friendliness(soup)
        
        # Calculate mobile-friendliness score
        score = 0
        if analysis["has_viewport_meta"]:
            score += 50
        if analysis["has_responsive_design"]:
            score += 30
        if analysis["uses_mobile_css"]:
            score += 20
        
        return {
            "url": url,
            "mobile_friendly": score >= 70,
            "score": score,
            "analysis": analysis,
            "recommendations": self._get_mobile_recommendations(analysis)
        }

    def _get_mobile_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate mobile-specific recommendations."""
        recommendations = []
        
        if not analysis["has_viewport_meta"]:
            recommendations.append("Add viewport meta tag: <meta name='viewport' content='width=device-width, initial-scale=1'>")
        
        if not analysis["has_responsive_design"]:
            recommendations.append("Implement responsive design with flexible layouts")
        
        if not analysis["uses_mobile_css"]:
            recommendations.append("Add CSS media queries for mobile optimization")
        
        return recommendations

    async def analyze_structured_data(self, url: str) -> Dict[str, Any]:
        """Focused structured data analysis."""
        response, error = await self._make_request(url)
        
        if error or not response:
            return {
                "url": url,
                "error": error or "Could not fetch page"
            }
        
        soup = BeautifulSoup(response.text, 'html.parser')
        analysis = await self._analyze_structured_data(soup)
        
        # Add validation recommendations
        recommendations = []
        if analysis["json_ld_count"] == 0 and analysis["microdata_count"] == 0:
            recommendations.append("Add structured data markup using JSON-LD or Microdata")
        
        if analysis["errors"]:
            recommendations.append("Fix structured data syntax errors")
        
        recommendations.append("Test structured data with Google's Rich Results Test")
        
        return {
            "url": url,
            "analysis": analysis,
            "recommendations": recommendations,
            "has_structured_data": analysis["json_ld_count"] > 0 or analysis["microdata_count"] > 0
        }