# 🏗️ GeneFlow Architecture Documentation

## System Overview

GeneFlow is a **multi-agent bioinformatics platform** using Google ADK (Agentic Development Kit) that intelligently routes user requests to specialized AI agents based on content type. The architecture follows a **modular, scalable design pattern** with clear separation of concerns.

## Architecture Layers

### Layer 1: User Interface (Streamlit)

**Location**: `src/ui/`

The web interface provides three main pages:

1. **Home.py** - Landing page with features and quick start
2. **Dashboard.py** - Analytics and session management
3. **Chat.py** - Interactive bioinformatics chat
4. **Analysis.py** - Full sequence analysis pipeline

**Technologies**:
- Streamlit for UI rendering
- Session state management
- Interactive visualizations

```python
# Streamlit app initialization
st.set_page_config(
    page_title="GeneFlow",
    page_icon="🧬",
    layout="wide"
)
```

### Layer 2: Request Routing (UnifiedCoordinator)

**Location**: `src/agents/unified_coordinator.py`

Intelligent router that determines which agent to use based on input analysis.

```
Input Message
    ↓
Content Analysis
    ├─ Contains DNA sequence (20+ bp) → ADKCoordinator
    └─ General question → ChatAgent
```

**Key Features**:
- Pattern matching for DNA sequences
- Automatic agent selection
- Unified session management
- Performance tracking

**Routing Logic**:
```python
def _contains_dna_sequence(self, message: str) -> bool:
    """Detects DNA sequences using regex pattern"""
    dna_pattern = r'[ATCGURYKMSWBDHVN]{20,}'
    return bool(re.search(dna_pattern, message.upper()))
```

### Layer 3: Agent Layer

Two specialized agents handle different use cases:

#### 3a. ChatAgent (Lightweight)

**Location**: `src/agents/chat_agent.py`

Fast conversational agent for general bioinformatics questions.

**Characteristics**:
- No tool integration
- 1-3 second response time
- Lower token usage
- Cost-effective

**Use Cases**:
- "What is GC content?"
- "Explain ORFs"
- "How does protein synthesis work?"

**Implementation**:
```python
class ChatAgent:
    def answer_question(self, question: str, 
                       conversation_history: List = []) -> str:
        """Generate conversational response using LLM"""
        # Uses Google's Generative AI directly
        # No tool overhead
```

#### 3b. ADKCoordinator (Full-Featured)

**Location**: `src/agents/adk_coordinator.py`

Advanced analysis orchestrator using Google ADK with integrated tools.

**Characteristics**:
- Tool integration (10+ analysis tools)
- 30-60 second execution time
- Comprehensive bioinformatics analysis
- Structured output generation

**Architecture**:
```
ADKCoordinator
    ├── ADK Services
    │   ├── InMemorySessionService
    │   ├── InMemoryMemoryService
    │   └── InMemoryArtifactService
    │
    ├── LLMAgent (geneflow_coordinator)
    │   └── Tools (20+ functions)
    │
    └── Runner
        └── Executes agent with all services
```

**Workflow**:
```
1. User provides DNA sequence
2. ADKCoordinator creates ADK session
3. LLMAgent processes request with tools
4. Tools execute in sequence:
   - analyze_sequence()
   - predict_protein_properties()
   - search_literature()
   - generate_hypotheses()
   - create_visualizations()
   - generate_report()
5. Results aggregated and returned
```

### Layer 4: Analysis Engines

**Location**: `src/agents/`

Specialized agents for different bioinformatics tasks:

#### 4a. SequenceAnalyzerAgent
```python
class SequenceAnalyzerAgent:
    """Analyzes DNA/RNA sequences"""
    
    def analyze(self, sequence: str) -> Dict:
        - Clean and validate sequence
        - Calculate GC content
        - Find ORFs (Open Reading Frames)
        - Scan regulatory motifs
        
        Returns: Analysis results dict
```

