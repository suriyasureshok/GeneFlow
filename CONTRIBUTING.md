# 🤝 GeneFlow Contributing Guide

Thank you for your interest in contributing to GeneFlow! This guide will help you get started.

---

## Code of Conduct

We are committed to providing a welcoming and inspiring community. Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## Getting Started

### Fork & Clone

```bash
# 1. Fork on GitHub
# Click "Fork" on https://github.com/suriyasureshok/geneflow

# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/geneflow.git
cd GeneFlow

# 3. Add upstream remote
git remote add upstream https://github.com/suriyasureshok/geneflow.git
```

### Setup Development Environment

```bash
# Create virtual environment
python -m venv gene
source gene/bin/activate  # Mac/Linux
gene\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### Verify Setup

```bash
# Run tests
pytest src/tests/ -v

# Check code quality
flake8 src/
black --check src/
mypy src/

# Try the app
python main.py
```

---

## Development Workflow

### 1. Create Feature Branch

```bash
# Update main branch
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/your-feature-name
```

**Branch Naming Convention**:
- `feature/new-analysis-tool` - New features
- `fix/session-bug` - Bug fixes
- `docs/api-guide` - Documentation
- `refactor/module-name` - Refactoring
- `test/edge-cases` - Tests

### 2. Make Changes

```bash
# Edit files
nano src/agents/chat_agent.py

# Follow code style
black src/
flake8 src/

# Run tests
pytest src/tests/ -v
```

### 3. Commit Changes

```bash
# Stage changes
git add src/agents/chat_agent.py

# Commit with descriptive message
git commit -m "Add support for RNA sequences in chat agent

- Add RNA codon table
- Update sequence validation
- Add tests for RNA handling
- Closes #123"
```

**Commit Message Guidelines**:
- Use imperative mood ("Add feature" not "Added feature")
- First line ≤ 50 characters
- Wrap body at 72 characters
- Reference issues with "Closes #123"
- Separate subject from body with blank line

### 4. Keep Branch Updated

```bash
# Fetch latest upstream changes
git fetch upstream

# Rebase on main
git rebase upstream/main

# Force push (use with caution!)
git push origin feature/your-feature-name --force-with-lease
```

### 5. Push Changes

```bash
# Push to your fork
git push origin feature/your-feature-name
```

### 6. Create Pull Request

1. Go to https://github.com/YOUR_USERNAME/geneflow
2. Click "Compare & pull request"
3. Fill in PR template:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation

## Testing
- [ ] Unit tests added
- [ ] Integration tests passed
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No breaking changes
- [ ] Performance impact analyzed
```

---

## Coding Standards

### Python Style

```python
# Follow PEP 8
# Use type hints
def analyze_sequence(sequence: str) -> Dict[str, Any]:
    """
    Comprehensive docstring following NumPy style.
    
    Parameters
    ----------
    sequence : str
        DNA sequence string
    
    Returns
    -------
    Dict[str, Any]
        Analysis results
    
    Examples
    --------
    >>> result = analyze_sequence("ATGAAATAAG")
    >>> print(result['gc_percent'])
    """
    pass

# Imports
from typing import Dict, Any, List  # Standard library
import os
import sys

import numpy as np  # Third-party

from src.agents.sequence_analyzer import SequenceAnalyzerAgent  # Local
```

### Formatting

```bash
# Auto-format code
black src/

# Check formatting
flake8 src/

# Type checking
mypy src/

# All at once
pre-commit run --all-files
```

### Documentation

```python
"""
Module docstring at top of file.

Describes purpose, main classes, and usage examples.
"""

class ExampleClass:
    """
    Class docstring with description.
    
    Attributes
    ----------
    name : str
        The name attribute
    
    Methods
    -------
    example_method()
        Does something
    """
    
    def example_method(self, param: str) -> bool:
        """
        Method description.
        
        Parameters
        ----------
        param : str
            Description
        
        Returns
        -------
        bool
            Description
        
        Raises
        ------
        ValueError
            If param is invalid
        
        Examples
        --------
        >>> obj.example_method("test")
        True
        """
        pass
```

---

## Testing Requirements

### Unit Tests

```python
# tests/test_sequence_analyzer.py
import pytest
from src.agents.sequence_analyzer import SequenceAnalyzerAgent

class TestSequenceAnalyzer:
    """Test sequence analysis functionality"""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance"""
        return SequenceAnalyzerAgent()
    
    def test_gc_content_calculation(self, analyzer):
        """Test GC content calculation"""
        result = analyzer.analyze("ATGC")
        assert result['gc_percent'] == 50.0
    
    def test_orf_detection(self, analyzer):
        """Test ORF detection"""
        result = analyzer.analyze("ATGAAATAA")
        assert len(result['orfs']) == 1
        assert result['orfs'][0]['start'] == 0
    
    def test_invalid_sequence(self, analyzer):
        """Test invalid sequence handling"""
        result = analyzer.analyze("INVALID")
        assert result['valid'] == False
```

### Running Tests

