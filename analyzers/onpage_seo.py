"""
On-page SEO analyzer
Handles content analysis, keyword optimization, title tags, meta descriptions, and readability
"""

import asyncio
import httpx
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
from collections import Counter
import math

from config import Config
from database.models import AuditResult, save_audit_result

logger = logging.getLogger(__name__)

class OnPageSEOAnalyzer:
    """Analyzer for on-page SEO factors."""
    
    def __init__(self):
        self.session = None
        
    async def _get_session(self):
        """Get or create HTTP session."""
        if not self.session:
            self.session = httpx.AsyncClient(
                timeout=Config.REQUEST_TIMEOUT,
                headers={'User-Agent': Config.DEFAULT_USER_AGENT}
            )
        return self.session

    async def _make_request(self, url: str) -> Tuple[Optional[httpx.Response], Optional[str]]:
        """Make HTTP request with error handling."""
        try:
            session = await self._get_session()
            response = await session.get(url)
            return response, None
        except Exception as e:
            logger.error(f"Request failed for {url}: {str(e)}")
            return None, str(e)

    async def analyze_onpage_seo(self, url: str, target_keyword: Optional[str] = None) -> Dict[str, Any]:
        """
        Comprehensive on-page SEO analysis.
        
        Args:
            url: URL to analyze
            target_keyword: Primary target keyword for optimization analysis
            
        Returns:
            Dict containing on-page SEO analysis results
        """
        logger.info(f"Starting on-page SEO analysis for {url}")
        
        results = {
            "url": url,
            "target_keyword": target_keyword,
            "timestamp": datetime.now().isoformat(),
            "title_analysis": {},
            "meta_description_analysis": {},
            "heading_analysis": {},
            "content_analysis": {},
            "image_analysis": {},
            "internal_linking": {},
            "keyword_analysis": {},
            "readability": {},
            "issues": [],
            "recommendations": [],
            "score": 0
        }
        
        response, error = await self._make_request(url)
        
        if error or not response:
            results["error"] = error or "Could not fetch page"
            return results
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Analyze different on-page elements
        results["title_analysis"] = await self._analyze_title_tag(soup, target_keyword)
        results["meta_description_analysis"] = await self._analyze_meta_description(soup, target_keyword)
        results["heading_analysis"] = await self._analyze_headings(soup, target_keyword)
        results["content_analysis"] = await self._analyze_content(soup, target_keyword)
        results["image_analysis"] = await self._analyze_images(soup, url)
        results["internal_linking"] = await self._analyze_internal_links(soup, url)
        
        if target_keyword:
            results["keyword_analysis"] = await self._analyze_keyword_optimization(soup, target_keyword)
        
        results["readability"] = await self._analyze_readability(soup)
        
        # Calculate overall score and generate recommendations
        results["score"] = self._calculate_onpage_score(results)
        results["issues"], results["recommendations"] = self._generate_onpage_recommendations(results)
        
        # Save to database
        audit_result = AuditResult(
            url=url,
            audit_type="onpage_seo",
            timestamp=datetime.now(),
            results=results,
            score=results["score"],
            issues=results["issues"],
            recommendations=results["recommendations"]
        )
        await save_audit_result(audit_result)
        
        return results

    async def _analyze_title_tag(self, soup: BeautifulSoup, target_keyword: Optional[str] = None) -> Dict[str, Any]:
        """Analyze title tag optimization."""
        title_element = soup.find('title')
        
        analysis = {
            "title": "",
            "length": 0,
            "length_status": "",
            "has_keyword": False,
            "keyword_position": -1,
            "issues": [],
            "recommendations": []
        }
        
        if not title_element:
            analysis["issues"].append("Missing title tag")
            analysis["recommendations"].append("Add a descriptive title tag to the page")
            return analysis
        
        title_text = title_element.get_text().strip()
        analysis["title"] = title_text
        analysis["length"] = len(title_text)
        
        # Analyze title length
        if analysis["length"] == 0:
            analysis["length_status"] = "empty"
            analysis["issues"].append("Title tag is empty")
        elif analysis["length"] < 30:
            analysis["length_status"] = "too_short"
            analysis["issues"].append("Title tag is too short (under 30 characters)")
        elif analysis["length"] > 60:
            analysis["length_status"] = "too_long"
            analysis["issues"].append("Title tag is too long (over 60 characters)")
        else:
            analysis["length_status"] = "optimal"
        
        # Keyword analysis
        if target_keyword:
            keyword_lower = target_keyword.lower()
            title_lower = title_text.lower()
            
            if keyword_lower in title_lower:
                analysis["has_keyword"] = True
                analysis["keyword_position"] = title_lower.find(keyword_lower)
                
                if analysis["keyword_position"] == 0:
                    analysis["recommendations"].append("Great! Target keyword appears at the beginning of title")
                elif analysis["keyword_position"] < 30:
                    analysis["recommendations"].append("Good keyword placement in title tag")
                else:
                    analysis["recommendations"].append("Consider moving target keyword closer to the beginning of title")
            else:
                analysis["issues"].append("Target keyword not found in title tag")
                analysis["recommendations"].append(f"Include '{target_keyword}' in the title tag")
        
        # General recommendations
        if analysis["length_status"] == "optimal" and not analysis["issues"]:
            analysis["recommendations"].append("Title tag length is optimal")
        
        return analysis

    async def _analyze_meta_description(self, soup: BeautifulSoup, target_keyword: Optional[str] = None) -> Dict[str, Any]:
        """Analyze meta description optimization."""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        
        analysis = {
            "description": "",
            "length": 0,
            "length_status": "",
            "has_keyword": False,
            "issues": [],
            "recommendations": []
        }
        
        if not meta_desc:
            analysis["issues"].append("Missing meta description")
            analysis["recommendations"].append("Add a compelling meta description to improve click-through rates")
            return analysis
        
        desc_text = meta_desc.get('content', '').strip()
        analysis["description"] = desc_text
        analysis["length"] = len(desc_text)
        
        # Analyze description length
        if analysis["length"] == 0:
            analysis["length_status"] = "empty"
            analysis["issues"].append("Meta description is empty")
        elif analysis["length"] < 120:
            analysis["length_status"] = "too_short"
            analysis["issues"].append("Meta description is too short (under 120 characters)")
        elif analysis["length"] > 160:
            analysis["length_status"] = "too_long"
            analysis["issues"].append("Meta description is too long (over 160 characters)")
        else:
            analysis["length_status"] = "optimal"
        
        # Keyword analysis
        if target_keyword and desc_text:
            if target_keyword.lower() in desc_text.lower():
                analysis["has_keyword"] = True
                analysis["recommendations"].append("Target keyword found in meta description")
            else:
                analysis["issues"].append("Target keyword not found in meta description")
                analysis["recommendations"].append(f"Include '{target_keyword}' in meta description")
        
        return analysis

    async def _analyze_headings(self, soup: BeautifulSoup, target_keyword: Optional[str] = None) -> Dict[str, Any]:
        """Analyze heading structure and optimization."""
        analysis = {
            "h1_count": 0,
            "h1_text": [],
            "h1_has_keyword": False,
            "heading_structure": {},
            "heading_hierarchy_issues": [],
            "issues": [],
            "recommendations": []
        }
        
        # Count all headings
        for level in range(1, 7):
            headings = soup.find_all(f'h{level}')
            analysis["heading_structure"][f"h{level}"] = len(headings)
            
            if level == 1:
                analysis["h1_count"] = len(headings)
                analysis["h1_text"] = [h.get_text().strip() for h in headings]
        
        # Analyze H1 tags
        if analysis["h1_count"] == 0:
            analysis["issues"].append("Missing H1 tag")
            analysis["recommendations"].append("Add an H1 tag with your primary keyword")
        elif analysis["h1_count"] > 1:
            analysis["issues"].append(f"Multiple H1 tags found ({analysis['h1_count']})")
            analysis["recommendations"].append("Use only one H1 tag per page")
        else:
            # Check if H1 contains target keyword
            if target_keyword and analysis["h1_text"]:
                h1_text = analysis["h1_text"][0].lower()
                if target_keyword.lower() in h1_text:
                    analysis["h1_has_keyword"] = True
                    analysis["recommendations"].append("H1 contains target keyword")
                else:
                    analysis["issues"].append("H1 doesn't contain target keyword")
                    analysis["recommendations"].append(f"Include '{target_keyword}' in H1 tag")
        
        # Check heading hierarchy
        previous_level = 0
        for level in range(1, 7):
            count = analysis["heading_structure"][f"h{level}"]
            if count > 0:
                if level > previous_level + 1 and previous_level > 0:
                    analysis["heading_hierarchy_issues"].append(
                        f"Heading hierarchy skip: H{previous_level} to H{level}"
                    )
                previous_level = level
        
        if analysis["heading_hierarchy_issues"]:
            analysis["issues"].extend(analysis["heading_hierarchy_issues"])
            analysis["recommendations"].append("Fix heading hierarchy - don't skip heading levels")
        
        return analysis

    async def _analyze_content(self, soup: BeautifulSoup, target_keyword: Optional[str] = None) -> Dict[str, Any]:
        """Analyze content quality and optimization."""
        # Extract text content
        for script in soup(["script", "style"]):
            script.decompose()
        
        text_content = soup.get_text()
        words = text_content.split()
        word_count = len(words)
        
        analysis = {
            "word_count": word_count,
            "word_count_status": "",
            "paragraph_count": len(soup.find_all('p')),
            "list_count": len(soup.find_all(['ul', 'ol'])),
            "keyword_density": 0,
            "keyword_frequency": 0,
            "content_quality_score": 0,
            "issues": [],
            "recommendations": []
        }
        
        # Analyze word count
        if word_count < 300:
            analysis["word_count_status"] = "thin"
            analysis["issues"].append("Content is too short (under 300 words)")
            analysis["recommendations"].append("Expand content to at least 300 words for better SEO")
        elif word_count < 1000:
            analysis["word_count_status"] = "moderate"
            analysis["recommendations"].append("Consider expanding content for more comprehensive coverage")
        else:
            analysis["word_count_status"] = "comprehensive"
            analysis["recommendations"].append("Good content length for comprehensive coverage")
        
        # Keyword analysis
        if target_keyword and word_count > 0:
            keyword_lower = target_keyword.lower()
            text_lower = text_content.lower()
            
            # Count keyword occurrences
            analysis["keyword_frequency"] = text_lower.count(keyword_lower)
            analysis["keyword_density"] = (analysis["keyword_frequency"] / word_count) * 100
            
            # Analyze keyword density
            if analysis["keyword_density"] == 0:
                analysis["issues"].append("Target keyword not found in content")
                analysis["recommendations"].append("Include target keyword naturally in content")
            elif analysis["keyword_density"] < 0.5:
                analysis["recommendations"].append("Consider using target keyword more frequently (0.5-2.5% density)")
            elif analysis["keyword_density"] > 3:
                analysis["issues"].append("Keyword density too high (over 3%)")
                analysis["recommendations"].append("Reduce keyword density to avoid over-optimization")
            else:
                analysis["recommendations"].append("Good keyword density")
        
        # Content structure analysis
        if analysis["paragraph_count"] == 0:
            analysis["issues"].append("No paragraphs found - content lacks structure")
        elif analysis["paragraph_count"] < 3 and word_count > 300:
            analysis["recommendations"].append("Break content into more paragraphs for better readability")
        
        if word_count > 500 and analysis["list_count"] == 0:
            analysis["recommendations"].append("Consider adding lists to improve content structure")
        
        return analysis

    async def _analyze_images(self, soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
        """Analyze image optimization."""
        images = soup.find_all('img')
        
        analysis = {
            "total_images": len(images),
            "images_without_alt": 0,
            "images_with_empty_alt": 0,
            "images_without_title": 0,
            "large_images": [],
            "issues": [],
            "recommendations": []
        }
        
        for img in images:
            alt_text = img.get('alt', '')
            title_text = img.get('title', '')
            src = img.get('src', '')
            
            # Check alt attributes
            if not img.has_attr('alt'):
                analysis["images_without_alt"] += 1
            elif alt_text.strip() == '':
                analysis["images_with_empty_alt"] += 1
            
            # Check title attributes
            if not title_text:
                analysis["images_without_title"] += 1
        
        # Generate recommendations
        if analysis["images_without_alt"] > 0:
            analysis["issues"].append(f"{analysis['images_without_alt']} images missing alt attributes")
            analysis["recommendations"].append("Add alt text to all images for accessibility and SEO")
        
        if analysis["images_with_empty_alt"] > 0:
            analysis["issues"].append(f"{analysis['images_with_empty_alt']} images have empty alt attributes")
            analysis["recommendations"].append("Write descriptive alt text for images")
        
        if analysis["total_images"] > 0:
            analysis["recommendations"].append("Optimize image file sizes and use modern formats (WebP)")
        
        return analysis

    async def _analyze_internal_links(self, soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
        """Analyze internal linking structure."""
        base_domain = urlparse(base_url).netloc
        links = soup.find_all('a', href=True)
        
        analysis = {
            "total_links": len(links),
            "internal_links": 0,
            "external_links": 0,
            "nofollow_links": 0,
            "links_without_text": 0,
            "issues": [],
            "recommendations": []
        }
        
        for link in links:
            href = link.get('href', '')
            link_text = link.get_text().strip()
            rel = link.get('rel', [])
            
            if not link_text:
                analysis["links_without_text"] += 1
            
            if 'nofollow' in rel:
                analysis["nofollow_links"] += 1
            
            # Determine if internal or external
            if href.startswith('http'):
                link_domain = urlparse(href).netloc
                if link_domain == base_domain:
                    analysis["internal_links"] += 1
                else:
                    analysis["external_links"] += 1
            elif href.startswith('/') or not href.startswith(('http', 'mailto:', 'tel:')):
                analysis["internal_links"] += 1
        
        # Generate recommendations
        if analysis["links_without_text"] > 0:
            analysis["issues"].append(f"{analysis['links_without_text']} links without anchor text")
            analysis["recommendations"].append("Add descriptive anchor text to all links")
        
        if analysis["internal_links"] < 3:
            analysis["recommendations"].append("Add more internal links to improve site navigation and SEO")
        
        if analysis["internal_links"] > 0:
            analysis["recommendations"].append("Good internal linking structure")
        
        return analysis

    async def _analyze_keyword_optimization(self, soup: BeautifulSoup, target_keyword: str) -> Dict[str, Any]:
        """Analyze keyword optimization throughout the page."""
        keyword_lower = target_keyword.lower()
        
        analysis = {
            "keyword": target_keyword,
            "in_title": False,
            "in_meta_description": False,
            "in_h1": False,
            "in_headings": False,
            "in_url": False,
            "in_alt_text": False,
            "first_paragraph": False,
            "optimization_score": 0,
            "recommendations": []
        }
        
        # Check title
        title = soup.find('title')
        if title and keyword_lower in title.get_text().lower():
            analysis["in_title"] = True
        
        # Check meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and keyword_lower in meta_desc.get('content', '').lower():
            analysis["in_meta_description"] = True
        
        # Check H1
        h1 = soup.find('h1')
        if h1 and keyword_lower in h1.get_text().lower():
            analysis["in_h1"] = True
        
        # Check other headings
        for heading in soup.find_all(['h2', 'h3', 'h4', 'h5', 'h6']):
            if keyword_lower in heading.get_text().lower():
                analysis["in_headings"] = True
                break
        
        # Check alt text
        for img in soup.find_all('img', alt=True):
            if keyword_lower in img.get('alt', '').lower():
                analysis["in_alt_text"] = True
                break
        
        # Check first paragraph
        first_p = soup.find('p')
        if first_p and keyword_lower in first_p.get_text().lower():
            analysis["first_paragraph"] = True
        
        # Calculate optimization score
        checks = [
            analysis["in_title"],
            analysis["in_meta_description"], 
            analysis["in_h1"],
            analysis["in_headings"],
            analysis["first_paragraph"]
        ]
        analysis["optimization_score"] = (sum(checks) / len(checks)) * 100
        
        # Generate recommendations
        if not analysis["in_title"]:
            analysis["recommendations"].append("Include target keyword in title tag")
        if not analysis["in_meta_description"]:
            analysis["recommendations"].append("Include target keyword in meta description")
        if not analysis["in_h1"]:
            analysis["recommendations"].append("Include target keyword in H1 tag")
        if not analysis["first_paragraph"]:
            analysis["recommendations"].append("Include target keyword in first paragraph")
        
        return analysis

    async def _analyze_readability(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze content readability."""
        # Extract text content
        for script in soup(["script", "style"]):
            script.decompose()
        
        text_content = soup.get_text()
        sentences = re.split(r'[.!?]+', text_content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        words = text_content.split()
        word_count = len(words)
        sentence_count = len(sentences)
        
        analysis = {
            "word_count": word_count,
            "sentence_count": sentence_count,
            "avg_words_per_sentence": 0,
            "avg_syllables_per_word": 0,
            "flesch_reading_ease": 0,
            "readability_level": "",
            "recommendations": []
        }
        
        if sentence_count > 0:
            analysis["avg_words_per_sentence"] = word_count / sentence_count
        
        # Simple syllable counting
        total_syllables = 0
        for word in words:
            syllables = self._count_syllables(word)
            total_syllables += syllables
        
        if word_count > 0:
            analysis["avg_syllables_per_word"] = total_syllables / word_count
        
        # Flesch Reading Ease Score
        if sentence_count > 0 and word_count > 0:
            analysis["flesch_reading_ease"] = (
                206.835 - (1.015 * analysis["avg_words_per_sentence"]) 
                - (84.6 * analysis["avg_syllables_per_word"])
            )
            
            # Determine readability level
            if analysis["flesch_reading_ease"] >= 90:
                analysis["readability_level"] = "Very Easy"
            elif analysis["flesch_reading_ease"] >= 80:
                analysis["readability_level"] = "Easy"
            elif analysis["flesch_reading_ease"] >= 70:
                analysis["readability_level"] = "Fairly Easy"
            elif analysis["flesch_reading_ease"] >= 60:
                analysis["readability_level"] = "Standard"
            elif analysis["flesch_reading_ease"] >= 50:
                analysis["readability_level"] = "Fairly Difficult"
            elif analysis["flesch_reading_ease"] >= 30:
                analysis["readability_level"] = "Difficult"
            else:
                analysis["readability_level"] = "Very Difficult"
        
        # Generate recommendations
        if analysis["avg_words_per_sentence"] > 20:
            analysis["recommendations"].append("Break up long sentences to improve readability")
        
        if analysis["flesch_reading_ease"] < 60:
            analysis["recommendations"].append("Simplify language to improve readability")
        
        return analysis

    def _count_syllables(self, word: str) -> int:
        """Simple syllable counting algorithm."""
        word = word.lower()
        syllables = 0
        vowels = 'aeiouy'
        
        if len(word) == 0:
            return 0
        
        if word[0] in vowels:
            syllables += 1
        
        for i in range(1, len(word)):
            if word[i] in vowels and word[i-1] not in vowels:
                syllables += 1
        
        if word.endswith('e'):
            syllables -= 1
        
        if syllables == 0:
            syllables = 1
        
        return syllables

    def _calculate_onpage_score(self, results: Dict[str, Any]) -> float:
        """Calculate overall on-page SEO score."""
        score = 0
        max_score = 100
        
        # Title analysis (20 points)
        title = results.get("title_analysis", {})
        if title.get("title"):
            score += 10
        if title.get("length_status") == "optimal":
            score += 5
        if title.get("has_keyword"):
            score += 5
        
        # Meta description (15 points)
        meta = results.get("meta_description_analysis", {})
        if meta.get("description"):
            score += 10
        if meta.get("length_status") == "optimal":
            score += 5
        
        # Headings (20 points)
        headings = results.get("heading_analysis", {})
        if headings.get("h1_count") == 1:
            score += 10
        if headings.get("h1_has_keyword"):
            score += 5
        if not headings.get("heading_hierarchy_issues"):
            score += 5
        
        # Content (25 points)
        content = results.get("content_analysis", {})
        if content.get("word_count", 0) >= 300:
            score += 10
        if content.get("keyword_density", 0) > 0 and content.get("keyword_density", 0) <= 3:
            score += 10
        if content.get("paragraph_count", 0) > 0:
            score += 5
        
        # Images (10 points)
        images = results.get("image_analysis", {})
        if images.get("images_without_alt", 0) == 0 and images.get("total_images", 0) > 0:
            score += 10
        
        # Internal linking (10 points)
        links = results.get("internal_linking", {})
        if links.get("internal_links", 0) >= 3:
            score += 10
        
        return min(score, max_score)

    def _generate_onpage_recommendations(self, results: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Generate issues and recommendations from analysis results."""
        issues = []
        recommendations = []
        
        # Collect issues and recommendations from all analyses
        for analysis_key in results:
            if isinstance(results[analysis_key], dict):
                analysis = results[analysis_key]
                if "issues" in analysis:
                    issues.extend(analysis["issues"])
                if "recommendations" in analysis:
                    recommendations.extend(analysis["recommendations"])
        
        return issues, recommendations

    async def analyze_title_tags(self, url: str) -> Dict[str, Any]:
        """Focused title tag analysis."""
        response, error = await self._make_request(url)
        
        if error or not response:
            return {
                "url": url,
                "error": error or "Could not fetch page"
            }
        
        soup = BeautifulSoup(response.text, 'html.parser')
        analysis = await self._analyze_title_tag(soup)
        
        return {
            "url": url,
            "title_analysis": analysis
        }

    async def analyze_content_quality(self, url: str, include_readability: bool = True) -> Dict[str, Any]:
        """Focused content quality analysis."""
        response, error = await self._make_request(url)
        
        if error or not response:
            return {
                "url": url,
                "error": error or "Could not fetch page"
            }
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = {
            "url": url,
            "content_analysis": await self._analyze_content(soup),
            "heading_analysis": await self._analyze_headings(soup)
        }
        
        if include_readability:
            results["readability"] = await self._analyze_readability(soup)
        
        return results

    async def close(self):
        """Clean up resources."""
        if self.session:
            await self.session.aclose()