# 📚 GeneFlow Modules Reference

Complete documentation of all GeneFlow modules, classes, functions, and workflows.

---

## Table of Contents

1. [Main Application](#main-application-mainpy)
2. [Core Modules](#core-modules-srccorepy)
3. [Agents](#agents-srcagentspy)
4. [Utilities](#utilities-srcutilspy)
5. [UI Components](#ui-components-srcuipy)
6. [Test Modules](#test-modules-srctestspy)

---

## Main Application (`main.py`)

Entry point for launching GeneFlow. Performs dependency checks, environment validation, and launches Streamlit.

### Functions

#### `check_dependencies() → bool`
Verifies all required Python packages are installed.

**Purpose**: Ensures all dependencies are available before starting application

**Checks for**:
- streamlit (Web framework)
- google.generativeai (AI API)
- Bio/Biopython (Sequence analysis)
- pandas, plotly (Data visualization)
- pydantic, tiktoken, psutil (Support)

**Returns**: `True` if all packages installed, `False` otherwise

**Raises**: Logs missing packages and suggests pip install

**Example**:
```python
if not check_dependencies():
    print("Missing packages. Run: pip install -r requirements.txt")
    sys.exit(1)
```

---

#### `check_environment() → bool`
Validates environment configuration and creates necessary directories.

**Purpose**: Sets up application environment

**Checks**:
- GOOGLE_API_KEY environment variable

**Creates**:
- `sessions/` - Session storage
- `metrics/` - Performance metrics
- `geneflow_plots/` - Visualization outputs

**Returns**: `True` (warnings only, always proceeds)

**Example**:
```python
check_environment()
# Creates directories if not present
```

---

#### `launch_ui() → bool`
Launches the Streamlit web interface.

**Purpose**: Start web server with Home.py

**Process**:
1. Locate UI file (src/ui/Home.py)
2. Verify file exists
3. Execute: `streamlit run src/ui/Home.py`

**Returns**: `True` on success, `False` if UI file missing

**Example**:
```python
if not launch_ui():
    print("UI launch failed")
    sys.exit(1)
```

---

#### `main()`
Main application entry point orchestrating all startup checks.

**Workflow**:
```
1. Print welcome banner
2. check_dependencies()
3. check_environment()
4. launch_ui()
5. Exit with code 1 if any check fails
```

**Example**:
```bash
python main.py
# Output:
# ============================================================
# 🧬 GeneFlow: ADK-Powered Bioinformatics Copilot
# ============================================================
# 📱 Opening GeneFlow UI in your browser...
```

---

## Core Modules (`src/core/`)

### `session_manager.py`

Manages user sessions, conversation history, and persistent context.

#### Class: `Session`

Represents a single conversation session.

**Attributes**:
```python
session_id: str                    # Unique UUID
user_id: str                       # User identifier (default: "anonymous")
created_at: datetime               # Creation timestamp
last_accessed: datetime            # Last access time
conversation_history: List[Dict]   # Message history
context_data: Dict[str, Any]       # Persistent context
metadata: Dict[str, Any]           # Custom metadata
active: bool                       # Session status
```

**Methods**:

##### `add_message(role: str, content: str, metadata: Dict = None) → None`
Append message to conversation history.

**Parameters**:
- `role` (str): "user", "assistant", or "system"
- `content` (str): Message content
- `metadata` (Dict, optional): Additional metadata

**Updates**:
- `conversation_history` - New message appended
- `last_accessed` - Set to current time

**Example**:
```python
session = Session(user_id="researcher_001")
session.add_message("user", "Analyze ATGAAA...")
session.add_message("assistant", "Analysis shows...")
```

---

##### `update_context(key: str, value: Any) → None`
Store persistent context data.

**Parameters**:
- `key` (str): Context key
- `value` (Any): Context value

**Purpose**: Maintain analysis state across messages

**Example**:
```python
session.update_context("current_sequence", "ATGAAA...")
session.update_context("species", "bacteria")
```

---

##### `get_context(key: str = None) → Any`
Retrieve context data.

**Parameters**:
- `key` (str, optional): Specific key (returns all if None)

**Returns**:
- Context value if key provided
- Full context dictionary if no key

**Example**:
```python
sequence = session.get_context("current_sequence")
all_context = session.get_context()
```

---

##### `to_dict() → Dict[str, Any]`
Serialize session to dictionary for storage.

**Returns**: Dictionary with all session fields

**Example**:
```python
session_data = session.to_dict()
json.dump(session_data, open("session.json", "w"))
```

---

##### `from_dict(data: Dict) → Session` (class method)
Deserialize session from dictionary.

**Parameters**:
- `data` (Dict): Dictionary with session data

**Returns**: Reconstructed Session instance

**Example**:
```python
data = json.load(open("session.json"))
session = Session.from_dict(data)
```

---

#### Class: `SessionManager`

Manages multiple sessions with persistence and cleanup.

**Attributes**:
```python
storage_path: Path                 # Directory for session files
max_session_age: timedelta         # Max session age (default: 24h)
sessions: Dict[str, Session]       # Active session cache
```

**Methods**:

##### `create_session(user_id: str = None) → Session`
Create and persist new session.

**Parameters**:
- `user_id` (str, optional): User identifier

**Returns**: New Session instance

**Process**:
1. Generate unique session_id
2. Create Session object
3. Store in memory cache
4. Persist to disk

**Example**:
```python
manager = SessionManager()
session = manager.create_session(user_id="user_123")
print(session.session_id)  # UUID
```

---

##### `get_session(session_id: str) → Session | None`
Retrieve existing session and update last_accessed.

**Parameters**:
- `session_id` (str): Session identifier

**Returns**: Session or None if not found

**Updates**:
- `last_accessed` timestamp
- Saves to disk

**Example**:
```python
session = manager.get_session("session_abc123")
if session:
    print(f"Session has {len(session.conversation_history)} messages")
```

---

##### `get_or_create_session(session_id: str = None, user_id: str = None) → Session`
Retrieve existing or create new session.

**Parameters**:
- `session_id` (str, optional): Session to retrieve
- `user_id` (str, optional): User for new session

**Returns**: Existing or new Session

**Logic**:
```
if session_id provided and exists:
    return existing session
else:
    create_session(user_id)
```

**Example**:
```python
session = manager.get_or_create_session(
    session_id="existing_or_new",
    user_id="user_123"
)
```

---

##### `delete_session(session_id: str) → None`
Mark session as inactive and remove from cache.

**Parameters**:
- `session_id` (str): Session to delete

**Process**:
1. Set `active = False`
2. Persist deletion to disk
3. Remove from memory

**Example**:
```python
manager.delete_session("session_abc123")
```

---

##### `cleanup_old_sessions() → None`
Remove sessions older than `max_session_age`.

**Process**:
1. Identify expired sessions (>24h old by default)
2. Delete each expired session
3. Log cleanup count

**Use**: Call periodically or after peak hours

**Example**:
```python
manager.cleanup_old_sessions()  # Removes >24h sessions
```

---

##### `get_all_sessions() → List[Session]`
Get all active sessions.

**Returns**: List of active Session objects

**Example**:
```python
sessions = manager.get_all_sessions()
print(f"Active sessions: {len(sessions)}")
```

---

##### `get_session_stats() → Dict[str, Any]`
Get statistics about sessions.

**Returns**:
```python
{
    "total_sessions": int,
    "active_today": int,
    "total_messages": int,
    "avg_messages_per_session": float
}
```

**Example**:
```python
stats = manager.get_session_stats()
print(f"Avg messages per session: {stats['avg_messages_per_session']}")
```

---

### `monitoring.py`

Real-time performance monitoring and metrics collection.

#### Class: `MetricSnapshot`

Single point-in-time metric measurement.

**Attributes**:
```python
timestamp: str                     # ISO format timestamp
metric_name: str                   # Metric identifier
value: float                       # Measured value
labels: Dict[str, str]             # Classification labels
```

**Methods**:

##### `to_dict() → Dict[str, Any]`
Convert to dictionary for serialization.

---

#### Class: `AgentExecutionMetrics`

Comprehensive metrics for single agent execution.

**Attributes**:
```python
agent_name: str                    # Agent identifier
execution_id: str                  # Unique execution ID
start_time: float                  # Unix timestamp start
end_time: float                    # Unix timestamp end
duration_seconds: float            # Total duration
tokens_input: int                  # Input tokens used
tokens_output: int                 # Output tokens generated
tokens_total: int                  # Total tokens
cost_estimate: float               # Cost in USD
success: bool                      # Execution success
error: str (optional)              # Error message if failed
tool_calls: List[str]              # Names of tools called
```

---

#### Class: `PerformanceMonitor`

Real-time performance monitoring with statistics.

**Attributes**:
```python
storage_path: Path                 # Metric storage directory
metrics: List[MetricSnapshot]      # Collected metrics
executions: List[AgentExecutionMetrics]  # Execution records
pricing: Dict                      # Model pricing
```

**Methods**:

##### `start_execution(agent_name: str) → str`
Begin execution tracking.

**Parameters**:
- `agent_name` (str): Agent identifier

**Returns**: Unique execution_id for tracking

**Example**:
```python
monitor = PerformanceMonitor()
exec_id = monitor.start_execution("sequence_analyzer")
```

---

##### `end_execution(agent_name: str, execution_id: str, start_time: float, tokens_input: int, tokens_output: int, model: str, success: bool, error: str = None) → None`
Complete execution tracking and calculate metrics.

**Parameters**:
- `agent_name` (str): Agent name
- `execution_id` (str): ID from start_execution()
- `start_time` (float): Unix timestamp
- `tokens_input` (int): Input tokens
- `tokens_output` (int): Output tokens
- `model` (str): Model name
- `success` (bool): Execution success
- `error` (str, optional): Error message

**Calculates**:
- Duration: `end_time - start_time`
- Total tokens: `tokens_input + tokens_output`
- Cost estimate: tokens * pricing[model]

**Example**:
```python
start = time.time()
exec_id = monitor.start_execution("coordinator")

# ... execution ...

monitor.end_execution(
    agent_name="coordinator",
    execution_id=exec_id,
    start_time=start,
    tokens_input=500,
    tokens_output=300,
    model="gemini-2.5-flash",
    success=True
)
```

---

##### `get_summary_stats() → Dict[str, Any]`
Generate time-windowed statistics.

**Returns**:
```python
{
    "total_executions": int,
    "successful_executions": int,
    "failed_executions": int,
    "avg_latency_ms": float,
    "total_tokens": int,
    "total_cost": float,
    "by_agent": {
        "agent_name": {...metrics...}
    }
}
```

**Example**:
```python
stats = monitor.get_summary_stats()
print(f"Total cost: ${stats['total_cost']:.2f}")
```

---

##### `export_metrics() → None`
Export metrics to disk (JSON files).

**Output Files**:
- `metrics/executions.json` - All execution records
- `metrics/summary_stats.json` - Summary statistics

**Example**:
```python
monitor.export_metrics()  # Save metrics
```

---

### `adk_tools.py`

All bioinformatics functions exposed as ADK-compatible tools.

#### Function: `analyze_sequence(sequence: str) → str`

**Purpose**: Comprehensive DNA/RNA sequence analysis

**Input**:
- `sequence` (str): DNA sequence (ATCGN characters, case-insensitive)

**Returns**: JSON string with analysis results

**Output Format**:
```json
{
    "valid": true,
    "sequence_type": "DNA",
    "length": 100,
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
            "position": 15,
            "sequence": "TATAAA"
        }
    ]
}
```

**Process**:
1. Clean sequence (remove whitespace, uppercase)
2. Validate composition (ATCGN only)
3. Calculate GC content: (G+C)/length * 100
4. Find ORFs (ATG start → TAA/TAG/TGA stop)
5. Scan for regulatory motifs

**Example**:
```python
result_json = analyze_sequence("ATGAAATAAGCGTAG")
result = json.loads(result_json)
print(f"GC%: {result['gc_percent']}, ORFs: {len(result['orfs'])}")
```

---

#### Function: `predict_protein_properties(orf_sequence: str, orf_start: int = 0, orf_end: int = None) → str`

**Purpose**: Predict protein physicochemical properties from DNA sequence

**Input**:
- `orf_sequence` (str): DNA ORF (starts with ATG, length divisible by 3)
- `orf_start` (int, optional): Start position in parent sequence
- `orf_end` (int, optional): End position in parent sequence

**Returns**: JSON string with protein predictions

**Output Format**:
```json
{
    "orf_id": "ORF_0_90",
    "aa_sequence": "MKYKVLELSTL...",
    "length": 30,
    "properties": {
        "molecular_weight": 3456.7,
        "hydrophobicity": 0.45
    },
    "signal_peptide": false
}
```

**Process**:
1. Validate ORF format (ATG start, length % 3 == 0)
2. Translate to amino acids (using codon table)
3. Calculate molecular weight (sum of AA masses)
4. Calculate hydrophobicity (Kyte-Doolittle scale)
5. Check for signal peptide (N-terminal prediction)

**Codon Translation**:
- ATG → M (Methionine)
- TTT, TTC → F (Phenylalanine)
- TAA, TAG, TGA → STOP

**Example**:
```python
props_json = predict_protein_properties("ATGAAATAAGCGTAG")
props = json.loads(props_json)
print(f"MW: {props['properties']['molecular_weight']} Da")
```

---

#### Function: `compare_sequences(seq1: str, seq2: str) -> str`

**Purpose**: Sequence alignment and homology detection

**Input**:
- `seq1`, `seq2` (str): Two sequences to compare

**Returns**: JSON with alignment and similarity

**Output Format**:
```json
{
    "similarity_score": 85.5,
    "identity_percent": 82.0,
    "alignment": {
        "query": "ATGAA-TAAGCG",
        "target": "ATGAAATAGCG-",
        "match": "ATGAA TAAGCG"
    },
    "homology_prediction": "High homology detected"
}
```

---

#### Function: `search_literature(query: str) -> str`

**Purpose**: Find relevant scientific literature

**Input**:
- `query` (str): Search query (gene name, protein, pathway, etc.)

**Returns**: JSON with paper summaries

**Output Format**:
```json
{
    "total_results": 45,
    "papers": [
        {
            "pmid": "12345678",
            "title": "Paper title...",
            "authors": ["Author1", "Author2"],
            "year": 2023,
            "abstract": "Summary..."
        }
    ]
}
```

---

#### Function: `generate_hypotheses(context: Dict) -> str`

**Purpose**: Generate research hypotheses based on analysis

**Input**:
- `context` (Dict): Analysis results and literature

**Returns**: JSON with generated hypotheses

**Output Format**:
```json
{
    "hypotheses": [
        {
            "hypothesis": "The sequence may encode...",
            "confidence": 0.85,
            "rationale": "Based on...",
            "supporting_evidence": ["Evidence1", "Evidence2"]
        }
    ]
}
```

---

#### Function: `create_visualizations(data: Dict) -> str`

**Purpose**: Generate interactive plots

**Input**:
- `data` (Dict): Analysis data

**Returns**: JSON with file paths to generated visualizations

**Output Format**:
```json
{
    "plots": [
        {
            "name": "gc_content",
            "path": "geneflow_plots/gc_plot.png",
            "format": "PNG"
        }
    ]
}
```

---

#### Function: `generate_report(data: Dict) -> str`

**Purpose**: Create comprehensive PDF report

**Input**:
- `data` (Dict): Complete analysis data

**Returns**: JSON with report file path

**Output Format**:
```json
{
    "report_path": "reports/report_abc123.pdf",
    "pages": 12,
    "file_size": 2547890,
    "generated_at": "2024-01-15T10:30:00Z"
}
```

---

### `agent_factory.py`

Factory for creating specialized agents.

#### Function: `create_chat_agent() → ChatAgent`
Create lightweight chat agent.

#### Function: `create_analysis_agent() → ADKCoordinator`
Create full-featured analysis agent.

#### Function: `create_custom_agent(name: str, instruction: str, tools: List) → LlmAgent`
Create custom ADK agent.

---

### `context_manager.py`

Manages execution context and state.

#### Class: `ExecutionContext`
Maintains current execution state across function calls.

**Attributes**:
- `session_id` - Current session
- `user_id` - Current user
- `execution_id` - Current execution
- `agent_name` - Current agent
- `start_time` - Execution start

---

### `memory.py`

Memory management for agents.

#### Class: `ConversationMemory`
Manages conversation history with attention mechanism.

**Methods**:
- `add_message()` - Add to memory
- `get_recent(n: int)` - Last N messages
- `get_relevant(query: str)` - Semantically similar messages
- `clear()` - Clear memory

---

## Agents (`src/agents/`)

### `unified_coordinator.py`

Intelligent router between chat and analysis agents.

#### Class: `UnifiedCoordinator`

**Purpose**: Route requests to appropriate agent based on content

**Attributes**:
```python
session_manager: SessionManager
performance_monitor: PerformanceMonitor
chat_agent: ChatAgent
analysis_agent: ADKCoordinator
```

**Methods**:

##### `__init__(session_manager: SessionManager = None, performance_monitor: PerformanceMonitor = None, model: str = "gemini-2.5-flash")`

Initialize coordinator with optional managers.

**Example**:
```python
coordinator = UnifiedCoordinator()
# Or with custom managers:
coordinator = UnifiedCoordinator(
    session_manager=custom_session_mgr,
    performance_monitor=custom_monitor,
    model="gemini-2.5-flash"
)
```

---

##### `_contains_dna_sequence(message: str) → bool`

Detect DNA sequence in message.

**Logic**: Regex pattern match for 20+ consecutive nucleotides

**Pattern**: `[ATCGURYKMSWBDHVN]{20,}` (case-insensitive)

**Returns**: `True` if DNA sequence found

**Example**:
```python
coordinator._contains_dna_sequence("Check ATGAAATAAGCGTAGCTAGC sequence")  # True
coordinator._contains_dna_sequence("What is GC content?")  # False
```

---

##### `process_message(message: str, session_id: str = None, user_id: str = None) → Dict[str, Any]`

Main routing method for messages.

**Process**:
1. Get or create session
2. Add message to conversation
3. Check if contains DNA sequence
4. Route to ChatAgent or ADKCoordinator
5. Track performance metrics
6. Return result

**Parameters**:
- `message` (str): User message
- `session_id` (str, optional): Session ID for continuity
- `user_id` (str, optional): User identifier

**Returns**:
```python
{
    "success": bool,
    "session_id": str,
    "response": str,
    "timestamp": str,
    "error": str (optional)
}
```

**Example**:
```python
# Chat request
result1 = coordinator.process_message(
    "What is an ORF?",
    session_id="user_123"
)

# Analysis request
result2 = coordinator.process_message(
    "ATGAAATAAGCGTAGCTAG",
    session_id="user_123"
)
```

---

##### `run_pipeline(sequence: str, session_id: str = None, metadata: Dict = None) → Dict[str, Any]`

Explicitly run full analysis pipeline.

**Parameters**:
- `sequence` (str): DNA sequence
- `session_id` (str, optional): Session ID
- `metadata` (Dict, optional): Custom metadata

**Returns**: Complete analysis results

**Example**:
```python
result = coordinator.run_pipeline(
    sequence="ATGAAATAAGCGTAGCTAG",
    session_id="user_123",
    metadata={"source": "user_input"}
)
```

---

##### `get_session_summary(session_id: str) → Dict[str, Any]`

Get session information.

**Returns**:
```python
{
    "session_id": str,
    "created_at": str,
    "last_accessed": str,
    "message_count": int,
    "context_keys": List[str]
}
```

---

##### `get_performance_stats() → Dict[str, Any]`

Get performance statistics.

**Returns**: Aggregated metrics from performance monitor

---

### `adk_coordinator.py`

Main ADK-based analysis orchestrator using Google ADK.

#### Class: `ADKCoordinator`

**Purpose**: Full-featured bioinformatics analysis using ADK with tools

**Attributes**:
```python
model: str                         # LLM model name
session_manager: SessionManager
performance_monitor: PerformanceMonitor
session_service: InMemorySessionService
memory_service: InMemoryMemoryService
artifact_service: InMemoryArtifactService
agent: LlmAgent                    # Main coordinating agent
app: App                           # ADK App
runner: Runner                     # ADK Runner
```

**Architecture**:
```
ADK Services (Stateless)
    ↓
LLMAgent (with tools)
    ↓
ADK Runner (orchestration)
    ↓
Tool Execution
    ├─ analyze_sequence()
    ├─ predict_protein_properties()
    ├─ search_literature()
    ├─ generate_hypotheses()
    ├─ create_visualizations()
    └─ generate_report()
```

**Methods**:

##### `__init__(session_manager: SessionManager = None, performance_monitor: PerformanceMonitor = None, model: str = "gemini-2.5-flash")`

Initialize ADK coordinator.

**Process**:
1. Configure Google API
2. Create ADK services
3. Create LLMAgent with tools
4. Create ADK App
5. Create Runner

**Raises**: `RuntimeError` if GOOGLE_API_KEY not set

**Example**:
```python
coordinator = ADKCoordinator()
# Automatically initializes all ADK infrastructure
```

---

##### `_create_agent() → LlmAgent`

Create main coordinating agent with system instruction.

**System Instruction**: Bioinformatics expert with access to all tools

**Tools Provided**:
- analyze_sequence
- predict_protein_properties
- search_literature
- generate_hypotheses
- create_visualizations
- generate_report

**Returns**: Configured LlmAgent

---

##### `process_message(message: str, session_id: str = None, user_id: str = None, auto_pipeline: bool = False) → Dict[str, Any]`

Process message using ADK Runner pattern.

**Process**:
1. Create/get session
2. Build conversation context from history
3. Create ADK session
4. Run agent with message
5. Collect response from event stream
6. Store in session
7. Track metrics

**Parameters**:
- `message` (str): User message
- `session_id` (str, optional): Session ID
- `user_id` (str, optional): User ID
- `auto_pipeline` (bool): Auto-run full pipeline if DNA detected

**Returns**:
```python
{
    "success": bool,
    "session_id": str,
    "response": str,
    "timestamp": str,
    "error": str (optional)
}
```

**Example**:
```python
result = coordinator.process_message(
    "Can you analyze this sequence? ATGAAATAAGCG...",
    session_id="user_123"
)
print(result['response'])
```

---

##### `run_pipeline(sequence: str, session_id: str = None, metadata: Dict = None) → Dict[str, Any]`

Execute complete bioinformatics pipeline.

**Pipeline Steps**:
1. **Analyze Sequence**: GC content, ORFs, motifs
2. **Search Literature**: Related papers
3. **Generate Hypotheses**: Research directions
4. **Create Visualizations**: Plots and charts
5. **Generate Report**: PDF document
6. **Structure Generation**: 3D modeling

**Parameters**:
- `sequence` (str): DNA sequence (min 50 bp recommended)
- `session_id` (str, optional): Session for context
- `metadata` (Dict, optional): Custom metadata

**Returns**:
```python
{
    "success": bool,
    "session_id": str,
    "response": str,
    "results": {
        "sequence": str,
        "sequence_length": int,
        "analysis": Dict,
        "literature": str,
        "hypotheses": List,
        "visualizations": Dict,
        "report": Dict
    },
    "execution_time_seconds": float,
    "timestamp": str,
    "error": str (optional)
}
```

**Detailed Results Structure**:
```python
results = {
    "analysis": {
        "gc_percent": 42.5,
        "orfs_count": 3,
        "orfs": [
            {
                "start": 0,
                "end": 90,
                "frame": 1,
                "sequence": "ATG...TAG"
            }
        ],
        "motifs": [
            {
                "name": "TATA_box",
                "position": 15
            }
        ],
        "key_findings": ["Finding1", "Finding2"]
    },
    "literature": "Summary of relevant papers...",
    "hypotheses": [
        {
            "hypothesis": "...",
            "confidence": 0.85,
            "rationale": "..."
        }
    ],
    "visualizations": {
        "output_directory": "geneflow_plots/",
        "structure_pdb": "geneflow_structures/dna_model.pdb",
        "structure_image": "geneflow_plots/structure_3d.png"
    },
    "report": {
        "report_path": "reports/report_abc123.pdf"
    }
}
```

**Retry Logic**: Automatically retries on ResourceExhausted or ServiceUnavailable with exponential backoff

**Example**:
```python
result = coordinator.run_pipeline(
    sequence="ATGAAATATAAAGCGTACGTGCTTGAATGCCTTATAAACGTAGCTAG",
    session_id="analysis_001"
)

if result['success']:
    print(f"Analysis complete!")
    print(f"Report: {result['results']['report']['report_path']}")
else:
    print(f"Error: {result['error']}")
```

---

##### `get_session_summary(session_id: str) → Dict[str, Any]`

Get session metadata and statistics.

**Returns**:
```python
{
    "session_id": str,
    "created_at": str,
    "last_accessed": str,
    "message_count": int,
    "context_keys": List[str]
}
```

---

##### `get_performance_stats() → Dict[str, Any]`

Get performance metrics for all executions.

**Returns**: Summary statistics from performance monitor

---

##### `_extract_final_summary(response_text: str) → str`

Extract and format final summary from agent response.

**Process**:
1. Check if response is JSON
2. If JSON: format into readable markdown
3. If text: extract summary sections
4. Remove intermediate steps
5. Clean up whitespace

**Returns**: Formatted summary text

---

##### `_parse_pipeline_response(response_text: str, sequence: str) → Dict[str, Any]`

Parse structured response from pipeline execution.

**Extracts**:
- Sequence analysis (GC%, ORFs, motifs)
- Literature summary
- Hypotheses

**Returns**: Structured analysis data

---

##### `cleanup()`

Cleanup old sessions and export metrics.

**Actions**:
1. Remove expired sessions
2. Export metrics to disk

---

### `chat_agent.py`

Lightweight conversational agent for general questions.

#### Class: `ChatAgent`

**Purpose**: Fast bioinformatics Q&A (1-3 seconds)

**Attributes**:
```python
model: str                         # LLM model name
client: genai.GenerativeModel      # Configured model
system_instruction: str            # System prompt
```

**Methods**:

##### `__init__(model: str = "gemini-2.0-flash-exp")`

Initialize chat agent.

**Parameters**:
- `model` (str): Model to use

**Raises**: `RuntimeError` if GOOGLE_API_KEY not set

**Example**:
```python
chat = ChatAgent()
```

---

##### `answer_question(question: str, conversation_history: List = []) → str`

Answer a bioinformatics question.

**Process**:
1. Build conversation context from history
2. Format message with system instruction
3. Call Generative AI
4. Extract and return response

**Parameters**:
- `question` (str): User question
- `conversation_history` (List, optional): Previous messages

**Returns**: Conversational response text

**Example**:
```python
history = [
    {"role": "user", "content": "I study bacteria"},
    {"role": "assistant", "content": "That's interesting..."}
]

response = chat.answer_question(
    "What's the role of GC content in bacterial genomes?",
    conversation_history=history
)
print(response)
```

---

### `sequence_analyzer.py`

DNA/RNA sequence analysis engine.

#### Class: `SequenceAnalyzerAgent`

**Purpose**: Analyze sequences for properties, ORFs, and motifs

**Attributes**:
```python
motifs_db: Dict[str, str]          # Regex patterns for motifs
```

**Motifs Included**:
- TATA_box: `TATA[AT]A`
- CAAT_box: `CAAT`
- PolyA_signal: `AATAAA`
- Kozak_consensus: `[AG]CCATGG`
- Start_codon: `ATG`
- Stop_codon: `TAA|TAG|TGA`

**Methods**:

##### `analyze(sequence: str) → Dict[str, Any]`

Comprehensive sequence analysis.

**Process**:
1. Clean sequence
2. Validate composition
3. Calculate GC content
4. Find ORFs
5. Scan motifs

**Returns**:
```python
{
    "valid": bool,
    "sequence_type": "DNA" or "RNA",
    "length": int,
    "gc_percent": float,
    "orfs": List[Dict],
    "motifs": List[Dict],
    "cleaned_sequence": str
}
```

**Example**:
```python
agent = SequenceAnalyzerAgent()
result = agent.analyze("ATGAAATAAGCGTAG")
print(f"GC%: {result['gc_percent']}")
print(f"ORFs: {len(result['orfs'])}")
```

---

##### `_clean_sequence(sequence: str) → str`

Normalize sequence input.

**Process**:
1. Remove whitespace
2. Convert to uppercase
3. Remove numbers

**Returns**: Cleaned sequence

---

##### `_validate_sequence(sequence: str) → Tuple[bool, str]`

Validate sequence composition.

**Checks**:
- Only ATCGUN characters (with wildcards)
- Non-empty length

**Returns**: Tuple of (valid: bool, error_message: str)

---

##### `_calculate_gc(sequence: str) → float`

Calculate GC content percentage.

**Formula**: (G_count + C_count) / total_length * 100

**Returns**: GC percentage (0-100)

---

##### `_find_orfs(sequence: str) → List[Dict]`

Find Open Reading Frames.

**Process**:
1. Find all ATG start codons
2. For each ATG, find first stop codon (TAA, TAG, TGA)
3. Verify reading frame (multiple of 3)
4. Extract ORF information

**Returns**:
```python
[
    {
        "start": 0,
        "end": 90,
        "sequence": "ATG...TAG",
        "length": 90,
        "frame": 1
    }
]
```

---

##### `_scan_motifs(sequence: str) → List[Dict]`

Scan for regulatory motifs.

**Process**:
1. For each motif pattern
2. Find all matches
3. Record position and sequence

**Returns**:
```python
[
    {
        "name": "TATA_box",
        "position": 15,
        "sequence": "TATAAA",
        "match": "TATA"
    }
]
```

---

### `protein_prediction.py`

Protein property prediction from DNA.

#### Class: `ProteinPredictionAgent`

**Methods**:

##### `predict(orf_sequence: str) → Dict[str, Any]`

Predict protein properties.

**Returns**: Protein analysis results

---

### `comparison.py`

Sequence comparison and alignment.

#### Class: `ComparisonAgent`

**Methods**:

##### `compare(seq1: str, seq2: str) → Dict[str, Any]`

Compare two sequences.

**Returns**: Alignment and similarity data

---

### `hypothesis.py`

Research hypothesis generation.

#### Class: `HypothesisAgent`

**Methods**:

##### `generate(context: Dict) → List[Dict]`

Generate research hypotheses.

**Returns**: List of hypotheses with confidence scores

---

### `literature.py`

Scientific literature search.

#### Class: `LiteratureAgent`

**Methods**:

##### `search(query: str) → Dict[str, Any]`

Search scientific literature.

**Returns**: Paper summaries and metadata

---

## Utilities (`src/utils/`)

### `visualizer.py`

Genomic data visualization using Plotly.

#### Class: `VisualizationManager`

**Methods**:

##### `plot_gc_content(sequence: str, window_size: int = 100) → go.Figure`

Generate sliding window GC content plot.

**Process**:
1. Calculate GC% for sliding windows
2. Use 10 bp step size
3. Create Plotly line chart

**Returns**: Interactive Plotly Figure

**Example**:
```python
fig = VisualizationManager.plot_gc_content("ATGAAA...", window_size=100)
fig.show()
fig.write_image("gc_plot.png")
```

---

##### `plot_orf_map(orfs: List[Dict], seq_length: int) → go.Figure`

Linear ORF position mapping.

**Returns**: Plotly Figure with ORFs on sequence

---

##### `plot_protein_scatter(proteins: List[Dict]) → go.Figure`

Protein property correlation plot.

**Returns**: Scatter plot with property relationships

---

##### `save_plot_image(fig: go.Figure, filename: str, directory: str) → str`

Save plot to PNG file.

**Returns**: File path

---

### `reporter.py`

PDF report generation.

#### Function: `create_pdf(data: Dict, output_dir: str, filename: str) → str`

Generate comprehensive PDF report.

**Includes**:
- Analysis summary
- Sequence statistics
- Visualizations
- ORF information
- Hypotheses
- Literature references

**Returns**: Path to generated PDF

**Example**:
```python
report_path = create_pdf(
    data={
        "sequence_analysis": {...},
        "sequence_length": 1000,
        "literature": {...},
        "hypotheses": [...]
    },
    output_dir="reports",
    filename="analysis_report.pdf"
)
```

---

### `structure_generator.py`

3D DNA/protein structure modeling.

#### Class: `StructureGenerator`

**Methods**:

##### `generate_dna_pdb(sequence: str, output_path: str) → str`

Generate PDB format 3D structure.

**Returns**: Path to PDB file

---

##### `render_dna_image(pdb_path: str, output_path: str) → str`

Render 3D structure to image.

**Returns**: Path to PNG image

---

## UI Components (`src/ui/`)

### `Home.py`

Landing page with features and navigation.

**Components**:
- Hero header with tagline
- Feature cards
- Quick start buttons
- System statistics

---

### `pages/1_Dashboard.py`

Analytics and session dashboard.

**Features**:
- Session statistics
- Performance metrics
- Recent analyses
- Usage trends

---

### `pages/2_Chat.py`

Interactive chat interface.

**Features**:
- Message input
- Conversation history
- Session management
- Response streaming

---

### `pages/3_Analysis.py`

Full sequence analysis interface.

**Features**:
- Sequence input
- Advanced options
- Real-time progress
- Results visualization

---

## Test Modules (`src/tests/`)

### `test_sequence_analyzer.py`

Unit tests for sequence analysis.

**Tests**:
- GC content calculation
- ORF detection
- Motif scanning

---

### `test_protein_prediction.py`

Unit tests for protein prediction.

**Tests**:
- Codon translation
- Molecular weight calculation
- Property predictions

---

### `test_adk_pipeline.py`

Integration tests for ADK pipeline.

**Tests**:
- Full pipeline execution
- Tool integration
- Result aggregation

---

## Configuration & Constants

### Environment Variables

```env
GOOGLE_API_KEY              # Required: Google API key
LOG_LEVEL                   # Optional: logging.DEBUG/INFO/WARNING/ERROR
SESSION_MAX_AGE_HOURS       # Optional: session lifetime (default: 24)
MAX_SEQUENCE_LENGTH         # Optional: max sequence size (default: 100000)
CACHE_ENABLED               # Optional: enable caching (default: true)
REDIS_URL                   # Optional: Redis connection for caching
```

### File Paths

```
sessions/              # Session JSON files
metrics/              # Performance metrics JSON files
geneflow_plots/       # Generated visualizations
geneflow_structures/  # 3D structure files (PDB)
reports/              # Generated PDF reports
```

---

## Data Models

### Message Format

```python
{
    "role": "user" | "assistant" | "system",
    "content": str,
    "timestamp": ISO_datetime_str,
    "metadata": {
        "execution_id": str,
        "tokens_used": int
    }
}
```

### Analysis Result Format

```python
{
    "valid": bool,
    "sequence_type": "DNA" | "RNA",
    "length": int,
    "gc_percent": float,
    "orfs": [
        {
            "start": int,
            "end": int,
            "sequence": str,
            "length": int,
            "frame": int
        }
    ],
    "motifs": [
        {
            "name": str,
            "position": int,
            "sequence": str
        }
    ]
}
```

---

## Error Handling

### Common Errors & Solutions

#### InvalidSequenceError
```python
Cause: Non-DNA characters in sequence
Solution: Use only A, T, C, G, U, N characters
```

#### SessionNotFoundError
```python
Cause: Session ID doesn't exist or expired
Solution: Create new session or use get_or_create_session()
```

#### APIError
```python
Cause: Google API failure
Solution: Retry with exponential backoff (automatic in ADKCoordinator)
```

---

## Performance Optimization Tips

1. **Use ChatAgent for simple questions** (1-3 seconds)
2. **Cache frequently analyzed sequences**
3. **Limit sequence length** for faster processing
4. **Enable Redis caching** for production
5. **Batch multiple analyses** when possible

---

**Last Updated**: November 2024
**Version**: 1.0.0