```bash
# Run all tests
pytest src/tests/ -v

# Run specific test file
pytest src/tests/test_sequence_analyzer.py -v

# Run specific test
pytest src/tests/test_sequence_analyzer.py::TestSequenceAnalyzer::test_gc_content_calculation -v

# With coverage
pytest src/tests/ --cov=src --cov-report=html

# Watch mode
pytest-watch src/tests/
```

### Coverage Requirements

- Minimum 80% overall coverage
- 100% for critical paths (analysis, coordination)
- Document any intentional gaps

---

## Documentation

### Adding Docs

```markdown
# Feature Description

Brief description of the feature.

## Usage

```python
# Example code
```

## API Reference

### Function Name
Description and signature

## See Also

- Related functions
- External links
```

### Building Docs

```bash
# Generate documentation
sphinx-build -b html docs docs/_build

# View locally
open docs/_build/index.html
```

---

## Issue Tracking

### Creating Issues

When creating an issue, include:

1. **Title**: Clear, descriptive
2. **Description**: What, why, impact
3. **Reproduction**: Steps to reproduce (bugs)
4. **Expected/Actual**: For bugs
5. **Environment**: Python version, OS, etc.

### Issue Labels

- `bug` - Something isn't working
- `enhancement` - Feature request
- `documentation` - Docs improvement needed
- `good first issue` - Good for newcomers
- `help wanted` - Need community help
- `question` - Questions/discussion
- `wontfix` - Intentionally not fixing

---

## Performance Considerations

### Optimization Checklist

- [ ] No unnecessary nested loops
- [ ] Cache computed values
- [ ] Use appropriate data structures
- [ ] Profile before optimizing
- [ ] Document performance impact

### Benchmarking

```python
import timeit

# Simple benchmark
time_taken = timeit.timeit(
    'analyze_sequence("ATGAAA...")',
    setup='from src.core.adk_tools import analyze_sequence',
    number=100
)
print(f"Average time: {time_taken/100:.3f}s")
```

---

## Security

### Security Guidelines

- Never commit secrets (API keys, passwords)
- Use environment variables for sensitive data
- Validate all user inputs
- Sanitize error messages
- Keep dependencies updated

### Reporting Security Issues

**Do not** create public issues for security vulnerabilities.

Email: security@example.com

---

## Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):
- `MAJOR.MINOR.PATCH` (e.g., 1.2.3)
- Breaking changes = MAJOR
- New features = MINOR
- Bug fixes = PATCH

### Release Checklist

- [ ] Update version in `__init__.py`
- [ ] Update `CHANGELOG.md`
- [ ] Run full test suite
- [ ] Update documentation
- [ ] Create git tag
- [ ] Push to main
- [ ] Create GitHub release

---

## Common Contributing Scenarios

### Adding a New Analysis Tool

```python
# 1. Create agent in src/agents/
# src/agents/new_analysis.py

class NewAnalysisAgent:
    def analyze(self, data):
        """Perform analysis"""
        pass

# 2. Add tool in src/core/adk_tools.py

def new_analysis_tool(data: str) -> str:
    """Expose tool for ADK"""
    agent = NewAnalysisAgent()
    result = agent.analyze(data)
    return json.dumps(result)

# 3. Add to tool list in get_all_tools()

# 4. Add tests
# src/tests/test_new_analysis.py

# 5. Update documentation
# Modules.md, API_GUIDE.md

# 6. Create PR with all changes
```

### Fixing a Bug

```python
# 1. Create test that reproduces bug
def test_bug_scenario():
    result = problematic_function()
    assert result == expected_value  # Currently fails

# 2. Run test to confirm failure
pytest test_file.py -v

# 3. Fix the bug
# Update src/file.py

# 4. Run test again to confirm fix
pytest test_file.py -v

# 5. Create PR with bug fix + test
```

### Improving Documentation

```bash
# 1. Edit markdown file
nano Modules.md

# 2. Build docs locally
sphinx-build -b html docs docs/_build

# 3. Review changes
open docs/_build/index.html

# 4. Create PR with improvements
```

---

## Getting Help

### Resources

- 📚 [Documentation](../README.md)
- 🔗 [API Guide](API_GUIDE.md)
- 🏗️ [Architecture](Architecture.md)
- 💬 [GitHub Discussions](https://github.com/suriyasureshok/geneflow/discussions)

### Questions?

- 💬 Ask in [GitHub Discussions](https://github.com/suriyasureshok/geneflow/discussions/new)
- 📧 Email: dev@example.com
- 🐦 Twitter: [@GeneFlow](https://twitter.com/geneflow)

---

## Thank You! 🙏

Your contributions make GeneFlow better for everyone. We appreciate:

- 🐛 Bug reports and fixes
- ✨ New features and enhancements
- 📚 Documentation improvements
- 🧪 Test coverage increases
- 💡 Ideas and suggestions

---

## Additional Resources

- [GitHub Flow Guide](https://guides.github.com/introduction/flow/)
- [How to Write Good Commit Messages](https://chris.beams.io/posts/git-commit/)
- [NumPy Docstring Guide](https://numpydoc.readthedocs.io/en/latest/format.html)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)

---

**Last Updated**: November 2024
**Version**: 1.0.0
