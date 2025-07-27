#!/usr/bin/env python3
"""
SEO Auditor MCP Server - Claude Code CLI Installer
One-command installation for Claude Code integration
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Optional
import argparse

def get_claude_config_path() -> Path:
    """Get the Claude Code configuration directory path."""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        config_dir = Path.home() / "Library" / "Application Support" / "Claude"
    elif system == "Windows":
        config_dir = Path(os.getenv("APPDATA", "")) / "Claude"
    else:  # Linux and others
        config_dir = Path.home() / ".config" / "Claude"
    
    return config_dir

def get_claude_config_file() -> Path:
    """Get the Claude Code MCP configuration file path."""
    return get_claude_config_path() / "claude_desktop_config.json"

def load_claude_config() -> Dict:
    """Load existing Claude Code configuration."""
    config_file = get_claude_config_file()
    
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            print("Warning: Existing config file is corrupted, creating new one")
    
    return {"mcpServers": {}}

def save_claude_config(config: Dict) -> None:
    """Save Claude Code configuration."""
    config_file = get_claude_config_file()
    config_dir = config_file.parent
    
    # Create config directory if it doesn't exist
    config_dir.mkdir(parents=True, exist_ok=True)
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)

def install_from_git(repo_url: str, install_dir: Path, api_keys: Dict[str, str] = None) -> bool:
    """Install SEO Auditor from Git repository."""
    print(f"Installing SEO Auditor MCP Server from {repo_url}...")
    
    try:
        # Clone repository
        print("Cloning repository...")
        subprocess.run([
            "git", "clone", repo_url, str(install_dir)
        ], check=True, capture_output=True)
        
        # Install Python dependencies
        print("Installing Python dependencies...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", 
            str(install_dir / "requirements.txt")
        ], check=True, capture_output=True)
        
        # Install Lighthouse
        print("Installing Lighthouse...")
        try:
            subprocess.run([
                "npm", "install", "-g", "lighthouse"
            ], check=True, capture_output=True)
            print("✓ Lighthouse installed successfully")
        except subprocess.CalledProcessError:
            print("⚠ Warning: Lighthouse installation failed. Performance features may not work.")
            print("  Please install Node.js and run: npm install -g lighthouse")
        
        # Set up environment file
        env_file = install_dir / ".env"
        env_example = install_dir / ".env.example"
        
        if env_example.exists() and not env_file.exists():
            shutil.copy2(env_example, env_file)
            
            # Add API keys if provided
            if api_keys:
                with open(env_file, 'r') as f:
                    content = f.read()
                
                for key, value in api_keys.items():
                    if value:
                        content = content.replace(f"{key}=your_{key.lower()}_here", f"{key}={value}")
                
                with open(env_file, 'w') as f:
                    f.write(content)
        
        # Initialize database
        print("Initializing database...")
        subprocess.run([
            sys.executable, "-c", 
            f"import sys; sys.path.insert(0, '{install_dir}'); from database.models import init_database; import asyncio; asyncio.run(init_database())"
        ], check=True, capture_output=True, cwd=install_dir)
        
        # Run tests
        print("Running tests...")
        subprocess.run([
            sys.executable, str(install_dir / "test.py")
        ], check=True, capture_output=True, cwd=install_dir)
        
        print("✓ SEO Auditor MCP Server installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Installation failed: {e}")
        if e.stderr:
            print(f"Error: {e.stderr.decode()}")
        return False
    except Exception as e:
        print(f"✗ Installation failed: {e}")
        return False

def add_to_claude_config(install_dir: Path, server_name: str = "seo-auditor", 
                        api_keys: Dict[str, str] = None) -> bool:
    """Add SEO Auditor to Claude Code configuration."""
    try:
        config = load_claude_config()
        
        # Ensure mcpServers exists
        if "mcpServers" not in config:
            config["mcpServers"] = {}
        
        # Add server configuration
        server_config = {
            "command": sys.executable,
            "args": [str(install_dir / "server.py")],
            "cwd": str(install_dir)
        }
        
        # Add environment variables if API keys provided
        if api_keys and any(api_keys.values()):
            server_config["env"] = {k: v for k, v in api_keys.items() if v}
        
        config["mcpServers"][server_name] = server_config
        
        save_claude_config(config)
        print(f"✓ Added '{server_name}' to Claude Code configuration")
        return True
        
    except Exception as e:
        print(f"✗ Failed to update Claude Code configuration: {e}")
        return False

def remove_from_claude_config(server_name: str = "seo-auditor") -> bool:
    """Remove SEO Auditor from Claude Code configuration."""
    try:
        config = load_claude_config()
        
        if "mcpServers" in config and server_name in config["mcpServers"]:
            del config["mcpServers"][server_name]
            save_claude_config(config)
            print(f"✓ Removed '{server_name}' from Claude Code configuration")
            return True
        else:
            print(f"Server '{server_name}' not found in configuration")
            return False
            
    except Exception as e:
        print(f"✗ Failed to update Claude Code configuration: {e}")
        return False

def check_prerequisites() -> bool:
    """Check if prerequisites are installed."""
    print("Checking prerequisites...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("✗ Python 3.8 or higher is required")
        return False
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Check git
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        print("✓ Git is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ Git is required but not found")
        return False
    
    # Check pip
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True, check=True)
        print("✓ pip is available")
    except subprocess.CalledProcessError:
        print("✗ pip is required but not working")
        return False
    
    # Check Node.js (optional)
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, check=True)
        print(f"✓ Node.js detected: {result.stdout.decode().strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠ Node.js not found - Lighthouse features will be limited")
        print("  Install Node.js from: https://nodejs.org/")
    
    return True

def get_install_directory(custom_dir: Optional[str] = None) -> Path:
    """Get installation directory."""
    if custom_dir:
        return Path(custom_dir).expanduser().resolve()
    
    # Default installation locations
    system = platform.system()
    if system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "Claude" / "mcp-servers" / "seo-auditor"
    elif system == "Windows":
        return Path(os.getenv("APPDATA", "")) / "Claude" / "mcp-servers" / "seo-auditor"
    else:  # Linux
        return Path.home() / ".local" / "share" / "claude" / "mcp-servers" / "seo-auditor"

def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="SEO Auditor MCP Server - Claude Code CLI Installer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Install from GitHub
  python install.py install

  # Install with API keys
  python install.py install --google-api-key YOUR_KEY

  # Install to custom directory
  python install.py install --dir ~/my-mcp-servers/seo-auditor

  # Uninstall
  python install.py uninstall

  # Check status
  python install.py status
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Install command
    install_parser = subparsers.add_parser('install', help='Install SEO Auditor MCP Server')
    install_parser.add_argument('--repo', default='https://github.com/tuckercoffey/seo-auditor-mcp.git',
                               help='Git repository URL')
    install_parser.add_argument('--dir', help='Custom installation directory')
    install_parser.add_argument('--name', default='seo-auditor', help='Server name in Claude config')
    install_parser.add_argument('--google-api-key', help='Google API key for PageSpeed Insights')
    install_parser.add_argument('--ahrefs-api-key', help='Ahrefs API key for backlink analysis')
    install_parser.add_argument('--semrush-api-key', help='SEMrush API key for competitive analysis')
    install_parser.add_argument('--force', action='store_true', help='Force reinstall if already exists')
    
    # Uninstall command
    uninstall_parser = subparsers.add_parser('uninstall', help='Uninstall SEO Auditor MCP Server')
    uninstall_parser.add_argument('--name', default='seo-auditor', help='Server name in Claude config')
    uninstall_parser.add_argument('--keep-files', action='store_true', help='Keep installation files')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Check installation status')
    status_parser.add_argument('--name', default='seo-auditor', help='Server name to check')
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Update SEO Auditor MCP Server')
    update_parser.add_argument('--name', default='seo-auditor', help='Server name in Claude config')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    print("SEO Auditor MCP Server - Claude Code CLI Installer")
    print("=" * 55)
    
    if args.command == 'install':
        # Check prerequisites
        if not check_prerequisites():
            sys.exit(1)
        
        # Get installation directory
        install_dir = get_install_directory(args.dir)
        
        # Check if already installed
        if install_dir.exists() and not args.force:
            print(f"✗ SEO Auditor is already installed at {install_dir}")
            print("Use --force to reinstall or run 'uninstall' first")
            sys.exit(1)
        
        # Remove existing installation if force
        if install_dir.exists() and args.force:
            print(f"Removing existing installation at {install_dir}")
            shutil.rmtree(install_dir)
        
        # Collect API keys
        api_keys = {
            'GOOGLE_API_KEY': args.google_api_key,
            'AHREFS_API_KEY': args.ahrefs_api_key,
            'SEMRUSH_API_KEY': args.semrush_api_key
        }
        
        # Install
        if install_from_git(args.repo, install_dir, api_keys):
            if add_to_claude_config(install_dir, args.name, api_keys):
                print("\n🎉 Installation completed successfully!")
                print("\nNext steps:")
                print("1. Restart Claude Code")
                print("2. Try: 'Analyze the SEO of https://example.com'")
                print(f"3. Configuration: {get_claude_config_file()}")
                print(f"4. Installation: {install_dir}")
            else:
                print("\n⚠ Installation completed but Claude configuration failed")
                print("You may need to manually add the server to Claude Code")
        else:
            sys.exit(1)
    
    elif args.command == 'uninstall':
        success = True
        
        # Remove from Claude config
        if not remove_from_claude_config(args.name):
            success = False
        
        # Remove installation files
        if not args.keep_files:
            install_dir = get_install_directory()
            if install_dir.exists():
                try:
                    shutil.rmtree(install_dir)
                    print(f"✓ Removed installation directory: {install_dir}")
                except Exception as e:
                    print(f"✗ Failed to remove installation directory: {e}")
                    success = False
            else:
                print("Installation directory not found")
        
        if success:
            print("✓ SEO Auditor MCP Server uninstalled successfully")
            print("Restart Claude Code to apply changes")
        else:
            print("⚠ Uninstallation completed with some errors")
    
    elif args.command == 'status':
        # Check Claude config
        config = load_claude_config()
        server_name = args.name
        
        if "mcpServers" in config and server_name in config["mcpServers"]:
            server_config = config["mcpServers"][server_name]
            print(f"✓ '{server_name}' found in Claude Code configuration")
            print(f"  Command: {server_config.get('command', 'N/A')}")
            print(f"  Args: {server_config.get('args', [])}")
            print(f"  Working Directory: {server_config.get('cwd', 'N/A')}")
            
            # Check if installation directory exists
            if 'cwd' in server_config:
                install_dir = Path(server_config['cwd'])
                if install_dir.exists():
                    print(f"✓ Installation directory exists: {install_dir}")
                    
                    # Check if server file exists
                    if len(server_config.get('args', [])) > 0:
                        server_file = install_dir / Path(server_config['args'][0]).name
                        if server_file.exists():
                            print(f"✓ Server file exists: {server_file}")
                        else:
                            print(f"✗ Server file missing: {server_file}")
                else:
                    print(f"✗ Installation directory missing: {install_dir}")
        else:
            print(f"✗ '{server_name}' not found in Claude Code configuration")
            print(f"Configuration file: {get_claude_config_file()}")
    
    elif args.command == 'update':
        print("Update functionality coming soon!")
        print("For now, run: python install.py uninstall && python install.py install")

if __name__ == "__main__":
    main()