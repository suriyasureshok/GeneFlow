# ⚡ GeneFlow Quick Reference

Quick lookup guide for common tasks and API calls.

---

## Installation & Setup

```bash
# Clone
git clone https://github.com/suriyasureshok/geneflow.git
cd GeneFlow

# Setup
python -m venv gene
gene\Scripts\activate  # Windows
source gene/bin/activate  # Mac/Linux
pip install -r requirements.txt

# Configure
echo GOOGLE_API_KEY=your_key > .env

# Run
python main.py
```

---

## Basic Usage

### Quick Chat

```python
from src.agents.unified_coordinator import UnifiedCoordinator

coordinator = UnifiedCoordinator()
result = coordinator.process_message("What is GC content?")
print(result['response'])
```

### Sequence Analysis

```python
result = coordinator.run_pipeline("ATGAAATAAGCGTAGCTAG")
print(f"GC%: {result['results']['analysis']['gc_percent']}")
print(f"ORFs: {len(result['results']['analysis']['orfs'])}")
```

### Direct Tool Access

```python
from src.core.adk_tools import analyze_sequence
import json

result_json = analyze_sequence("ATGAAATAAGCG")
result = json.loads(result_json)
```

---

## API Quick Reference

### UnifiedCoordinator

| Method | Purpose | Speed | Use Case |
|--------|---------|-------|----------|
| `process_message()` | Route message | 1-60s | General purpose |
| `run_pipeline()` | Full analysis | 30-60s | Deep dive |
| `get_session_summary()` | Session info | <1s | Session lookup |
| `get_performance_stats()` | Metrics | <1s | Monitoring |

```python
# Chat (1-3s)
result = coordinator.process_message("Question?")

# Analysis (30-60s)
result = coordinator.run_pipeline("ATGAAA...")

# Session info (<1s)
summary = coordinator.get_session_summary("session_id")

# Stats (<1s)
stats = coordinator.get_performance_stats()
```

### Session Management

```python
from src.core.session_manager import SessionManager

manager = SessionManager()

# Create
session = manager.create_session(user_id="user_123")

# Get
session = manager.get_session("session_id")

# Get or create
session = manager.get_or_create_session("session_id", "user_123")

# Work with session
session.add_message("user", "text")
session.update_context("key", "value")
session.get_context("key")

# Cleanup
manager.cleanup_old_sessions()
```

### Direct Tools

```python
from src.core.adk_tools import *
import json

# Analyze sequence
analyze_sequence("ATGAAA...")

# Predict protein
predict_protein_properties("ATGAAA...")

# Compare sequences
compare_sequences("ATGAAA...", "ATGAAA...")

# Search literature
search_literature("GC-rich regions")

# Generate hypotheses
generate_hypotheses({"analysis": {...}})

# Create visualizations
create_visualizations({"data": "..."})

# Generate report
generate_report({"data": "..."})
```

---

## Common Patterns

### Chat Loop

```python
coordinator = UnifiedCoordinator()
session_id = "user_session"

while True:
    query = input("You: ").strip()
    if query.lower() == 'quit':
        break
    
    result = coordinator.process_message(query, session_id=session_id)
    print(f"Bot: {result['response']}\n")
```

### Batch Processing

```python
coordinator = UnifiedCoordinator()

sequences = ["ATGAAA...", "ATGCCC...", "ATGAAG..."]
results = []

for seq in sequences:
    result = coordinator.run_pipeline(seq)
    if result['success']:
        results.append({
            "seq": seq,
            "gc": result['results']['analysis']['gc_percent'],
            "report": result['results']['report']['report_path']
        })
```

### Error Handling

```python
result = coordinator.process_message(message)

if result['success']:
    print(result['response'])
else:
    print(f"Error: {result['error']}")
    # Handle error...
```

### Session-based Workflow

```python
coordinator = UnifiedCoordinator()
session_id = "researcher_001"

# First interaction
r1 = coordinator.process_message(
    "I'm studying bacteria GC content",
    session_id=session_id
)

# Follow-up with context
r2 = coordinator.process_message(
    "Analyze this sequence: ATGAAA...",
    session_id=session_id
)

# Agent remembers context
print(r2['response'])
```

---

## Configuration

### Environment Variables

```bash
# Required
GOOGLE_API_KEY=sk-xxxxx

# Optional
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR
SESSION_MAX_AGE_HOURS=24         # Default: 24
MAX_SEQUENCE_LENGTH=100000       # Max input length
CACHE_ENABLED=true               # Enable caching
REDIS_URL=redis://localhost:6379 # Redis connection
```

### Programmatic Configuration

```python
from src.core.session_manager import SessionManager
from src.core.monitoring import PerformanceMonitor

session_manager = SessionManager(
    storage_path="my_sessions",
    max_session_age_hours=48
)

monitor = PerformanceMonitor(
    storage_path="my_metrics"
)

coordinator = UnifiedCoordinator(
    session_manager=session_manager,
    performance_monitor=monitor,
    model="gemini-2.5-flash"
)
```

---

## Response Structures

### Message Response

```python
{
    "success": True,
    "session_id": "uuid",
    "response": "Text response",
    "timestamp": "2024-01-15T10:30:00Z"
}
```

### Pipeline Response

