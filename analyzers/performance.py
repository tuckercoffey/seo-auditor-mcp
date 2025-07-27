"""
Performance analyzer for Core Web Vitals and page speed testing
Handles Lighthouse audits, performance metrics, and optimization recommendations
"""

import asyncio
import json
import subprocess
import tempfile
import httpx
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
from urllib.parse import urlparse

from config import Config
from database.models import PerformanceResult, save_performance_result

logger = logging.getLogger(__name__)

class PerformanceAnalyzer:
    """Analyzer for website performance and Core Web Vitals."""
    
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

    async def measure_core_web_vitals(self, url: str, device: str = "mobile", runs: int = 3) -> Dict[str, Any]:
        """
        Measure Core Web Vitals metrics using multiple approaches.
        
        Args:
            url: URL to test
            device: 'mobile' or 'desktop'
            runs: Number of test runs to average
            
        Returns:
            Dict containing Core Web Vitals measurements
        """
        logger.info(f"Measuring Core Web Vitals for {url} on {device}")
        
        results = {
            "url": url,
            "device": device,
            "timestamp": datetime.now().isoformat(),
            "runs": runs,
            "metrics": {
                "lcp": {"values": [], "average": 0, "rating": ""},
                "fid": {"values": [], "average": 0, "rating": ""},
                "cls": {"values": [], "average": 0, "rating": ""},
                "fcp": {"values": [], "average": 0, "rating": ""},
                "ttfb": {"values": [], "average": 0, "rating": ""}
            },
            "field_data": {},
            "recommendations": []
        }
        
        # Try to get field data from Google PageSpeed Insights API
        if Config.GOOGLE_API_KEY:
            field_data = await self._get_crux_data(url, device)
            results["field_data"] = field_data
        
        # Run multiple performance tests
        for run in range(runs):
            logger.info(f"Running performance test {run + 1}/{runs}")
            
            try:
                # Use Lighthouse for lab data
                lighthouse_data = await self._run_lighthouse_performance(url, device)
                
                if lighthouse_data:
                    # Extract Core Web Vitals from Lighthouse
                    lcp = lighthouse_data.get("largest-contentful-paint", {}).get("numericValue", 0)
                    cls = lighthouse_data.get("cumulative-layout-shift", {}).get("numericValue", 0)
                    fcp = lighthouse_data.get("first-contentful-paint", {}).get("numericValue", 0)
                    
                    if lcp > 0:
                        results["metrics"]["lcp"]["values"].append(lcp / 1000)  # Convert to seconds
                    if cls >= 0:
                        results["metrics"]["cls"]["values"].append(cls)
                    if fcp > 0:
                        results["metrics"]["fcp"]["values"].append(fcp / 1000)  # Convert to seconds
                    
                    # Note: FID cannot be measured in lab conditions, using TBT as proxy
                    tbt = lighthouse_data.get("total-blocking-time", {}).get("numericValue", 0)
                    if tbt > 0:
                        results["metrics"]["fid"]["values"].append(tbt / 1000)  # Convert to seconds
                
            except Exception as e:
                logger.error(f"Error in performance test run {run + 1}: {str(e)}")
                continue
                
            # Add delay between runs
            if run < runs - 1:
                await asyncio.sleep(2)
        
        # Calculate averages and ratings
        for metric_name, metric_data in results["metrics"].items():
            if metric_data["values"]:
                metric_data["average"] = sum(metric_data["values"]) / len(metric_data["values"])
                metric_data["rating"] = self._rate_metric(metric_name, metric_data["average"])
        
        # Generate recommendations
        results["recommendations"] = self._generate_performance_recommendations(results)
        
        # Save to database
        perf_result = PerformanceResult(
            url=url,
            device=device,
            lcp=results["metrics"]["lcp"]["average"] if results["metrics"]["lcp"]["values"] else None,
            fid=results["metrics"]["fid"]["average"] if results["metrics"]["fid"]["values"] else None,
            cls=results["metrics"]["cls"]["average"] if results["metrics"]["cls"]["values"] else None,
            fcp=results["metrics"]["fcp"]["average"] if results["metrics"]["fcp"]["values"] else None,
            lighthouse_score=None,  # Will be set by lighthouse_audit
            timestamp=datetime.now()
        )
        await save_performance_result(perf_result)
        
        return results

    async def _get_crux_data(self, url: str, device: str) -> Dict[str, Any]:
        """Get Chrome User Experience Report (CrUX) field data from PageSpeed Insights API."""
        try:
            api_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
            params = {
                "url": url,
                "key": Config.GOOGLE_API_KEY,
                "strategy": device.upper(),
                "category": "PERFORMANCE"
            }
            
            session = await self._get_session()
            response = await session.get(api_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                crux_data = data.get("loadingExperience", {}).get("metrics", {})
                
                field_metrics = {}
                
                # Extract CrUX metrics
                for metric_name, metric_data in crux_data.items():
                    if metric_name in ["LARGEST_CONTENTFUL_PAINT_MS", "FIRST_INPUT_DELAY_MS", 
                                     "CUMULATIVE_LAYOUT_SHIFT_SCORE", "FIRST_CONTENTFUL_PAINT_MS"]:
                        
                        percentile = metric_data.get("percentile", 0)
                        category = metric_data.get("category", "")
                        
                        field_metrics[metric_name] = {
                            "percentile": percentile,
                            "category": category.lower()
                        }
                
                return field_metrics
                
        except Exception as e:
            logger.error(f"Error fetching CrUX data: {str(e)}")
            
        return {}

    async def _run_lighthouse_performance(self, url: str, device: str = "mobile") -> Optional[Dict[str, Any]]:
        """Run Lighthouse performance audit."""
        try:
            # Create temporary file for Lighthouse output
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as tmp_file:
                output_path = tmp_file.name
            
            # Build Lighthouse command
            cmd = [
                "lighthouse",
                url,
                "--only-categories=performance",
                "--output=json",
                f"--output-path={output_path}",
                "--quiet",
                "--no-enable-error-reporting"
            ]
            
            # Add device-specific flags
            if device == "mobile":
                cmd.extend([
                    "--preset=perf",
                    "--emulated-form-factor=mobile",
                    "--throttling-method=simulate"
                ])
            else:
                cmd.extend([
                    "--preset=desktop",
                    "--emulated-form-factor=desktop",
                    "--throttling-method=simulate"
                ])
            
            # Add Chrome flags
            cmd.extend([f"--chrome-flags={' '.join(Config.LIGHTHOUSE_CHROME_FLAGS)}"])
            
            # Run Lighthouse
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # Read results
                with open(output_path, 'r') as f:
                    lighthouse_data = json.load(f)
                
                # Extract performance metrics
                audits = lighthouse_data.get("audits", {})
                return audits
            else:
                logger.error(f"Lighthouse failed: {stderr.decode()}")
                return None
                
        except Exception as e:
            logger.error(f"Error running Lighthouse: {str(e)}")
            return None

    async def lighthouse_audit(self, url: str, device: str = "mobile", 
                              categories: List[str] = None) -> Dict[str, Any]:
        """
        Run comprehensive Lighthouse audit.
        
        Args:
            url: URL to audit
            device: 'mobile' or 'desktop'
            categories: List of categories to audit (performance, accessibility, best-practices, seo)
            
        Returns:
            Dict containing full Lighthouse audit results
        """
        if categories is None:
            categories = ["performance", "seo"]
            
        logger.info(f"Running Lighthouse audit for {url}")
        
        try:
            # Create temporary file for Lighthouse output
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as tmp_file:
                output_path = tmp_file.name
            
            # Build command
            cmd = [
                "lighthouse",
                url,
                f"--only-categories={','.join(categories)}",
                "--output=json",
                f"--output-path={output_path}",
                "--quiet",
                "--no-enable-error-reporting"
            ]
            
            # Device-specific settings
            if device == "mobile":
                cmd.extend([
                    "--preset=perf",
                    "--emulated-form-factor=mobile"
                ])
            else:
                cmd.extend([
                    "--preset=desktop", 
                    "--emulated-form-factor=desktop"
                ])
            
            cmd.extend([f"--chrome-flags={' '.join(Config.LIGHTHOUSE_CHROME_FLAGS)}"])
            
            # Run Lighthouse
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=None
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                return {
                    "url": url,
                    "error": f"Lighthouse failed: {stderr.decode()}",
                    "device": device
                }
            
            # Read and parse results
            with open(output_path, 'r') as f:
                lighthouse_data = json.load(f)
            
            # Extract key information
            results = {
                "url": url,
                "device": device,
                "timestamp": datetime.now().isoformat(),
                "scores": {},
                "metrics": {},
                "opportunities": [],
                "diagnostics": [],
                "passed_audits": [],
                "failed_audits": []
            }
            
            # Extract scores
            category_results = lighthouse_data.get("categories", {})
            for category_name, category_data in category_results.items():
                results["scores"][category_name] = {
                    "score": category_data.get("score", 0) * 100,  # Convert to percentage
                    "title": category_data.get("title", "")
                }
            
            # Extract performance metrics
            audits = lighthouse_data.get("audits", {})
            
            performance_metrics = [
                "first-contentful-paint",
                "largest-contentful-paint", 
                "cumulative-layout-shift",
                "total-blocking-time",
                "speed-index"
            ]
            
            for metric in performance_metrics:
                if metric in audits:
                    audit_data = audits[metric]
                    results["metrics"][metric] = {
                        "value": audit_data.get("numericValue", 0),
                        "displayValue": audit_data.get("displayValue", ""),
                        "score": audit_data.get("score", 0)
                    }
            
            # Extract opportunities (performance improvements)
            for audit_id, audit_data in audits.items():
                if audit_data.get("scoreDisplayMode") == "numeric" and audit_data.get("score", 1) < 0.9:
                    opportunity = {
                        "id": audit_id,
                        "title": audit_data.get("title", ""),
                        "description": audit_data.get("description", ""),
                        "score": audit_data.get("score", 0),
                        "displayValue": audit_data.get("displayValue", "")
                    }
                    
                    # Add potential savings if available
                    details = audit_data.get("details", {})
                    if "overallSavingsMs" in details:
                        opportunity["savings_ms"] = details["overallSavingsMs"]
                    
                    results["opportunities"].append(opportunity)
            
            # Separate passed and failed audits
            for audit_id, audit_data in audits.items():
                if audit_data.get("scoreDisplayMode") == "binary":
                    audit_info = {
                        "id": audit_id,
                        "title": audit_data.get("title", ""),
                        "description": audit_data.get("description", "")
                    }
                    
                    if audit_data.get("score") == 1:
                        results["passed_audits"].append(audit_info)
                    else:
                        results["failed_audits"].append(audit_info)
            
            return results
            
        except Exception as e:
            logger.error(f"Error running Lighthouse audit: {str(e)}")
            return {
                "url": url,
                "error": str(e),
                "device": device
            }

    def _rate_metric(self, metric_name: str, value: float) -> str:
        """Rate a performance metric as good, needs improvement, or poor."""
        if metric_name == "lcp":  # Largest Contentful Paint (seconds)
            if value <= 2.5:
                return "good"
            elif value <= 4.0:
                return "needs_improvement"
            else:
                return "poor"
                
        elif metric_name == "fcp":  # First Contentful Paint (seconds)
            if value <= 1.8:
                return "good"
            elif value <= 3.0:
                return "needs_improvement"
            else:
                return "poor"
                
        elif metric_name == "cls":  # Cumulative Layout Shift
            if value <= 0.1:
                return "good"
            elif value <= 0.25:
                return "needs_improvement"
            else:
                return "poor"
                
        elif metric_name == "fid":  # First Input Delay (seconds) - using TBT as proxy
            if value <= 0.1:
                return "good"
            elif value <= 0.3:
                return "needs_improvement"
            else:
                return "poor"
                
        elif metric_name == "ttfb":  # Time to First Byte (seconds)
            if value <= 0.8:
                return "good"
            elif value <= 1.8:
                return "needs_improvement"
            else:
                return "poor"
        
        return "unknown"

    def _generate_performance_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate performance optimization recommendations."""
        recommendations = []
        metrics = results.get("metrics", {})
        
        # LCP recommendations
        lcp = metrics.get("lcp", {})
        if lcp.get("rating") in ["needs_improvement", "poor"]:
            recommendations.extend([
                "Optimize server response times and use a CDN",
                "Optimize images and use next-gen formats (WebP, AVIF)",
                "Remove unused CSS and JavaScript",
                "Use resource hints (preload, prefetch) for critical resources"
            ])
        
        # CLS recommendations
        cls = metrics.get("cls", {})
        if cls.get("rating") in ["needs_improvement", "poor"]:
            recommendations.extend([
                "Set explicit dimensions for images and videos",
                "Avoid inserting content above existing content",
                "Use CSS transforms instead of animating layout properties",
                "Preload fonts and use font-display: swap"
            ])
        
        # FCP recommendations
        fcp = metrics.get("fcp", {})
        if fcp.get("rating") in ["needs_improvement", "poor"]:
            recommendations.extend([
                "Eliminate render-blocking resources",
                "Minify CSS and JavaScript",
                "Remove unused code",
                "Use efficient cache policies"
            ])
        
        # FID/Interactivity recommendations
        fid = metrics.get("fid", {})
        if fid.get("rating") in ["needs_improvement", "poor"]:
            recommendations.extend([
                "Break up long JavaScript tasks",
                "Optimize third-party code",
                "Use web workers for heavy computations",
                "Implement code splitting and lazy loading"
            ])
        
        # General recommendations if no specific issues
        if not recommendations:
            recommendations = [
                "Continue monitoring Core Web Vitals",
                "Consider implementing performance budgets",
                "Optimize images and use modern formats",
                "Enable compression (gzip/brotli)"
            ]
        
        return list(set(recommendations))  # Remove duplicates

    async def analyze_render_blocking(self, url: str) -> Dict[str, Any]:
        """Analyze render-blocking resources."""
        try:
            # This would typically use Lighthouse or browser automation
            # For now, we'll do a basic analysis of the HTML
            session = await self._get_session()
            response = await session.get(url)
            
            if response.status_code != 200:
                return {"error": f"HTTP {response.status_code}"}
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            blocking_resources = {
                "stylesheets": [],
                "scripts": [],
                "recommendations": []
            }
            
            # Find render-blocking stylesheets
            for link in soup.find_all('link', rel='stylesheet'):
                href = link.get('href')
                if href and not link.get('media'):  # No media query = render blocking
                    blocking_resources["stylesheets"].append(href)
            
            # Find render-blocking scripts
            for script in soup.find_all('script', src=True):
                if not script.get('async') and not script.get('defer'):
                    blocking_resources["scripts"].append(script.get('src'))
            
            # Generate recommendations
            if blocking_resources["stylesheets"]:
                blocking_resources["recommendations"].append(
                    f"Consider inlining critical CSS and deferring {len(blocking_resources['stylesheets'])} non-critical stylesheets"
                )
            
            if blocking_resources["scripts"]:
                blocking_resources["recommendations"].append(
                    f"Add async or defer attributes to {len(blocking_resources['scripts'])} non-critical scripts"
                )
            
            return {
                "url": url,
                "blocking_resources": blocking_resources,
                "total_blocking": len(blocking_resources["stylesheets"]) + len(blocking_resources["scripts"])
            }
            
        except Exception as e:
            return {"error": str(e)}

    async def close(self):
        """Clean up resources."""
        if self.session:
            await self.session.aclose()