**Methods**:
- `_clean_sequence()`: Normalize input
- `_validate_sequence()`: Check composition
- `_calculate_gc()`: GC percentage
- `_find_orfs()`: ORF detection (ATG → STOP)
- `_scan_motifs()`: Regulatory element detection

#### 4b. ProteinPredictionAgent
```python
class ProteinPredictionAgent:
    """Predicts protein properties from sequences"""
    
    def predict(self, orf_sequence: str) -> Dict:
        - Translate DNA to amino acids
        - Calculate molecular weight
        - Assess hydrophobicity
        - Detect signal peptides
```

#### 4c. ComparisonAgent
```python
class ComparisonAgent:
    """Compares sequences for homology"""
    
    def compare(self, seq1: str, seq2: str) -> Dict:
        - Sequence alignment
        - Similarity scoring
        - Homology detection
```

#### 4d. LiteratureAgent
```python
class LiteratureAgent:
    """Searches scientific literature"""
    
    def search(self, query: str) -> Dict:
        - PubMed search
        - Citation analysis
        - Trend identification
```

#### 4e. HypothesisAgent
```python
class HypothesisAgent:
    """Generates research hypotheses"""
    
    def generate(self, context: Dict) -> List[Dict]:
        - Pattern-based hypothesis
        - Literature-informed suggestions
        - Confidence scoring
```

### Layer 5: Tool Layer

**Location**: `src/core/adk_tools.py`

All bioinformatics functions exposed as ADK-compatible tools.

```python
def analyze_sequence(sequence: str) -> str:
    """Tool: Comprehensive sequence analysis"""
    # Returns JSON with analysis results

def predict_protein_properties(orf_sequence: str) -> str:
    """Tool: Protein physicochemical properties"""
    # Molecular weight, hydrophobicity, signal peptides

def compare_sequences(seq1: str, seq2: str) -> str:
    """Tool: Sequence alignment and homology"""

def search_literature(query: str) -> str:
    """Tool: Scientific paper discovery"""

def generate_hypotheses(context: Dict) -> str:
    """Tool: Research hypothesis generation"""

def create_visualizations(data: Dict) -> str:
    """Tool: Plot generation"""

def generate_report(data: Dict) -> str:
    """Tool: PDF report creation"""
```

### Layer 6: Infrastructure & Support

#### 6a. Session Management

**Location**: `src/core/session_manager.py`

Manages user sessions with persistence.

```python
class Session:
    """User conversation session"""
    session_id: str              # UUID
    user_id: str                 # User identifier
    created_at: datetime         # Creation timestamp
    conversation_history: List   # Message history
    context_data: Dict           # Persistent context
    
    Methods:
    - add_message()              # Store message
    - update_context()           # Update context
    - to_dict() / from_dict()    # Serialization

class SessionManager:
    """Manages multiple sessions"""
    
    Methods:
    - create_session()           # New session
    - get_session()              # Retrieve session
    - delete_session()           # Close session
    - cleanup_old_sessions()     # Maintenance
    - get_session_stats()        # Statistics
```

**Data Flow**:
```
Session Storage (JSON files)
    ↓
SessionManager (In-memory cache)
    ├─ Active sessions
    ├─ Conversation history
    └─ Context persistence
```

#### 6b. Performance Monitoring

**Location**: `src/core/monitoring.py`

Real-time metrics collection and analysis.

```python
class PerformanceMonitor:
    """Tracks execution metrics"""
    
    Tracks:
    - Execution time (latency)
    - Token usage (input/output)
    - Cost estimation
    - Error rates
    - Success rates
    
    Methods:
    - start_execution()
    - end_execution()
    - get_summary_stats()
    - export_metrics()
```

**Metrics Collected**:
| Metric | Unit | Tracked |
|--------|------|---------|
| Latency | ms | Per execution |
| Tokens Input | count | Per execution |
| Tokens Output | count | Per execution |
| Cost | USD | Per execution |
| Error Rate | % | Aggregate |
| Success Rate | % | Aggregate |