```python
{
    "success": True,
    "session_id": "uuid",
    "response": "Summary",
    "results": {
        "sequence_length": 50,
        "analysis": {
            "gc_percent": 42.0,
            "orfs": [...],
            "motifs": [...]
        },
        "literature": "Summary",
        "hypotheses": [
            {
                "hypothesis": "...",
                "confidence": 0.85,
                "rationale": "..."
            }
        ],
        "visualizations": {
            "structure_pdb": "path/to/file.pdb",
            "structure_image": "path/to/image.png"
        },
        "report": {
            "report_path": "path/to/report.pdf"
        }
    },
    "execution_time_seconds": 45.3
}
```

### Analysis Results

```python
{
    "valid": True,
    "sequence_type": "DNA",
    "length": 1000,
    "gc_percent": 42.5,
    "orfs": [
        {
            "start": 0,
            "end": 90,
            "sequence": "ATG...TAG",
            "length": 90,
            "frame": 1
        }
    ],
    "motifs": [
        {
            "name": "TATA_box",
            "position": 100,
            "sequence": "TATAAA"
        }
    ]
}
```

---

## Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set environment
import os
os.environ['LOG_LEVEL'] = 'DEBUG'
```

### Check Health

```python
from main import check_dependencies, check_environment

if check_dependencies():
    print("✓ Dependencies OK")
else:
    print("✗ Missing dependencies")

if check_environment():
    print("✓ Environment OK")
else:
    print("✗ Environment issues")
```

### Monitor Performance

```python
coordinator = UnifiedCoordinator()

# Get metrics
stats = coordinator.get_performance_stats()
print(f"Total cost: ${stats['total_cost']:.2f}")
print(f"Avg latency: {stats['avg_latency_ms']:.0f}ms")
```

---

## Testing

### Run All Tests

```bash
pytest src/tests/ -v
```

### Run Specific Test

```bash
pytest src/tests/test_sequence_analyzer.py -v
```

### Run with Coverage

```bash
pytest src/tests/ --cov=src --cov-report=html
```

### Write Quick Test

```python
def test_gc_content():
    from src.agents.sequence_analyzer import SequenceAnalyzerAgent
    agent = SequenceAnalyzerAgent()
    result = agent.analyze("ATGC")
    assert result['gc_percent'] == 50.0
```

---

## Deployment

### Docker

```bash
# Build
docker build -t geneflow:latest .

# Run
docker run -p 8501:8501 \
  -e GOOGLE_API_KEY=your_key \
  geneflow:latest

# Compose
docker-compose up -d
```

### Environment-specific

```bash
# Local development
python main.py

# Production
gunicorn -w 4 -b 0.0.0.0:8501 src.ui.Home:app
```

---

## Common Commands

```bash
# Create virtual environment
python -m venv venv

# Activate environment
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Install packages
pip install -r requirements.txt

# Run application
python main.py

# Run specific page
streamlit run src/ui/pages/2_💬_Chat.py

# Run tests
pytest src/tests/ -v

# Build Docker image
docker build -t geneflow:latest .

# Clean cache
find . -type d -name __pycache__ -exec rm -r {} +

# Format code
black src/

# Check style
flake8 src/

# Type check
mypy src/
```

---

## Troubleshooting Quick Fixes

| Issue | Fix |
|-------|-----|
| GOOGLE_API_KEY not found | `export GOOGLE_API_KEY=your_key` |
| Module not found | `pip install -r requirements.txt` |
| Port 8501 in use | `streamlit run ... --server.port 8502` |
| Out of memory | Reduce sequence length or enable Redis |
| Slow responses | Check API quota, enable caching |
| Session not found | Create new session with `get_or_create_session()` |

---

## Key Files

| File | Purpose |
|------|---------|
| `main.py` | Application entry point |
| `README.md` | Project overview |
| `Architecture.md` | System design |
| `Modules.md` | Module reference |
| `API_GUIDE.md` | API documentation |
| `DEPLOYMENT_GUIDE.md` | Deployment instructions |
| `src/agents/` | AI agents |
| `src/core/` | Core infrastructure |
| `src/utils/` | Utility functions |
| `src/ui/` | Streamlit UI |

---

## Common Sequences for Testing

```python
# Short sequence
short = "ATGAAATAAGCG"

# ORF-containing sequence
with_orf = "ATGAAATAAGCGTAA"

# High GC content
high_gc = "GCGCGCGCGCGCGCGC"

# Low GC content
low_gc = "ATATATAT"

# With motifs
with_motifs = "AATAAATATAAGCG"

# Long sequence (for pipeline)
long_seq = "ATGAAATAAGCGTACGTGCTTGAATGCCTTATAAACGTAGCTAGATGAAATAAGCGTACGTGCTTGAATGCCTTATAAACGTAGCTAG"
```

---

## Performance Reference

| Operation | Time | Cost |
|-----------|------|------|
| Chat | 1-3s | <$0.01 |
| Analyze | 5-10s | ~$0.01 |
| Pipeline | 30-60s | ~$0.05 |
| Report | 5-15s | ~$0.01 |
| Structure | 10-20s | <$0.01 |

---

## Resources

- 📖 [Full README](README.md)
- 🏗️ [Architecture](Architecture.md)
- 📚 [Modules Guide](Modules.md)
- 🔌 [API Guide](API_GUIDE.md)
- 🚀 [Deployment Guide](DEPLOYMENT_GUIDE.md)
- 🤝 [Contributing](CONTRIBUTING.md)

---

**Last Updated**: November 2024
**Version**: 1.0.0
