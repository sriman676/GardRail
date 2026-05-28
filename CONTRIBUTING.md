# Contributing to GardRail

Thank you for your interest in contributing to GardRail! This document provides guidelines for participating in the project.

## Development Setup

### Prerequisites
- Python 3.11+
- Git
- pip or Poetry

### Local Development Environment

```bash
# Clone the repository
git clone https://github.com/sriman676/GardRail.git
cd GardRail

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov black flake8 mypy

# Run tests
pytest -v

# Run linting
flake8 --max-line-length=88
black --check .
mypy core/ api/ agent/ db/ --ignore-missing-imports
```

## Code Style Guide

### Python Style
- Follow **PEP 8** with line length max 88 characters (Black formatter)
- Use **type hints** for all function parameters and return values
- Use **Google-style docstrings** for all public APIs

### Documentation Requirements
```python
def process_injection(content: str, tenant_id: str = "default") -> ScanResult:
    """
    Scan content for injection patterns.
    
    Analyzes the input for known injection attacks and behavioral anomalies.
    Applies active rules first, then optional LLM classification.
    
    Args:
        content: The user-provided input to scan
        tenant_id: Multi-tenancy identifier (default: 'default')
        
    Returns:
        ScanResult: Threat level, matched patterns, and explanations
        
    Raises:
        ValueError: If content is None or not a string
        TimeoutError: If LLM call exceeds timeout
    """
```

### Naming Conventions
- Classes: `PascalCase` (e.g., `InjectionScanner`)
- Functions/methods: `snake_case` (e.g., `scan_content`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_TIMEOUT`)
- Private methods: prefix with `_` (e.g., `_internal_helper`)

## Testing Requirements

### Coverage Standards
- **Minimum**: 95% code coverage
- **Target**: 100% coverage for security-critical paths
- Run: `pytest --cov=core --cov=api --cov=db --cov-report=html`

### Test Structure
```python
def test_feature_description():
    """Test that specific behavior works correctly."""
    # Arrange: Set up test data and mocks
    scanner = InjectionScanner()
    
    # Act: Execute the behavior under test
    result = scanner.scan("SELECT * FROM users--")
    
    # Assert: Verify expected outcomes
    assert result.threat_level == ThreatLevel.DANGER
```

## Pull Request Process

### Before Submitting

1. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Write tests** for new functionality and verify coverage

3. **Format and lint code**:
   ```bash
   black .
   flake8
   mypy core/ api/ agent/ db/ --ignore-missing-imports
   ```

4. **Update documentation** and docstrings

5. **Run full test suite**:
   ```bash
   pytest -v
   ```

### PR Requirements

Your PR must:
- ✅ Pass all automated tests
- ✅ Maintain or improve code coverage (>95%)
- ✅ Include descriptive commit messages
- ✅ Have clear description of changes
- ✅ Be rebased on latest `main` branch

## Commit Message Guidelines

```
[TYPE] Short description under 50 characters

More detailed explanation of the change, wrapped at 72 characters.
Explain what the change does and why it was needed.

Fixes #123
```

### Commit Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions/updates
- `security`: Security fixes/enhancements

## Reporting Security Issues

⚠️ **Do not** create public issues for security vulnerabilities.
Email maintainers with:
- Description of vulnerability
- Steps to reproduce
- Potential impact

## File Structure
```
GardRail/
├── core/              # Core security logic
├── api/               # FastAPI routes and middleware
├── db/                # Database/persistence layer
├── agent/             # Agent wrapper and orchestration
├── tests/             # Test suite
├── config.py          # Configuration
└── requirements.txt   # Dependencies
```

## Getting Help

- Check README.md and IMPROVEMENTS.md
- Search existing GitHub issues
- Join community discussions

---

**Thank you for making GardRail more secure!** 🛡️