#### 6c. Utility Functions

**Visualization** (`src/utils/visualizer.py`):
```python
class VisualizationManager:
    - plot_gc_content()    # GC% sliding window
    - plot_orf_map()       # ORF linear map
    - plot_protein_scatter() # Protein properties
    - save_plot_image()    # Export to PNG
```

**Reporting** (`src/utils/reporter.py`):
```python
def create_pdf(data: Dict) -> str:
    """Generates PDF reports with:
    - Analysis summary
    - Visualizations
    - Statistics
    - Hypotheses
    """
```

**Structure Generation** (`src/utils/structure_generator.py`):
```python
class StructureGenerator:
    - generate_dna_pdb()   # PDB structure file
    - render_dna_image()   # 3D visualization
```

## Data Flow Diagrams

### Simple Chat Request

```
User Input: "What is GC content?"
    ↓
UnifiedCoordinator
    ├─ No DNA sequence detected
    └─ Route to ChatAgent
    ↓
ChatAgent.answer_question()
    ├─ Build conversation context
    ├─ Call Generative AI
    └─ Return response
    ↓
Response: "GC content is..."
```

### Full Analysis Pipeline

```
User Input: "ATGAAATAAGCG..." (DNA sequence)
    ↓
UnifiedCoordinator
    ├─ DNA sequence detected
    └─ Route to ADKCoordinator
    ↓
ADKCoordinator.run_pipeline()
    ├─ Create ADK session
    └─ Initialize LLMAgent
    ↓
ADK Runner Execution
    ├─ Step 1: analyze_sequence()
    │   └─ SequenceAnalyzerAgent
    ├─ Step 2: predict_protein_properties()
    │   └─ ProteinPredictionAgent
    ├─ Step 3: search_literature()
    │   └─ LiteratureAgent
    ├─ Step 4: generate_hypotheses()
    │   └─ HypothesisAgent
    ├─ Step 5: create_visualizations()
    │   └─ VisualizationManager
    └─ Step 6: generate_report()
        └─ PDF generation
    ↓
Results Aggregation
    ├─ Analysis summary
    ├─ Visualizations
    ├─ PDF report path
    └─ 3D structure
    ↓
Response returned to UI
```

### Session-Based Conversation

```
Message 1: "I study bacteria"
    ↓
Create/Get Session
    └─ session_id: "abc123"
    └─ conversation_history: [msg1]
    └─ context_data: {topic: "bacteria"}
    ↓
Store in SessionManager
    └─ Save to disk (sessions/abc123.json)
    └─ Cache in memory

Message 2: "Analyze this sequence"
    ↓
Load Session (abc123)
    ├─ Retrieve conversation history
    ├─ Include context in prompt
    └─ Agent has full context
    ↓
Response uses previous context
    └─ More relevant analysis
```

## Technology Stack

### Core AI/ML
- **Google Generative AI**: LLM backend
- **Google ADK**: Agent orchestration framework
- **Tenacity**: Retry logic with exponential backoff

### Data Processing
- **BioPython**: Sequence analysis
- **Pandas**: Data manipulation
- **NumPy**: Numerical computing

### Visualization
- **Plotly**: Interactive plots
- **Matplotlib**: Static graphics
- **Kaleido**: Image export

### Web & Storage
- **Streamlit**: Web UI framework
- **SQLAlchemy**: Database ORM
- **Redis**: Optional caching layer

### Utilities
- **Pydantic**: Data validation
- **python-dotenv**: Environment management
- **colorama**: Terminal colors
- **psutil**: System monitoring
- **FPDF**: PDF generation

## Deployment Architecture

### Local Development
```
User → Streamlit UI (localhost:8501)
    ↓
GeneFlow Application
    ├─ Sessions (local JSON files)
    ├─ Metrics (local JSON files)
    └─ Plots (local PNG files)
    ↓
Google Cloud APIs
    ├─ Generative AI
    └─ ADK services
```

