# Contributing to SEO Auditor MCP Server

Thank you for your interest in contributing to the SEO Auditor MCP Server! This document provides guidelines and information for contributors.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Adding New Features](#adding-new-features)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/seo-auditor-mcp.git
   cd seo-auditor-mcp
   ```
3. **Set up the development environment**:
   ```bash
   python setup.py
   ```
4. **Create a branch** for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Prerequisites
- Python 3.8+
- Node.js and npm (for Lighthouse)
- Git

### Installation
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-asyncio black flake8 mypy

# Install Lighthouse
npm install -g lighthouse
```

### Environment Setup
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Code Style

We follow Python PEP 8 guidelines with some modifications:

### Formatting
- Use **Black** for code formatting: `black .`
- Line length: 100 characters
- Use type hints for function parameters and return values
- Use descriptive variable and function names

### Documentation
- Add docstrings to all public functions and classes
- Use Google-style docstrings
- Include parameter types and descriptions
- Include usage examples for complex functions

### Example:
```python
async def analyze_technical_seo(self, url: str, include_security: bool = True) -> Dict[str, Any]:
    """
    Comprehensive technical SEO analysis.
    
    Args:
        url: URL to analyze
        include_security: Whether to include security analysis
        
    Returns:
        Dict containing technical SEO analysis results
        
    Example:
        analyzer = TechnicalSEOAnalyzer()
        result = await analyzer.analyze_technical_seo("https://example.com")
    """
```

## Adding New Features

### 1. SEO Analysis Tools

To add a new SEO analysis tool:

1. **Create analyzer method** in the appropriate module (`analyzers/`)
2. **Add tool definition** to `server.py` in `handle_list_tools()`
3. **Add tool handler** in `handle_call_tool()`
4. **Write tests** for the new functionality
5. **Update documentation**

### 2. File Structure

```
analyzers/
├── __init__.py
├── site_crawler.py      # Site discovery and crawling
├── technical_seo.py     # Technical SEO analysis
├── performance.py       # Performance and Core Web Vitals
├── onpage_seo.py       # On-page SEO analysis
└── your_new_analyzer.py # New analyzer module
```

### 3. Example New Analyzer

```python
class YourNewAnalyzer:
    """Analyzer for your specific SEO aspect."""
    
    def __init__(self):
        self.session = None
        
    async def analyze_your_feature(self, url: str) -> Dict[str, Any]:
        """
        Analyze your specific SEO feature.
        
        Args:
            url: URL to analyze
            
        Returns:
            Dict containing analysis results
        """
        # Your analysis logic here
        results = {
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "analysis_data": {},
            "score": 0,
            "issues": [],
            "recommendations": []
        }
        
        # Save to database
        audit_result = AuditResult(
            url=url,
            audit_type="your_feature",
            timestamp=datetime.now(),
            results=results,
            score=results["score"],
            issues=results["issues"],
            recommendations=results["recommendations"]
        )
        await save_audit_result(audit_result)
        
        return results
```

### 4. Database Models

If you need to store new data types, add models to `database/models.py`:

```python
@dataclass
class YourNewResult:
    """Your new result type."""
    url: str
    your_data: Dict[str, Any]
    timestamp: datetime
```

## Testing

### Running Tests

```bash
# Run all tests
python test.py

# Run with live testing
python test.py --live

# Run specific test
python -m pytest tests/test_your_analyzer.py
```

### Writing Tests

Create test files in the `tests/` directory:

```python
import pytest
from analyzers.your_new_analyzer import YourNewAnalyzer

@pytest.mark.asyncio
async def test_analyze_your_feature():
    analyzer = YourNewAnalyzer()
    result = await analyzer.analyze_your_feature("https://example.com")
    
    assert "url" in result
    assert "score" in result
    assert isinstance(result["score"], (int, float))
```

### Test Guidelines
- Write tests for all new functionality
- Include both positive and negative test cases
- Test error handling and edge cases
- Use mock objects for external API calls
- Ensure tests can run without internet connection

## Submitting Changes

### Pull Request Process

1. **Ensure tests pass**:
   ```bash
   python test.py
   python -m pytest
   ```

2. **Check code style**:
   ```bash
   black --check .
   flake8 .
   mypy .
   ```

3. **Update documentation** if needed

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add: Brief description of your changes"
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request** on GitHub

### Commit Message Guidelines

Use conventional commit format:
- `feat: add new SEO analyzer`
- `fix: resolve performance analysis bug`
- `docs: update README with new features`
- `test: add tests for technical SEO analyzer`
- `refactor: improve code organization`

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass
- [ ] New tests added
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes
```

## Reporting Issues

### Bug Reports

Use the GitHub issue template and include:

1. **Environment information**:
   - Python version
   - Operating system
   - Package versions

2. **Steps to reproduce**
3. **Expected behavior**
4. **Actual behavior**
5. **Error messages** (if any)
6. **Minimal code example**

### Feature Requests

Include:
1. **Use case description**
2. **Proposed solution**
3. **Alternative solutions considered**
4. **Implementation complexity estimate**

### Security Issues

For security vulnerabilities, please email directly instead of creating public issues.

## Development Guidelines

### Performance Considerations
- Implement rate limiting for external requests
- Use async/await for I/O operations
- Cache results when appropriate
- Handle large websites gracefully

### Error Handling
- Use specific exception types
- Provide helpful error messages
- Log errors appropriately
- Graceful degradation when services are unavailable

### API Integration
- Respect API rate limits
- Handle API errors gracefully
- Make API keys optional when possible
- Provide fallback methods

## Getting Help

- **GitHub Discussions**: For questions and general discussion
- **GitHub Issues**: For bug reports and feature requests
- **Code Review**: Submit PRs for feedback

## Recognition

Contributors will be acknowledged in:
- README.md contributors section
- Release notes
- Project documentation

Thank you for contributing to SEO Auditor MCP Server!