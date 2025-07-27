#!/usr/bin/env python3
"""
Setup script for SEO Auditor MCP Server
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("✗ Python 3.8 or higher is required")
        return False
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def check_node_installed():
    """Check if Node.js is installed."""
    try:
        result = subprocess.run("node --version", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Node.js detected: {result.stdout.strip()}")
            return True
    except:
        pass
    
    print("✗ Node.js not found - required for Lighthouse")
    print("Please install Node.js from: https://nodejs.org/")
    return False

def install_python_dependencies():
    """Install Python dependencies."""
    return run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Installing Python dependencies"
    )

def install_lighthouse():
    """Install Lighthouse via npm."""
    return run_command(
        "npm install -g lighthouse",
        "Installing Lighthouse globally via npm"
    )

def create_env_file():
    """Create .env file from template if it doesn't exist."""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        try:
            env_file.write_text(env_example.read_text())
            print("✓ Created .env file from template")
            print("Please edit .env file with your API keys and configuration")
            return True
        except Exception as e:
            print(f"✗ Failed to create .env file: {e}")
            return False
    elif env_file.exists():
        print("✓ .env file already exists")
        return True
    else:
        print("✗ .env.example template not found")
        return False

def initialize_database():
    """Initialize the database."""
    try:
        # Import and run database initialization
        import asyncio
        from database.models import init_database
        
        asyncio.run(init_database())
        print("✓ Database initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return False

def test_installation():
    """Test basic functionality."""
    try:
        # Try importing main components
        from analyzers.site_crawler import SiteCrawler
        from analyzers.technical_seo import TechnicalSEOAnalyzer
        from analyzers.performance import PerformanceAnalyzer
        from analyzers.onpage_seo import OnPageSEOAnalyzer
        from database.models import init_database
        
        print("✓ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import test failed: {e}")
        return False

def main():
    """Main setup function."""
    print("SEO Auditor MCP Server Setup")
    print("=" * 40)
    
    # Check prerequisites
    if not check_python_version():
        sys.exit(1)
    
    if not check_node_installed():
        print("Warning: Lighthouse features will not work without Node.js")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Install dependencies
    success = True
    
    success &= install_python_dependencies()
    
    if check_node_installed():
        success &= install_lighthouse()
    
    success &= create_env_file()
    success &= initialize_database()
    success &= test_installation()
    
    print("\n" + "=" * 40)
    
    if success:
        print("✓ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Edit .env file with your API keys")
        print("2. Add server to your Claude Code configuration")
        print("3. Run: python server.py")
        print("\nFor detailed usage instructions, see README.md")
    else:
        print("✗ Setup completed with errors")
        print("Please check the error messages above and resolve any issues")
        sys.exit(1)

if __name__ == "__main__":
    main()