### Production Deployment
```
Users
    ↓
Load Balancer
    ↓
Streamlit App Replicas
    ├─ Container 1
    ├─ Container 2
    └─ Container N
    ↓
Shared Storage
    ├─ Redis (sessions/cache)
    ├─ PostgreSQL (persistent data)
    └─ Cloud Storage (artifacts)
    ↓
Google Cloud APIs
```

## Scalability Considerations

### Horizontal Scaling
- Multiple Streamlit containers behind load balancer
- Shared session storage (Redis/Database)
- Distributed metrics collection

### Vertical Scaling
- Increase container resources
- Enable GPU for LLM inference
- Cache frequently used results

### Optimization Strategies
1. **Session Caching**: Redis for hot sessions
2. **Result Caching**: Cache analysis results
3. **Batch Processing**: Group similar requests
4. **Async Processing**: Background jobs for long tasks

## Error Handling & Resilience

### Retry Logic
```python
@retry(
    retry=retry_if_exception_type((ResourceExhausted, ServiceUnavailable)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=5, min=10, max=120)
)
def run_pipeline(self, sequence: str) -> Dict:
    """Automatic retry with exponential backoff"""
```

### Fallback Strategies
- Chat Agent fallback if Analysis Agent fails
- Cached results if API unavailable
- Graceful degradation of visualizations

### Error Logging
```python
logger.error(f"Sequence analysis failed: {e}")
logger.exception("Full traceback")
monitor.end_execution(..., success=False, error=str(e))
```

## Testing Strategy

### Unit Tests (`src/tests/`)
```
test_sequence_analyzer.py
    - Test GC content calculation
    - Test ORF detection
    - Test motif scanning

test_protein_prediction.py
    - Test translation accuracy
    - Test molecular weight calculation

test_adk_pipeline.py
    - Test full pipeline execution
    - Test tool integration
```

### Integration Tests
- End-to-end workflow testing
- Session management testing
- Coordinator routing testing

### Performance Tests
- Latency benchmarking
- Memory usage profiling
- Token usage tracking

## Security Considerations

1. **API Key Management**
   - Environment variable storage
   - No hardcoding in code
   - Rotate regularly

2. **Session Security**
   - Unique session IDs (UUID4)
   - Session isolation
   - Automatic expiration (24h default)

3. **Input Validation**
   - Sequence validation (ATCGN only)
   - Length restrictions
   - Malicious input filtering

4. **Data Privacy**
   - User data stored locally by default
   - No cloud storage of sequences unless configured
   - Clear data deletion policies

## Monitoring & Observability

### Metrics Exported
- `metrics/executions.json` - Execution records
- `metrics/summary_stats.json` - Aggregate statistics
- Performance dashboards in Dashboard.py

### Logging Levels
- DEBUG: Detailed execution flow
- INFO: Key milestones
- WARNING: Non-critical issues
- ERROR: Failures and exceptions

## Future Enhancements

1. **Multi-Model Support**
   - Claude, Llama, open-source models
   - Model selection per use case

2. **Advanced Caching**
   - Semantic caching for similar queries
   - Result deduplication

3. **Batch Processing**
   - Process multiple sequences
   - Scheduled analyses

4. **Integrations**
   - Database connections (DNA/protein DBs)
   - External analysis tools (BLAST, AlphaFold)
   - Slack/Teams notifications

5. **Enhanced Analytics**
   - User activity tracking
   - Analysis trend analysis
   - Cost forecasting

## Architecture Best Practices Applied

✅ **Separation of Concerns**: Clear layer separation
✅ **Single Responsibility**: Each class has one purpose
✅ **Dependency Injection**: Easy to test and extend
✅ **Error Handling**: Comprehensive error management
✅ **Logging & Monitoring**: Full observability
✅ **Documentation**: Well-documented code
✅ **Performance Optimization**: Token/cost tracking
✅ **Scalability**: Horizontal scaling ready

---

**Last Updated**: November 2024
**Version**: 1.0.0
