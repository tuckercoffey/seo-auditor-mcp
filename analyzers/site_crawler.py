"""
Site crawling and discovery analyzer
Handles website crawling, robots.txt analysis, sitemap validation, and broken link detection
"""

import asyncio
import httpx
from urllib.parse import urljoin, urlparse, parse_qs
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
from typing import Dict, List, Set, Any, Optional, Tuple
from datetime import datetime
import xml.etree.ElementTree as ET
import re
import logging
from asyncio_throttle import Throttler

from config import Config
from database.models import CrawlResult, save_crawl_result

logger = logging.getLogger(__name__)

class SiteCrawler:
    """Site crawler for discovering and analyzing website structure."""
    
    def __init__(self):
        self.session = None
        self.throttler = Throttler(rate_limit=Config.REQUESTS_PER_SECOND, period=1.0)
        
    async def __aenter__(self):
        self.session = httpx.AsyncClient(
            timeout=Config.REQUEST_TIMEOUT,
            headers={'User-Agent': Config.DEFAULT_USER_AGENT},
            follow_redirects=True
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()

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

    async def crawl_site(self, url: str, max_pages: int = 100, depth: int = 3) -> Dict[str, Any]:
        """
        Crawl a website and discover all pages.
        
        Args:
            url: Starting URL
            max_pages: Maximum number of pages to crawl
            depth: Maximum crawl depth
            
        Returns:
            Dict containing crawl results
        """
        logger.info(f"Starting site crawl for {url}")
        
        start_time = datetime.now()
        crawled_urls: Set[str] = set()
        to_crawl: List[Tuple[str, int]] = [(url, 0)]  # (url, depth)
        pages: List[Dict[str, Any]] = []
        errors: List[str] = []
        
        # Parse base domain for internal link filtering
        base_domain = urlparse(url).netloc
        
        while to_crawl and len(crawled_urls) < max_pages:
            current_url, current_depth = to_crawl.pop(0)
            
            if current_url in crawled_urls or current_depth > depth:
                continue
                
            crawled_urls.add(current_url)
            
            # Make request
            response, error = await self._make_request(current_url)
            
            if error or not response:
                errors.append(f"Failed to crawl {current_url}: {error}")
                continue
                
            # Analyze page
            page_data = await self._analyze_page(current_url, response)
            pages.append(page_data)
            
            # Extract internal links for further crawling
            if current_depth < depth:
                internal_links = await self._extract_internal_links(response.text, current_url, base_domain)
                for link in internal_links:
                    if link not in crawled_urls:
                        to_crawl.append((link, current_depth + 1))
        
        # Create results
        crawl_result = CrawlResult(
            url=url,
            total_pages=len(pages),
            crawled_pages=len(crawled_urls),
            errors=errors,
            pages=pages,
            timestamp=start_time
        )
        
        # Save to database
        await save_crawl_result(crawl_result)
        
        return {
            "url": url,
            "pages_found": len(pages),
            "pages_crawled": len(crawled_urls),
            "errors": len(errors),
            "crawl_depth": depth,
            "pages": pages[:10],  # Return first 10 pages for summary
            "error_summary": errors[:5],  # Return first 5 errors
            "crawl_time": (datetime.now() - start_time).total_seconds()
        }

    async def _analyze_page(self, url: str, response: httpx.Response) -> Dict[str, Any]:
        """Analyze individual page for basic SEO data."""
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract basic SEO elements
        title = soup.find('title')
        title_text = title.get_text().strip() if title else ""
        
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        meta_desc_text = meta_desc.get('content', '').strip() if meta_desc else ""
        
        # Count headings
        headings = {
            'h1': len(soup.find_all('h1')),
            'h2': len(soup.find_all('h2')),
            'h3': len(soup.find_all('h3')),
            'h4': len(soup.find_all('h4')),
            'h5': len(soup.find_all('h5')),
            'h6': len(soup.find_all('h6'))
        }
        
        return {
            "url": url,
            "status_code": response.status_code,
            "title": title_text,
            "title_length": len(title_text),
            "meta_description": meta_desc_text,
            "meta_description_length": len(meta_desc_text),
            "headings": headings,
            "word_count": len(soup.get_text().split()),
            "internal_links": len(soup.find_all('a', href=True)),
            "images": len(soup.find_all('img')),
            "response_time": response.elapsed.total_seconds() if hasattr(response, 'elapsed') else None
        }

    async def _extract_internal_links(self, html: str, base_url: str, base_domain: str) -> List[str]:
        """Extract internal links from HTML content."""
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if not href:
                continue
                
            # Convert relative URLs to absolute
            absolute_url = urljoin(base_url, href)
            parsed_url = urlparse(absolute_url)
            
            # Only include internal links
            if parsed_url.netloc == base_domain:
                # Remove fragment and query parameters for deduplication
                clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                if clean_url not in links:
                    links.append(clean_url)
        
        return links

    async def check_robots_txt(self, url: str) -> Dict[str, Any]:
        """
        Analyze robots.txt file for crawling rules and issues.
        
        Args:
            url: Website URL
            
        Returns:
            Dict containing robots.txt analysis
        """
        parsed_url = urlparse(url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        
        response, error = await self._make_request(robots_url)
        
        if error or not response:
            return {
                "url": robots_url,
                "exists": False,
                "error": error or "Could not fetch robots.txt",
                "recommendations": ["Create a robots.txt file to guide search engine crawlers"]
            }
        
        if response.status_code != 200:
            return {
                "url": robots_url,
                "exists": False,
                "status_code": response.status_code,
                "recommendations": ["Create a robots.txt file to guide search engine crawlers"]
            }
        
        # Parse robots.txt content
        robots_content = response.text
        issues = []
        recommendations = []
        
        # Basic validation
        if not robots_content.strip():
            issues.append("Robots.txt file is empty")
            recommendations.append("Add appropriate directives to robots.txt")
        
        # Check for common issues
        lines = robots_content.split('\n')
        has_user_agent = False
        has_sitemap = False
        
        for line in lines:
            line = line.strip()
            if line.startswith('User-agent:'):
                has_user_agent = True
            elif line.startswith('Sitemap:'):
                has_sitemap = True
            elif line.startswith('Disallow: /'):
                # Check for overly broad disallows
                if line == 'Disallow: /':
                    issues.append("Disallow: / blocks all crawlers from entire site")
        
        if not has_user_agent:
            issues.append("No User-agent directive found")
            recommendations.append("Add User-agent directives to specify crawler rules")
        
        if not has_sitemap:
            recommendations.append("Consider adding Sitemap directive to help crawlers find your sitemap")
        
        return {
            "url": robots_url,
            "exists": True,
            "content": robots_content,
            "issues": issues,
            "recommendations": recommendations,
            "has_sitemap_directive": has_sitemap,
            "has_user_agent": has_user_agent
        }

    async def check_sitemap(self, url: str) -> Dict[str, Any]:
        """
        Validate and analyze XML sitemap.
        
        Args:
            url: Website URL or direct sitemap URL
            
        Returns:
            Dict containing sitemap analysis
        """
        # Determine sitemap URL
        if url.endswith('.xml'):
            sitemap_url = url
        else:
            parsed_url = urlparse(url)
            sitemap_url = f"{parsed_url.scheme}://{parsed_url.netloc}/sitemap.xml"
        
        response, error = await self._make_request(sitemap_url)
        
        if error or not response or response.status_code != 200:
            return {
                "url": sitemap_url,
                "exists": False,
                "error": error or f"HTTP {response.status_code if response else 'No response'}",
                "recommendations": [
                    "Create an XML sitemap to help search engines discover your pages",
                    "Submit sitemap to Google Search Console"
                ]
            }
        
        # Parse XML sitemap
        try:
            root = ET.fromstring(response.text)
            namespace = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            
            urls = root.findall('.//sitemap:url', namespace)
            issues = []
            recommendations = []
            
            # Analyze sitemap
            total_urls = len(urls)
            
            if total_urls == 0:
                issues.append("Sitemap contains no URLs")
            elif total_urls > 50000:
                issues.append(f"Sitemap contains {total_urls} URLs (maximum recommended: 50,000)")
                recommendations.append("Consider splitting large sitemap into multiple files")
            
            # Check for required elements
            urls_without_loc = 0
            urls_with_lastmod = 0
            urls_with_priority = 0
            
            for url_elem in urls[:100]:  # Check first 100 URLs
                loc = url_elem.find('sitemap:loc', namespace)
                lastmod = url_elem.find('sitemap:lastmod', namespace)
                priority = url_elem.find('sitemap:priority', namespace)
                
                if loc is None:
                    urls_without_loc += 1
                if lastmod is not None:
                    urls_with_lastmod += 1
                if priority is not None:
                    urls_with_priority += 1
            
            if urls_without_loc > 0:
                issues.append(f"{urls_without_loc} URLs missing required <loc> element")
            
            return {
                "url": sitemap_url,
                "exists": True,
                "total_urls": total_urls,
                "urls_with_lastmod": urls_with_lastmod,
                "urls_with_priority": urls_with_priority,
                "issues": issues,
                "recommendations": recommendations,
                "valid_xml": True
            }
            
        except ET.ParseError as e:
            return {
                "url": sitemap_url,
                "exists": True,
                "valid_xml": False,
                "error": f"XML parsing error: {str(e)}",
                "issues": ["Sitemap contains invalid XML"],
                "recommendations": ["Fix XML syntax errors in sitemap"]
            }

    async def find_broken_links(self, url: str) -> Dict[str, Any]:
        """
        Find broken links and redirect chains on a website.
        
        Args:
            url: Website URL to analyze
            
        Returns:
            Dict containing broken link analysis
        """
        logger.info(f"Analyzing broken links for {url}")
        
        # First crawl the main page to get links
        response, error = await self._make_request(url)
        
        if error or not response:
            return {
                "url": url,
                "error": error or "Could not fetch page",
                "broken_links": [],
                "redirects": []
            }
        
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        
        # Extract all links
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href:
                absolute_url = urljoin(url, href)
                links.append(absolute_url)
        
        # Remove duplicates
        unique_links = list(set(links))[:50]  # Limit to 50 links for performance
        
        broken_links = []
        redirects = []
        
        # Check each link
        for link_url in unique_links:
            try:
                async with self.throttler:
                    session = await self._get_session()
                    response = await session.get(link_url, follow_redirects=False)
                    
                    if response.status_code >= 400:
                        broken_links.append({
                            "url": link_url,
                            "status_code": response.status_code,
                            "error": f"HTTP {response.status_code}"
                        })
                    elif response.status_code in [301, 302, 303, 307, 308]:
                        redirect_target = response.headers.get('location', '')
                        redirects.append({
                            "url": link_url,
                            "status_code": response.status_code,
                            "redirect_target": redirect_target
                        })
                        
            except Exception as e:
                broken_links.append({
                    "url": link_url,
                    "error": str(e)
                })
        
        return {
            "url": url,
            "total_links_checked": len(unique_links),
            "broken_links": broken_links,
            "redirects": redirects,
            "summary": {
                "broken_count": len(broken_links),
                "redirect_count": len(redirects),
                "healthy_links": len(unique_links) - len(broken_links) - len(redirects)
            },
            "recommendations": [
                "Fix broken links to improve user experience and SEO",
                "Update redirected links to point directly to final destination",
                "Regularly monitor for new broken links"
            ] if broken_links or redirects else ["All checked links are working properly"]
        }