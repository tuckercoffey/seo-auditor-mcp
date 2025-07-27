"""
Configuration management for SEO Auditor MCP Server
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration settings for the SEO auditor."""
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///seo_auditor.db")
    
    # API Keys
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    GOOGLE_SEARCH_CONSOLE_CREDENTIALS = os.getenv("GSC_CREDENTIALS")
    AHREFS_API_KEY = os.getenv("AHREFS_API_KEY")
    SEMRUSH_API_KEY = os.getenv("SEMRUSH_API_KEY")
    
    # Rate Limiting
    REQUESTS_PER_SECOND = int(os.getenv("REQUESTS_PER_SECOND", "2"))
    MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))
    
    # Crawling Settings
    DEFAULT_USER_AGENT = os.getenv(
        "USER_AGENT", 
        "SEO-Auditor-Bot/1.0 (+https://github.com/your-org/seo-auditor)"
    )
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
    MAX_REDIRECTS = int(os.getenv("MAX_REDIRECTS", "5"))
    
    # Performance Testing
    LIGHTHOUSE_CHROME_FLAGS = [
        "--headless",
        "--no-sandbox",
        "--disable-gpu"
    ]
    
    # Cache Settings
    CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))  # 1 hour
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration settings."""
        required_vars = []
        missing_vars = []
        
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"Warning: Missing configuration variables: {', '.join(missing_vars)}")
            return False
        
        return True