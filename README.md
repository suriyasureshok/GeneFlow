# 🧬 GeneFlow: ADK-Powered Bioinformatics Copilot

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.0+-red.svg)](https://streamlit.io/)
[![Google ADK](https://img.shields.io/badge/Google%20ADK-Latest-green.svg)](https://ai.google.dev/adk)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Overview

**GeneFlow** is an advanced bioinformatics analysis platform powered by **Google ADK (Agentic Development Kit)** that combines multi-agent architecture with generative AI capabilities. It provides researchers and bioinformaticians with intelligent, conversational tools for DNA sequence analysis, protein prediction, literature search, and hypothesis generation.

### Key Capabilities

- 🧬 **Intelligent Sequence Analysis**: GC content, ORF detection, motif scanning
- 🔬 **Protein Prediction**: Physicochemical properties from DNA sequences
- 📚 **Literature Integration**: AI-powered research paper discovery and synthesis
- 💡 **Hypothesis Generation**: AI-driven research direction suggestions
- 📊 **Advanced Visualizations**: Interactive plots and 3D structure modeling
- 🤖 **Multi-Agent Architecture**: Specialized agents for different bioinformatics tasks
- 💾 **Session Management**: Persistent conversation history and context
- 📈 **Performance Monitoring**: Real-time metrics and cost tracking

## Quick Start

### Prerequisites

- Python 3.10 or higher
- Google API Key (for generative AI capabilities)
- 4GB RAM minimum

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/suriyasureshok/geneflow.git
   cd GeneFlow
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv gene
   gene\Scripts\activate  # On Windows
   source gene/bin/activate  # On macOS/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Create .env file in root directory
   echo GOOGLE_API_KEY=your_api_key_here > .env
   ```

5. **Launch the application**
   ```bash
   python main.py
   ```

   The application will automatically:
   - Check all dependencies
   - Create necessary directories (`sessions/`, `metrics/`, `geneflow_plots/`)
   - Launch the Streamlit UI at `http://localhost:8501`

## Application Architecture

### System Overview

```
┌─────────────────────────────────────────────┐
│           Streamlit Web UI                   │
│  (Home, Dashboard, Chat, Analysis Pages)     │
└────────────────────┬────────────────────────┘
                     │
┌────────────────────▼────────────────────────┐
│      UnifiedCoordinator (Router)             │
│  - Routes to Chat or Analysis based on input │
└────────────────────┬────────────────────────┘
          ┌──────────┴──────────┐
          │                     │
    ┌─────▼─────┐        ┌─────▼──────────┐
    │ ChatAgent │        │ ADKCoordinator │
    │ (Fast)    │        │ (Comprehensive)│
    └───────────┘        └─────┬──────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
            ┌───────▼──────┐      ┌──────▼────────┐
            │ Sequence     │      │ Protein       │
            │ Analyzer     │      │ Prediction    │
            └──────────────┘      └───────────────┘
```

### Module Structure

```
GeneFlow/
├── main.py                      # Application entry point
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── Architecture.md              # System design documentation
├── Modules.md                   # Module reference guide
│
├── src/
│   ├── agents/                  # AI agent implementations
│   │   ├── adk_coordinator.py   # Main ADK-based orchestrator
│   │   ├── unified_coordinator.py # Request router
│   │   ├── chat_agent.py        # Lightweight chat
│   │   ├── sequence_analyzer.py # Sequence analysis agent
│   │   ├── protein_prediction.py # Protein analysis
│   │   ├── comparison.py        # Sequence comparison
│   │   ├── hypothesis.py        # Hypothesis generation
│   │   ├── literature.py        # Literature search
│   │   └── coordinator.py       # Legacy coordinator
│   │
│   ├── core/                    # Core infrastructure
│   │   ├── session_manager.py   # User session management
│   │   ├── monitoring.py        # Performance metrics
│   │   ├── adk_tools.py         # ADK tool definitions
│   │   ├── agent_factory.py     # Agent creation
│   │   ├── context_manager.py   # Execution context
│   │   └── memory.py            # Memory management
│   │
│   ├── utils/                   # Utility modules
│   │   ├── visualizer.py        # Plot generation
│   │   ├── reporter.py          # PDF report creation
│   │   └── structure_generator.py # 3D structure modeling
│   │
│   ├── ui/                      # Streamlit user interface
│   │   ├── Home.py              # Landing page
│   │   └── pages/
│   │       ├── 1_Dashboard.py   # Analytics dashboard
│   │       ├── 2_Chat.py        # Chat interface
│   │       └── 3_Analysis.py    # Full analysis
│   │
│   ├── data/                    # Reference data
│   │   └── known_sequences.fasta # Sequence database
│   │
│   └── tests/                   # Unit tests
│       ├── test_adk_pipeline.py
│       ├── test_*.py            # Component tests
│       └── ...
│
├── sessions/                    # User session storage
├── metrics/                     # Performance metrics
└── geneflow_plots/              # Generated visualizations
```

## Workflow Examples

### Example 1: Quick Chat (1-3 seconds)

```python
from src.agents.unified_coordinator import UnifiedCoordinator

coordinator = UnifiedCoordinator()

# Simple question - routes to ChatAgent
result = coordinator.process_message(
    "What is GC content and why is it important?",
    session_id="user_123"
)

print(result['response'])
```

### Example 2: Full DNA Analysis Pipeline (30-60 seconds)

```python
coordinator = UnifiedCoordinator()

# DNA sequence - routes to ADKCoordinator with full tools
sequence = "ATGAAATATAAAGCGTACGTGCTTGAATGCCTTATAAACGTAGCTAG"

result = coordinator.run_pipeline(
    sequence=sequence,
    session_id="user_123"
)

print(f"Analysis complete!")
print(f"GC Content: {result['results']['analysis']['gc_percent']}%")
print(f"ORFs Found: {len(result['results']['analysis']['orfs'])}")
print(f"Report saved to: {result['results']['report']['report_path']}")
```

### Example 3: Session-based Conversation

```python
coordinator = UnifiedCoordinator()
session_id = "researcher_001"

# First message
result1 = coordinator.process_message(
    "I'm studying bacterial resistance genes",
    session_id=session_id
)

# Follow-up with context
result2 = coordinator.process_message(
    "Can you analyze this sequence for me?",
    session_id=session_id
)

# The agent remembers previous conversation context
print(result2['response'])
```

## Performance Characteristics

| Operation | Time | Tokens | Cost Est. |
|-----------|------|--------|-----------|
| Chat Response | 1-3s | 200-500 | <$0.01 |
| Sequence Analysis | 5-10s | 500-1000 | ~$0.01 |
| Full Pipeline | 30-60s | 2000-5000 | ~$0.05 |
| PDF Report Gen | 5-15s | - | ~$0.01 |
| 3D Structure Gen | 10-20s | - | <$0.01 |

## Configuration

### Environment Variables

```env
# Required
GOOGLE_API_KEY=your_api_key_here

# Optional
LOG_LEVEL=INFO                    # Logging level
SESSION_MAX_AGE_HOURS=24         # Session expiration
MAX_SEQUENCE_LENGTH=100000       # Max sequence size
CACHE_ENABLED=true               # Enable caching
REDIS_URL=redis://localhost:6379 # Redis cache (optional)
```

### Performance Tuning

```python
# In your initialization code
from src.core.session_manager import SessionManager
from src.core.monitoring import PerformanceMonitor

# Customize session storage
session_manager = SessionManager(
    storage_path="custom_sessions",
    max_session_age_hours=48  # Longer session lifetime
)

# Customize performance monitoring
monitor = PerformanceMonitor(
    storage_path="custom_metrics",
    enabled=True  # Disable for production if needed
)

# Pass to coordinator
from src.agents.unified_coordinator import UnifiedCoordinator
coordinator = UnifiedCoordinator(
    session_manager=session_manager,
    performance_monitor=monitor
)
```

## Features in Detail

### 1. Sequence Analysis
- **GC Content**: Percentage of guanine and cytosine bases
- **ORF Detection**: Open Reading Frame identification (ATG to stop codon)
- **Motif Scanning**: Regulatory element detection (TATA box, Kozak sequence, etc.)

### 2. Protein Prediction
- **Translation**: DNA to amino acid conversion
- **Molecular Weight**: Protein mass calculation
- **Hydrophobicity**: Protein property analysis
- **Signal Peptide**: N-terminal signal detection

### 3. Sequence Comparison
- **Homology Search**: Find similar sequences
- **Alignment**: Compare multiple sequences
- **Similarity Scoring**: Quantify sequence relationships

### 4. Literature Integration
- **PubMed Search**: Scientific paper discovery
- **Citation Analysis**: Find related research
- **Trend Analysis**: Identify research directions

### 5. Hypothesis Generation
- **Pattern-based**: From sequence analysis results
- **Literature-informed**: Based on research context
- **Confidence Scoring**: Probability estimation

### 6. Visualization Suite
- **GC Content Plots**: Sliding window analysis
- **ORF Maps**: Linear genome representation
- **3D Structure**: DNA/Protein visualization
- **Property Charts**: Physicochemical analysis

## Testing

```bash
# Run all tests
pytest src/tests/

# Run specific test
pytest src/tests/test_sequence_analyzer.py -v

# With coverage
pytest src/tests/ --cov=src --cov-report=html
```

## Troubleshooting

### Issue: "GOOGLE_API_KEY not found"
**Solution**: Set the environment variable:
```bash
set GOOGLE_API_KEY=your_key  # Windows
export GOOGLE_API_KEY=your_key  # Mac/Linux
```

### Issue: Slow responses
**Solutions**:
- Check network connectivity
- Verify API quota limits
- Reduce sequence length for initial analysis
- Enable local caching

### Issue: Session not found
**Solution**: Sessions expire after 24 hours by default. Create a new session or adjust `SESSION_MAX_AGE_HOURS`.

### Issue: Out of memory
**Solution**: Reduce sequence length or enable Redis caching for session storage.

## Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Citation

If you use GeneFlow in your research, please cite:

```bibtex
@software{geneflow2024,
  author = {Suriya Sureshkumar},
  title = {GeneFlow: ADK-Powered Bioinformatics Copilot},
  year = {2024},
  url = {https://github.com/suriyasureshok/geneflow}
}
```

## Resources

- [Google ADK Documentation](https://ai.google.dev/adk)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Biopython Tutorial](https://biopython.org/wiki/Documentation)
- [BioPython API Reference](https://biopython.org/docs/)

## Support

- 📧 Email: suriyasureshkumarkannian@gmail.com
- 📱 Phone: +91 8072816532
- 💼 LinkedIn: [Suriya Sureshkumar](https://linkedin.com/in/suriyasurreshkumar)
- 💬 Issues: [GitHub Issues](https://github.com/suriyasureshok/geneflow/issues)
- 📚 Documentation: [Full Docs](https://github.com/suriyasureshok/geneflow/wiki)

---

**Last Updated**: November 2024
**Version**: 1.0.0