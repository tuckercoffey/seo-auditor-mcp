# SEO Auditor MCP Server

A comprehensive SEO auditing and analysis MCP (Model Context Protocol) server that provides LLMs with professional-grade SEO tools and insights.

## Features

### Core SEO Analysis
- **Site Crawling & Discovery**: Comprehensive website crawling, robots.txt analysis, sitemap validation, and broken link detection
- **Technical SEO**: HTTPS analysis, mobile-friendliness, structured data validation, canonical URLs, and security headers
- **Performance Analysis**: Core Web Vitals measurement, Lighthouse audits, and performance optimization recommendations
- **On-Page SEO**: Content analysis, title tags, meta descriptions, heading structure, keyword optimization, and readability scoring

### Advanced Capabilities
- **Real-time Analysis**: Live performance and SEO metrics
- **Historical Tracking**: Audit history and trend analysis
- **Competitive Intelligence**: Compare against competitors (coming soon)
- **Local SEO**: Local search optimization analysis (coming soon)
- **Content Strategy**: Gap analysis and content recommendations (coming soon)

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/seo-auditor-mcp.git
   cd seo-auditor-mcp
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Lighthouse** (required for performance analysis):
   ```bash
   npm install -g lighthouse
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

## Configuration

### Required Dependencies
- Python 3.8+
- Node.js and npm (for Lighthouse)
- Chrome/Chromium browser

### Optional API Keys
- **Google API Key**: Enables PageSpeed Insights and Chrome UX Report data
- **Google Search Console**: Access to search performance data
- **Ahrefs API**: Advanced backlink and keyword analysis
- **SEMrush API**: Competitive analysis and keyword research

### MCP Configuration

Add to your Claude Code configuration:

```json
{
  "mcpServers": {
    "seo-auditor": {
      "command": "python",
      "args": ["path/to/seo-auditor-mcp/server.py"],
      "env": {
        "GOOGLE_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## Usage

### Available Tools

#### Site Crawling & Discovery
- `crawl_site(url, max_pages?, depth?)` - Discover and crawl website pages
- `check_robots_txt(url)` - Analyze robots.txt configuration
- `check_sitemap(url)` - Validate XML sitemaps
- `find_broken_links(url)` - Identify broken links and redirects

#### Technical SEO
- `analyze_technical_seo(url, include_security?)` - Comprehensive technical analysis
- `check_mobile_friendliness(url)` - Mobile usability testing
- `analyze_structured_data(url)` - Schema.org markup validation

#### Performance & Core Web Vitals
- `measure_core_web_vitals(url, device?, runs?)` - Measure LCP, FID, CLS
- `lighthouse_audit(url, device?, categories?)` - Full Lighthouse audit

#### On-Page SEO
- `analyze_onpage_seo(url, target_keyword?)` - Comprehensive on-page analysis
- `analyze_title_tags(url)` - Title tag optimization
- `analyze_content_quality(url, include_readability?)` - Content analysis

### Slash Commands
- `/seo-audit <url>` - Complete comprehensive audit
- `/performance-audit <url>` - Focus on speed and Core Web Vitals
- `/technical-audit <url>` - Technical SEO analysis
- `/content-audit <url>` - On-page and content analysis

### Example Usage

```bash
# Complete SEO audit
/seo-audit https://example.com

# Performance-focused analysis
measure_core_web_vitals https://example.com mobile 3

# Technical SEO analysis
analyze_technical_seo https://example.com true

# On-page optimization
analyze_onpage_seo https://example.com "target keyword"
```

## Architecture

```
seo-auditor-mcp/
├── server.py              # Main MCP server
├── config.py              # Configuration management
├── analyzers/             # Core analysis modules
│   ├── site_crawler.py    # Site crawling and discovery
│   ├── technical_seo.py   # Technical SEO analysis
│   ├── performance.py     # Performance and Core Web Vitals
│   └── onpage_seo.py      # On-page SEO analysis
├── database/              # Data persistence
│   └── models.py          # Database models and operations
└── requirements.txt       # Python dependencies
```

## Data Storage

The server uses SQLite by default for storing:
- Audit results and history
- Performance metrics over time
- Crawl results and site structure
- Site tracking and monitoring data

## Rate Limiting

The server implements responsible crawling:
- Configurable requests per second (default: 2/sec)
- Respects robots.txt directives
- Implements delays between requests
- Concurrent request limiting

## Security & Privacy

- No data is sent to external services without explicit API configuration
- Local processing for most analysis functions
- Secure handling of API keys via environment variables
- Option to disable external API calls entirely

## Development

### Adding New Tools

1. Create analyzer method in appropriate module
2. Add tool definition to `server.py`
3. Register tool handler in `handle_call_tool()`
4. Update documentation

### Running Tests

```bash
# Run with sample data
python server.py --test-mode

# Analyze specific URL
python -c "from analyzers.technical_seo import TechnicalSEOAnalyzer; import asyncio; print(asyncio.run(TechnicalSEOAnalyzer().analyze_technical_seo('https://example.com')))"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

- GitHub Issues: Report bugs and feature requests
- Documentation: See docs/ directory for detailed guides
- Examples: Check examples/ directory for usage patterns