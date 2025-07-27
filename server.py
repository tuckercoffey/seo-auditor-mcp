#!/usr/bin/env python3
"""
SEO Auditor MCP Server
Comprehensive SEO auditing and analysis tools for LLMs
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Sequence
from dataclasses import dataclass
import json

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
import mcp.types as types

from analyzers.site_crawler import SiteCrawler
from analyzers.technical_seo import TechnicalSEOAnalyzer
from analyzers.performance import PerformanceAnalyzer
from analyzers.onpage_seo import OnPageSEOAnalyzer
from database.models import AuditResult, init_database
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seo-auditor")

# Initialize the MCP server
server = Server("seo-auditor")

# Global analyzers
site_crawler = SiteCrawler()
technical_analyzer = TechnicalSEOAnalyzer()
performance_analyzer = PerformanceAnalyzer()
onpage_analyzer = OnPageSEOAnalyzer()

@server.list_resources()
async def handle_list_resources() -> List[Resource]:
    """List available SEO resources and knowledge base."""
    return [
        Resource(
            uri="seo://best-practices/technical",
            name="Technical SEO Guidelines",
            description="Current technical SEO best practices and recommendations",
            mimeType="text/plain"
        ),
        Resource(
            uri="seo://best-practices/onpage",
            name="On-Page SEO Guidelines",
            description="On-page optimization best practices",
            mimeType="text/plain"
        ),
        Resource(
            uri="seo://audit-history",
            name="Audit History",
            description="Historical audit results and trends",
            mimeType="application/json"
        )
    ]

@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read SEO resources and knowledge base content."""
    if uri == "seo://best-practices/technical":
        return """Technical SEO Best Practices:
1. Ensure proper robots.txt configuration
2. Optimize XML sitemaps for search engines
3. Fix crawl errors and broken links
4. Implement proper URL structure and canonicalization
5. Optimize site speed and Core Web Vitals
6. Ensure mobile-first indexing compatibility
7. Implement proper structured data markup
8. Secure site with HTTPS and proper headers"""
    
    elif uri == "seo://best-practices/onpage":
        return """On-Page SEO Best Practices:
1. Optimize title tags (50-60 characters)
2. Write compelling meta descriptions (150-160 characters)
3. Use proper heading hierarchy (H1-H6)
4. Optimize content for target keywords
5. Implement internal linking strategy
6. Optimize images with alt tags
7. Ensure content quality and readability
8. Target user search intent"""
    
    elif uri == "seo://audit-history":
        # Return audit history from database
        return json.dumps({"message": "Audit history feature coming soon"})
    
    else:
        raise ValueError(f"Unknown resource: {uri}")

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List all available SEO audit tools."""
    return [
        # Site Crawling & Discovery Tools
        Tool(
            name="crawl_site",
            description="Discover and crawl all pages on a website",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Website URL to crawl"},
                    "max_pages": {"type": "number", "default": 100, "description": "Maximum pages to crawl"},
                    "depth": {"type": "number", "default": 3, "description": "Maximum crawl depth"}
                },
                "required": ["url"]
            }
        ),
        
        Tool(
            name="check_robots_txt",
            description="Analyze robots.txt file and crawling rules",
            inputSchema={
                "type": "object", 
                "properties": {
                    "url": {"type": "string", "description": "Website URL"}
                },
                "required": ["url"]
            }
        ),
        
        Tool(
            name="check_sitemap",
            description="Validate and analyze XML sitemaps",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Website URL or sitemap URL"}
                },
                "required": ["url"]
            }
        ),
        
        Tool(
            name="find_broken_links",
            description="Identify broken links and redirect chains",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Website URL to analyze"}
                },
                "required": ["url"]
            }
        ),
        
        # Technical SEO Tools
        Tool(
            name="analyze_technical_seo",
            description="Comprehensive technical SEO analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to analyze"},
                    "include_security": {"type": "boolean", "default": True}
                },
                "required": ["url"]
            }
        ),
        
        Tool(
            name="check_mobile_friendliness",
            description="Test mobile usability and responsiveness",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to test"}
                },
                "required": ["url"]
            }
        ),
        
        Tool(
            name="analyze_structured_data",
            description="Validate Schema.org markup and structured data",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to analyze"}
                },
                "required": ["url"]
            }
        ),
        
        # Performance & Core Web Vitals Tools
        Tool(
            name="measure_core_web_vitals",
            description="Measure Core Web Vitals metrics",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to test"},
                    "device": {"type": "string", "enum": ["mobile", "desktop"], "default": "mobile"},
                    "runs": {"type": "number", "default": 3, "description": "Number of test runs"}
                },
                "required": ["url"]
            }
        ),
        
        Tool(
            name="lighthouse_audit",
            description="Run comprehensive Lighthouse performance audit",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to audit"},
                    "device": {"type": "string", "enum": ["mobile", "desktop"], "default": "mobile"},
                    "categories": {
                        "type": "array",
                        "items": {"enum": ["performance", "accessibility", "best-practices", "seo"]},
                        "default": ["performance", "seo"]
                    }
                },
                "required": ["url"]
            }
        ),
        
        # On-Page SEO Tools
        Tool(
            name="analyze_onpage_seo",
            description="Comprehensive on-page SEO analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to analyze"},
                    "target_keyword": {"type": "string", "description": "Primary target keyword"}
                },
                "required": ["url"]
            }
        ),
        
        Tool(
            name="analyze_title_tags",
            description="Analyze title tag optimization",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to analyze"}
                },
                "required": ["url"]
            }
        ),
        
        Tool(
            name="analyze_content_quality",
            description="Analyze content quality and readability",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to analyze"},
                    "include_readability": {"type": "boolean", "default": True}
                },
                "required": ["url"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls for SEO analysis."""
    
    try:
        if name == "crawl_site":
            result = await site_crawler.crawl_site(
                url=arguments["url"],
                max_pages=arguments.get("max_pages", 100),
                depth=arguments.get("depth", 3)
            )
            
        elif name == "check_robots_txt":
            result = await site_crawler.check_robots_txt(arguments["url"])
            
        elif name == "check_sitemap":
            result = await site_crawler.check_sitemap(arguments["url"])
            
        elif name == "find_broken_links":
            result = await site_crawler.find_broken_links(arguments["url"])
            
        elif name == "analyze_technical_seo":
            result = await technical_analyzer.analyze_technical_seo(
                url=arguments["url"],
                include_security=arguments.get("include_security", True)
            )
            
        elif name == "check_mobile_friendliness":
            result = await technical_analyzer.check_mobile_friendliness(arguments["url"])
            
        elif name == "analyze_structured_data":
            result = await technical_analyzer.analyze_structured_data(arguments["url"])
            
        elif name == "measure_core_web_vitals":
            result = await performance_analyzer.measure_core_web_vitals(
                url=arguments["url"],
                device=arguments.get("device", "mobile"),
                runs=arguments.get("runs", 3)
            )
            
        elif name == "lighthouse_audit":
            result = await performance_analyzer.lighthouse_audit(
                url=arguments["url"],
                device=arguments.get("device", "mobile"),
                categories=arguments.get("categories", ["performance", "seo"])
            )
            
        elif name == "analyze_onpage_seo":
            result = await onpage_analyzer.analyze_onpage_seo(
                url=arguments["url"],
                target_keyword=arguments.get("target_keyword")
            )
            
        elif name == "analyze_title_tags":
            result = await onpage_analyzer.analyze_title_tags(arguments["url"])
            
        elif name == "analyze_content_quality":
            result = await onpage_analyzer.analyze_content_quality(
                url=arguments["url"],
                include_readability=arguments.get("include_readability", True)
            )
            
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        logger.error(f"Error in tool {name}: {str(e)}")
        return [types.TextContent(
            type="text", 
            text=f"Error executing {name}: {str(e)}"
        )]

async def main():
    """Main function to run the MCP server."""
    # Initialize database
    await init_database()
    
    # Run the server using stdin/stdout streams
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="seo-auditor",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())