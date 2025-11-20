# 🔌 GeneFlow API & Integration Guide

Comprehensive guide for integrating GeneFlow into external applications and workflows.

---

## Table of Contents

1. [Quick Start API](#quick-start-api)
2. [Core API](#core-api)
3. [Advanced Integration](#advanced-integration)
4. [Error Handling](#error-handling)
5. [Examples](#examples)

---

## Quick Start API

### Installation

```bash
# Clone and install
git clone https://github.com/suriyasureshok/geneflow.git
cd GeneFlow
pip install -r requirements.txt
```

### Basic Usage

```python
from src.agents.unified_coordinator import UnifiedCoordinator

# Initialize
coordinator = UnifiedCoordinator()

# Quick chat
response = coordinator.process_message("What is GC content?")
print(response['response'])

# Sequence analysis
result = coordinator.run_pipeline("ATGAAATAAGCG...")
print(f"Analysis complete! GC%: {result['results']['analysis']['gc_percent']}")
```

---

## Core API

### UnifiedCoordinator

Main entry point for all operations.

#### Initialization

```python
from src.agents.unified_coordinator import UnifiedCoordinator
from src.core.session_manager import SessionManager
from src.core.monitoring import PerformanceMonitor

# Simple initialization
coordinator = UnifiedCoordinator()

# With custom managers
coordinator = UnifiedCoordinator(
    session_manager=SessionManager(storage_path="sessions"),
    performance_monitor=PerformanceMonitor(storage_path="metrics"),
    model="gemini-2.5-flash"
)
```

#### `process_message(message, session_id=None, user_id=None)`

Process a single message (auto-routes based on content).

**Request**:
```python
result = coordinator.process_message(
    message="Your question or sequence here",
    session_id="optional_session_123",
    user_id="optional_user_123"
)
```

**Response**:
```python
{
    "success": True,
    "session_id": "session_uuid",
    "response": "Response text",
    "timestamp": "2024-01-15T10:30:00Z",
    "error": None  # Optional, only if success=False
}
```

**Routing Logic**:
- DNA sequence (20+ bp) → ADKCoordinator (30-60s)
- General question → ChatAgent (1-3s)

#### `run_pipeline(sequence, session_id=None, metadata=None)`

Execute full bioinformatics pipeline.

**Request**:
```python
result = coordinator.run_pipeline(
    sequence="ATGAAATATAAAGCGTACGTGCTTGAATGCCTTATAAACGTAGCTAG",
    session_id="session_123",
    metadata={"source": "experiment_001", "organism": "bacteria"}
)
```

**Response**:
```python
{
    "success": True,
    "session_id": "session_uuid",
    "response": "Summary text",
    "results": {
        "sequence": "ATGAAA...CTAG",
        "sequence_length": 50,
        "analysis": {
            "gc_percent": 42.0,
            "orfs": [
                {
                    "start": 0,
                    "end": 48,
                    "frame": 1,
                    "sequence": "ATGAAATAA..."
                }
            ],
            "motifs": [],
            "key_findings": ["ORF identified"]
        },
        "literature": "Related research summary...",
        "hypotheses": [
            {
                "hypothesis": "May encode...",
                "confidence": 0.85,
                "rationale": "Based on..."
            }
        ],
        "visualizations": {
            "output_directory": "geneflow_plots/",
            "structure_pdb": "geneflow_structures/dna_model_123.pdb",
            "structure_image": "geneflow_plots/structure_3d.png"
        },
        "report": {
            "report_path": "reports/report_123.pdf"
        }
    },
    "execution_time_seconds": 45.3,
    "timestamp": "2024-01-15T10:30:00Z"
}
```

#### `get_session_summary(session_id)`

Retrieve session metadata.

**Request**:
```python
summary = coordinator.get_session_summary("session_123")
```

**Response**:
```python
{
    "session_id": "session_uuid",
    "created_at": "2024-01-15T10:00:00Z",
    "last_accessed": "2024-01-15T10:35:00Z",
    "message_count": 5,
    "context_keys": ["current_sequence", "organism"]
}
```

#### `get_performance_stats()`

Get performance metrics.

**Request**:
```python
stats = coordinator.get_performance_stats()
```

**Response**:
```python
{
    "total_executions": 42,
    "successful_executions": 40,
    "failed_executions": 2,
    "avg_latency_ms": 2850,
    "total_tokens": 125000,
    "total_cost": 1.25,
    "by_agent": {
        "chat": {
            "executions": 30,
            "avg_latency_ms": 1500,
            "tokens": 75000
        },
        "analysis": {
            "executions": 12,
            "avg_latency_ms": 45000,
            "tokens": 50000
        }
    }
}
```

---

### ChatAgent (Direct Access)

For fast responses without analysis tools.

```python
from src.agents.chat_agent import ChatAgent

chat = ChatAgent()

# Simple question answering
response = chat.answer_question(
    question="Explain what ORFs are in genetics",
    conversation_history=[]
)

print(response)
```

---

### ADKCoordinator (Direct Access)

For full analysis with all tools.

```python
from src.agents.adk_coordinator import ADKCoordinator

coordinator = ADKCoordinator()

# Process with tools
result = coordinator.process_message(
    message="ATGAAATAAGCGTAGCTAG",
    session_id="analysis_123"
)

# Run pipeline
result = coordinator.run_pipeline(
    sequence="ATGAAATAAGCGTAGCTAG",
    session_id="analysis_123"
)

# Get metrics
stats = coordinator.get_performance_stats()
```

---

### SessionManager

Manage user sessions directly.

```python
from src.core.session_manager import SessionManager

manager = SessionManager(
    storage_path="my_sessions",
    max_session_age_hours=48
)

# Create session
session = manager.create_session(user_id="researcher_001")
print(session.session_id)

# Get session
session = manager.get_session("session_uuid")

# Get or create
session = manager.get_or_create_session(
    session_id="optional_id",
    user_id="user_123"
)

# Work with session
session.add_message("user", "Analyze this sequence")
session.add_message("assistant", "Analysis shows...")
session.update_context("current_organism", "E. coli")

# Session statistics
stats = manager.get_session_stats()
print(f"Active sessions: {stats['total_sessions']}")
print(f"Total messages: {stats['total_messages']}")

# Cleanup old sessions
manager.cleanup_old_sessions()
```

---

### PerformanceMonitor

Track execution metrics.

```python
from src.core.monitoring import PerformanceMonitor
import time

monitor = PerformanceMonitor(storage_path="my_metrics")

# Track an operation
exec_id = monitor.start_execution("my_agent")

start_time = time.time()
# ... do work ...
end_time = time.time()

monitor.end_execution(
    agent_name="my_agent",
    execution_id=exec_id,
    start_time=start_time,
    tokens_input=500,
    tokens_output=300,
    model="gemini-2.5-flash",
    success=True
)

# Get statistics
stats = monitor.get_summary_stats()
print(f"Total cost: ${stats['total_cost']:.2f}")

# Export metrics
monitor.export_metrics()  # Saves to metrics/
```

---

## Advanced Integration

### Custom Agent Creation

```python
from google.adk.agents import LlmAgent
from src.core.adk_tools import get_all_tools

# Create custom agent
custom_agent = LlmAgent(
    name="my_custom_agent",
    model="gemini-2.5-flash",
    instruction="""You are a specialized bioinformatics analyst.
Focus on:
- Protein structure prediction
- Phylogenetic analysis
- Evolutionary insights
""",
    tools=get_all_tools()
)

# Use with Runner
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.adk.artifacts import InMemoryArtifactService
from google.adk.apps import App

session_service = InMemorySessionService()
memory_service = InMemoryMemoryService()
artifact_service = InMemoryArtifactService()

app = App(
    name="custom_agents",
    root_agent=custom_agent,
    plugins=[]
)

runner = Runner(
    app=app,
    session_service=session_service,
    memory_service=memory_service,
    artifact_service=artifact_service
)
```

### Direct Tool Access

```python
from src.core.adk_tools import (
    analyze_sequence,
    predict_protein_properties,
    search_literature,
    generate_hypotheses
)
import json

# Sequence analysis
result_json = analyze_sequence("ATGAAATAAGCGTAGCTAG")
analysis = json.loads(result_json)
print(f"GC%: {analysis['gc_percent']}")

# Protein prediction
orfs = analysis['orfs']
if orfs:
    orf = orfs[0]
    props_json = predict_protein_properties(
        orf_sequence=orf['sequence']
    )
    properties = json.loads(props_json)
    print(f"MW: {properties['properties']['molecular_weight']} Da")

# Literature search
lit_json = search_literature("GC-rich regions bacteria")
literature = json.loads(lit_json)
print(f"Found {literature['total_results']} papers")

# Generate hypotheses
hyp_json = generate_hypotheses({
    "analysis": analysis,
    "literature": literature
})
hypotheses = json.loads(hyp_json)
for h in hypotheses['hypotheses']:
    print(f"- {h['hypothesis']} ({h['confidence']:.0%})")
```

### Visualization Access

```python
from src.utils.visualizer import VisualizationManager

# Create plots
fig_gc = VisualizationManager.plot_gc_content("ATGAAA...", window_size=100)
fig_orf = VisualizationManager.plot_orf_map(orfs, seq_length)

# Save plots
VisualizationManager.save_plot_image(fig_gc, "gc_plot.png", "plots/")
VisualizationManager.save_plot_image(fig_orf, "orf_map.png", "plots/")

# Display
fig_gc.show()
```

### Report Generation

```python
from src.utils.reporter import create_pdf

report_data = {
    "sequence_analysis": {
        "gc_percent": 42.5,
        "orfs": [...],
        "motifs": [...]
    },
    "sequence_length": 1000,
    "literature": {
        "papers": [...],
        "summary": "..."
    },
    "hypotheses": [...]
}

report_path = create_pdf(
    data=report_data,
    output_dir="reports",
    filename="analysis_report.pdf"
)

print(f"Report saved to: {report_path}")
```

---

## Error Handling

### Exception Types

```python
# API/Service Errors
from google.api_core.exceptions import (
    ResourceExhausted,  # Quota exceeded
    ServiceUnavailable,  # API down
    InvalidArgument     # Bad input
)

# Application Errors
class SequenceValidationError(Exception):
    """Invalid sequence format"""
    pass

class SessionNotFoundError(Exception):
    """Session doesn't exist"""
    pass
```

### Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=1, max=10)
)
def analyze_with_retry(sequence):
    coordinator = UnifiedCoordinator()
    return coordinator.run_pipeline(sequence)

try:
    result = analyze_with_retry("ATGAAA...")
except Exception as e:
    print(f"Failed after retries: {e}")
```

### Error Handling Pattern

```python
def safe_analysis(sequence):
    try:
        coordinator = UnifiedCoordinator()
        result = coordinator.run_pipeline(sequence)
        
        if not result['success']:
            print(f"Analysis failed: {result['error']}")
            return None
        
        return result['results']
    
    except ResourceExhausted:
        print("API quota exceeded. Try again later.")
    except ServiceUnavailable:
        print("API service temporarily unavailable.")
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    return None

results = safe_analysis("ATGAAATAAGCG...")
```

---

## Examples

### Example 1: Simple Chatbot

```python
from src.agents.unified_coordinator import UnifiedCoordinator

def bioinformatics_chatbot():
    coordinator = UnifiedCoordinator()
    session_id = "chatbot_session"
    
    print("🧬 GeneFlow Bioinformatics Bot")
    print("Type 'quit' to exit\n")
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() == 'quit':
            break
        
        if not user_input:
            continue
        
        result = coordinator.process_message(
            message=user_input,
            session_id=session_id
        )
        
        if result['success']:
            print(f"Bot: {result['response']}\n")
        else:
            print(f"Error: {result['error']}\n")

if __name__ == "__main__":
    bioinformatics_chatbot()
```

### Example 2: Batch Sequence Analysis

```python
from src.agents.unified_coordinator import UnifiedCoordinator
import json

def batch_analyze(sequences_file):
    coordinator = UnifiedCoordinator()
    results = []
    
    with open(sequences_file, 'r') as f:
        sequences = json.load(f)  # List of {"id": ..., "seq": ...}
    
    for seq_data in sequences:
        print(f"Analyzing {seq_data['id']}...")
        
        result = coordinator.run_pipeline(
            sequence=seq_data['seq'],
            session_id=f"batch_{seq_data['id']}",
            metadata={"batch": "experiment_001"}
        )
        
        if result['success']:
            results.append({
                "sequence_id": seq_data['id'],
                "analysis": result['results']['analysis'],
                "gc_percent": result['results']['analysis']['gc_percent'],
                "orf_count": len(result['results']['analysis']['orfs']),
                "report_path": result['results']['report']['report_path']
            })
        else:
            results.append({
                "sequence_id": seq_data['id'],
                "error": result['error']
            })
    
    # Save results
    with open("batch_results.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Analyzed {len(sequences)} sequences")
    print(f"Results saved to: batch_results.json")

if __name__ == "__main__":
    batch_analyze("sequences.json")
```

### Example 3: Web API Server

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from src.agents.unified_coordinator import UnifiedCoordinator

app = FastAPI(title="GeneFlow API")
coordinator = UnifiedCoordinator()

class AnalysisRequest(BaseModel):
    sequence: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None

class MessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None

@app.post("/analyze")
async def analyze_sequence(request: AnalysisRequest):
    """Run full sequence analysis pipeline"""
    result = coordinator.run_pipeline(
        sequence=request.sequence,
        session_id=request.session_id,
        user_id=request.user_id
    )
    
    if not result['success']:
        raise HTTPException(status_code=500, detail=result['error'])
    
    return result

@app.post("/chat")
async def chat(request: MessageRequest):
    """Process message through coordinator"""
    result = coordinator.process_message(
        message=request.message,
        session_id=request.session_id,
        user_id=request.user_id
    )
    
    if not result['success']:
        raise HTTPException(status_code=500, detail=result['error'])
    
    return result

@app.get("/stats")
async def get_stats():
    """Get performance statistics"""
    return coordinator.get_performance_stats()

# Run with: uvicorn main:app --reload
```

### Example 4: Comparison Analysis

```python
from src.core.adk_tools import compare_sequences
import json

def compare_two_sequences(seq1_file, seq2_file):
    # Read sequences
    with open(seq1_file) as f:
        seq1 = f.read().strip()
    with open(seq2_file) as f:
        seq2 = f.read().strip()
    
    print(f"Sequence 1: {len(seq1)} bp")
    print(f"Sequence 2: {len(seq2)} bp")
    
    # Compare
    result_json = compare_sequences(seq1, seq2)
    result = json.loads(result_json)
    
    print(f"\nComparison Results:")
    print(f"Similarity: {result['similarity_score']:.1f}%")
    print(f"Identity: {result['identity_percent']:.1f}%")
    print(f"Homology: {result['homology_prediction']}")
    
    # Print alignment
    print(f"\nAlignment:")
    print(f"Query:  {result['alignment']['query']}")
    print(f"Match:  {result['alignment']['match']}")
    print(f"Target: {result['alignment']['target']}")

if __name__ == "__main__":
    compare_two_sequences("seq1.fasta", "seq2.fasta")
```

---

## Best Practices

1. **Reuse Coordinator Instances**
   ```python
   # Good: Single instance
   coordinator = UnifiedCoordinator()
   for seq in sequences:
       coordinator.run_pipeline(seq)
   
   # Bad: Creating new instance each time
   for seq in sequences:
       coordinator = UnifiedCoordinator()  # Inefficient
   ```

2. **Use Session IDs for Context**
   ```python
   # Good: Related messages in same session
   result1 = coordinator.process_message("Intro", session_id="user1")
   result2 = coordinator.process_message("Analyze X", session_id="user1")
   
   # Bad: New session each time
   result1 = coordinator.process_message("Intro")  # New session
   result2 = coordinator.process_message("Analyze X")  # Different session
   ```

3. **Handle Errors Gracefully**
   ```python
   result = coordinator.run_pipeline(sequence)
   if result['success']:
       use_results(result['results'])
   else:
       log_error(result['error'])
       notify_user("Analysis failed")
   ```

4. **Monitor Performance**
   ```python
   stats = coordinator.get_performance_stats()
   if stats['avg_latency_ms'] > 60000:
       log_warning("Slow responses detected")
   ```

5. **Clean Up Sessions**
   ```python
   # Periodically
   session_manager.cleanup_old_sessions()
   performance_monitor.export_metrics()
   ```

---

**Last Updated**: November 2024
**Version**: 1.0.0
