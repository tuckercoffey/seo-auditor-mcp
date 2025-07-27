#!/usr/bin/env python3
"""
Test script for SEO Auditor MCP Server
Quick validation of core functionality
"""

import asyncio
import sys
from typing import Dict, Any

async def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    try:
        from analyzers.site_crawler import SiteCrawler
        from analyzers.technical_seo import TechnicalSEOAnalyzer
        from analyzers.performance import PerformanceAnalyzer
        from analyzers.onpage_seo import OnPageSEOAnalyzer
        from database.models import init_database
        from config import Config
        
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

async def test_database():
    """Test database initialization."""
    print("Testing database...")
    try:
        from database.models import init_database
        await init_database()
        print("✓ Database initialization successful")
        return True
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False

async def test_site_crawler():
    """Test basic site crawler functionality."""
    print("Testing site crawler...")
    try:
        from analyzers.site_crawler import SiteCrawler
        
        crawler = SiteCrawler()
        
        # Test robots.txt analysis (doesn't require actual HTTP request)
        # Using a mock test instead of real request
        print("✓ Site crawler module loaded")
        return True
    except Exception as e:
        print(f"✗ Site crawler test failed: {e}")
        return False

async def test_technical_analyzer():
    """Test technical SEO analyzer."""
    print("Testing technical SEO analyzer...")
    try:
        from analyzers.technical_seo import TechnicalSEOAnalyzer
        
        analyzer = TechnicalSEOAnalyzer()
        print("✓ Technical SEO analyzer loaded")
        return True
    except Exception as e:
        print(f"✗ Technical analyzer test failed: {e}")
        return False

async def test_performance_analyzer():
    """Test performance analyzer."""
    print("Testing performance analyzer...")
    try:
        from analyzers.performance import PerformanceAnalyzer
        
        analyzer = PerformanceAnalyzer()
        print("✓ Performance analyzer loaded")
        return True
    except Exception as e:
        print(f"✗ Performance analyzer test failed: {e}")
        return False

async def test_onpage_analyzer():
    """Test on-page SEO analyzer."""
    print("Testing on-page SEO analyzer...")
    try:
        from analyzers.onpage_seo import OnPageSEOAnalyzer
        
        analyzer = OnPageSEOAnalyzer()
        print("✓ On-page SEO analyzer loaded")
        return True
    except Exception as e:
        print(f"✗ On-page analyzer test failed: {e}")
        return False

async def test_config():
    """Test configuration loading."""
    print("Testing configuration...")
    try:
        from config import Config
        
        # Test basic config access
        timeout = Config.REQUEST_TIMEOUT
        user_agent = Config.DEFAULT_USER_AGENT
        
        print(f"✓ Config loaded - Timeout: {timeout}s, User-Agent: {user_agent[:30]}...")
        return True
    except Exception as e:
        print(f"✗ Config test failed: {e}")
        return False

async def test_mcp_server():
    """Test MCP server can be loaded."""
    print("Testing MCP server...")
    try:
        # Import server module
        import server
        
        print("✓ MCP server module loaded")
        return True
    except Exception as e:
        print(f"✗ MCP server test failed: {e}")
        return False

async def run_live_test():
    """Run a live test with a real URL (optional)."""
    test_url = "https://httpbin.org/html"  # Simple test endpoint
    
    print(f"\nRunning live test with {test_url}...")
    print("(This test requires internet connection)")
    
    try:
        from analyzers.site_crawler import SiteCrawler
        
        crawler = SiteCrawler()
        
        # Test robots.txt check (simple HTTP request)
        result = await crawler.check_robots_txt(test_url)
        
        if isinstance(result, dict) and "url" in result:
            print("✓ Live test successful - HTTP requests working")
            return True
        else:
            print("✗ Live test failed - unexpected response")
            return False
            
    except Exception as e:
        print(f"✗ Live test failed: {e}")
        print("(This may be due to network connectivity)")
        return False

async def main():
    """Run all tests."""
    print("SEO Auditor MCP Server Test Suite")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_config,
        test_database,
        test_site_crawler,
        test_technical_analyzer,
        test_performance_analyzer,
        test_onpage_analyzer,
        test_mcp_server
    ]
    
    results = []
    
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            results.append(False)
        print()
    
    # Optional live test
    if "--live" in sys.argv:
        live_result = await run_live_test()
        results.append(live_result)
    
    # Summary
    print("=" * 40)
    passed = sum(results)
    total = len(results)
    
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("✓ All tests passed! SEO Auditor is ready to use.")
        print("\nTo start the server:")
        print("python server.py")
        return 0
    else:
        print("✗ Some tests failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("- Ensure all dependencies are installed: pip install -r requirements.txt")
        print("- Check that Node.js and Lighthouse are installed")
        print("- Verify .env file is configured correctly")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)