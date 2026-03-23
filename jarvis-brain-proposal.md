# Proposal: JARVIS Brain - Persistent Memory System

> **Transformando J.A.R.V.I.S. en un asistente que recuerda, anticipa y aprende como el JARVIS real de Iron Man.**

---

## Executive Summary

El JARVIS actual es stateless - cada sesión empieza desde cero. Este proposal introduce un **"cerebro" de memoria persistente** que:

- **Recuerda** todas las conversaciones, decisiones y contexto de trabajo
- **Anticipa** necesidades basándose en patrones aprendidos
- **Mejora** continuamente el flujo de trabajo usando experiencia pasada
- **Responde** con latencia <50ms gracias a procesamiento local

La innovación central es el **Predictive Memory Pre-fetching**: JARVIS observa transiciones de contexto y pre-carga memorias relevantes antes de que el usuario las pida - exactamente como el JARVIS de Iron Man.

---

## Three-Layer Memory Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           J.A.R.V.I.S. BRAIN                        │
├─────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  LAYER 1: WORKING MEMORY (RAM-like, 0ms latency)            │  │
│  │  ─────────────────────────────────────────────────────────── │  │
│  │  • Current session context                                  │  │
│  │  • Active tasks & goals                                     │  │
│  │  • Last N interactions (sliding window)                     │  │
│  │  • In-process Python dict - zero network latency            │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              ↕ Sync on context change                │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  LAYER 2: EPISODIC MEMORY (ChromaDB, <5ms latency)         │  │
│  │  ─────────────────────────────────────────────────────────── │  │
│  │  • Conversation history (vector embeddings)                 │  │
│  │  • Session summaries                                        │  │
│  │  • Decisions & commitments made                             │  │
│  │  • User statements & facts mentioned                        │  │
│  │  • HNSW index for semantic similarity search               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              ↕ Background consolidation               │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  LAYER 3: SEMANTIC MEMORY (Knowledge Graph, <10ms)         │  │
│  │  ─────────────────────────────────────────────────────────── │  │
│  │  • Extracted facts & knowledge                             │  │
│  │  • User preferences & communication style                   │  │
│  │  • Project context, architecture decisions                  │  │
│  │  • Learned patterns (git workflow, error handling, etc.)   │  │
│  │  • NetworkX graph + SQLite for fast traversal              │  │
│  └───────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────┤
│                    MEMORY CONSOLIDATION ENGINE                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  Runs in background (never blocks voice interaction)         │  │
│  │  • Auto-summarization of sessions                          │  │
│  │  • Importance scoring (recency × relevance)                │  │
│  │  • Intelligent decay & archival of old memories            │  │
│  │  • Cross-session pattern detection                         │  │
│  │  • Conflict resolution for contradictory facts              │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Near-Zero Latency Strategy

### Innovation 1: Predictive Memory Pre-fetching

La innovación central que hace a JARVIS anticipar en lugar de solo recordar:

```python
class PredictiveMemory:
    """
    JARVIS watches context transitions and pre-loads likely memories.
    Like real JARVIS anticipating Tony Stark's needs.
    
    This runs ASYNC and never blocks voice interaction.
    """
    
    def on_context_change(self, old_ctx, new_ctx):
        """Called when user context changes - triggers pre-fetch"""
        
        # When user enters a new directory → pre-fetch project context
        if new_ctx.directory != old_ctx.directory:
            self.prefetch_project_memory(new_ctx.directory)
        
        # When user mentions specific files → pre-fetch file history
        if new_ctx.mentioned_files:
            self.prefetch_file_memories(new_ctx.mentioned_files)
        
        # When user encounters errors → pre-fetch similar past issues
        if new_ctx.has_errors:
            self.prefetch_error_context(new_ctx.errors)
        
        # When user asks about a concept → pre-fetch related discussions
        if new_ctx.topics:
            self.prefetch_topic_history(new_ctx.topics)
```

### Innovation 2: Voice-Optimized Retrieval Pipeline

```
User Speaks → VAD detects intent → INTENT analysis (fast LLM)
                                          ↓
                              Predictive memory lookup (pre-fetched)
                                          ↓
                              Relevant context merge (already ready)
                                          ↓
                              LLM responds with memory INJECTED
                                          ↓
                              TTS speaks (memory seamlessly integrated)
                                          ↓
                              [Meanwhile: background consolidation runs]
```

**Latency Budget:**
| Stage | Latency | Notes |
|-------|---------|-------|
| Intent detection | 20ms | Fast local model |
| Memory retrieval | **5ms** | Local ChromaDB |
| Context merge | 10ms | Pre-computed |
| **Total overhead** | **<35ms** | Imperceptible to humans |

### Innovation 3: Memory Compression Pipeline

```python
class MemoryConsolidation:
    """
    Background process that runs WHILE JARVIS is speaking.
    Never blocks voice interaction - async all the way.
    """
    
    # Triggers: every 5 minutes OR end of session
    async def consolidate(self, session_id):
        # 1. Summarize recent conversation → Episodic memory
        summary = await self.summarize_session(session_id)
        await self.store_episodic(summary)
        
        # 2. Extract facts → Semantic memory
        facts = await self.extract_facts(session_id)
        await self.update_knowledge_graph(facts)
        
        # 3. Score importance → Prune low-value memories
        await self.score_and_prune()
        
        # 4. Detect patterns → Update user model
        await self.detect_patterns()
        
        # 5. Update embeddings (incremental, not full re-index)
        await self.update_embeddings()
```

---

## JARVIS Personality Integration

### Memory-Enabled Behaviors

| Behavior | Without Memory | With JARVIS Brain |
|----------|---------------|-------------------|
| User mentions "fix that bug" | "Which bug?" | "You mean the null pointer in auth.py? I have the full context from yesterday." |
| User returns after days | "Hello, how can I help?" | "Welcome back. Last session we were debugging the API endpoint timeout." |
| User encounters an error | Generic help message | "This error signature matches one from last week. The fix was..." |
| User asks about code | Generic explanation | "This is the module we built together last Tuesday. The key pattern was..." |
| User starts new task | Empty context | "This reminds me of the project from March. The same architecture applies." |

### Learned User Profile

```yaml
user_profile:
  # Learned from interaction patterns
  communication_style: concise  # User prefers brief responses
  technical_level: advanced    # User uses technical terms naturally
  prefers_drafts: true         # User always asks for draft before implementation
  debug_level: detailed        # User wants full stack traces
  
  # Learned project patterns
  project_patterns:
    - type: git_workflow
      learned: "User always commits before major changes"
      confidence: 0.95
    - type: error_handling
      learned: "User prefers detailed error analysis over quick fixes"
      confidence: 0.88
    - type: code_review
      learned: "User asks for test coverage before merging"
      confidence: 0.92
  
  # Context tracking
  current_project:
    name: "gemini-extension"
    last_session: "2024-01-15"
    active_tasks: ["voice recognition optimization", "memory system"]
  
  # Relationship memory
  interactions:
    total_sessions: 47
    total_hours: 23.5
    topics_discussed: ["Python async", "Vector databases", "TTS optimization"]
```

---

## Technical Stack

| Component | Technology | Why | Latency |
|-----------|------------|-----|---------|
| **Vector DB** | ChromaDB (local) | 0ms network latency, embedded Python | <5ms |
| **Embeddings** | sentence-transformers (all-MiniLM-L6-v2) | Fast (CPU), good quality, 384 dimensions | <10ms |
| **Knowledge Graph** | NetworkX + SQLite | Fast traversal, ACID persistence | <10ms |
| **Working Memory** | In-memory Python dict | Zero latency for hot data | 0ms |
| **Session Store** | SQLite | Persistent, reliable, SQL queries | <5ms |
| **Background Processing** | asyncio | Non-blocking consolidation | async |
| **Intent Detection** | DistilBERT or fast local model | Sub-20ms classification | <20ms |

### Why ChromaDB over alternatives?

| Database | Latency | Pros | Cons |
|----------|---------|------|------|
| **ChromaDB** ✓ | 0ms (local) | Embedded, zero config, Python-native | Less scalable (>10M vectors) |
| Qdrant | <10ms | Rust performance, robust | Requires Docker/service |
| Weaviate | <50ms | Hybrid search built-in | More complex setup |
| Pinecone | <100ms | Managed, scalable | Network latency, cloud-only |
| pgvector | <20ms | If Postgres already used | Adds DB dependency |

**For JARVIS use case**: ChromaDB is ideal because:
1. Personal/local use (not enterprise scale)
2. Zero network latency (critical for voice)
3. Simple Python API
4. Runs entirely locally (privacy)

---

## File Structure

```
jarvis-brain/
├── __init__.py
├── config.py                 # Brain configuration
├── memory/
│   ├── __init__.py
│   ├── base.py              # Abstract memory interface
│   ├── working.py           # Layer 1: Working memory
│   ├── episodic.py          # Layer 2: ChromaDB episodic
│   ├── semantic.py          # Layer 3: Knowledge graph
│   └── consolidation.py     # Background consolidation
├── retrieval/
│   ├── __init__.py
│   ├── search.py            # Vector search wrapper
│   ├── predictive.py        # Pre-fetching engine
│   └── merger.py            # Context merge logic
├── learning/
│   ├── __init__.py
│   ├── profile.py           # User profile learning
│   ├── patterns.py          # Pattern detection
│   └── summarizer.py        # Session summarization
├── api/
│   ├── __init__.py
│   └── brain.py             # Brain API for JARVIS core
└── utils/
    ├── __init__.py
    ├── embeddings.py        # Embedding utilities
    └── metrics.py           # Latency/performance tracking
```

---

## Implementation Phases

### Phase 1: Core Memory (Week 1) 🔧
**Goal**: Basic memory persistence with semantic search

- [ ] ChromaDB integration with local persistence (`~/.jarvis/memory/`)
- [ ] Conversation storage pipeline (every user/assistant exchange)
- [ ] Basic semantic search of past conversations
- [ ] Working memory for current session context
- [ ] Simple session summaries

**Deliverable**: `jarvis recall "what were we working on yesterday?"` works

### Phase 2: Intelligence (Week 2) 🧠
**Goal**: Smart memory consolidation and importance scoring

- [ ] Memory consolidation engine (async background)
- [ ] Importance scoring algorithm (recency × relevance × user feedback)
- [ ] Session summarization with LLM
- [ ] Cross-session pattern detection
- [ ] Memory pruning (keep important, archive old)

**Deliverable**: JARVIS starts learning user preferences automatically

### Phase 3: Proactivity (Week 3) ⚡
**Goal**: Predictive pre-fetching and proactive suggestions

- [ ] Predictive pre-fetching engine
- [ ] Context-aware response enhancement
- [ ] User preference learning (communication style, technical level)
- [ ] Memory-based suggestions before user asks
- [ ] Integration with JARVIS core loop

**Deliverable**: JARVIS anticipates needs like real JARVIS

### Phase 4: Optimization & Polish (Week 4) 🎯
**Goal**: Production-ready performance

- [ ] Latency profiling and optimization
- [ ] Memory usage monitoring
- [ ] Disk usage management (archival system)
- [ ] Error recovery and consistency checks
- [ ] User testing and feedback loop
- [ ] Documentation

**Deliverable**: Release-ready, battle-tested system

---

## API Design

### Brain API

```python
from jarvis_brain import JARVISBrain

# Initialize (loads all layers)
brain = JARVISBrain()

# Store a conversation turn
await brain.remember(
    role="user",  # or "assistant"
    content="We're building a new API endpoint for user authentication",
    context={
        "directory": "/project/src/api",
        "files": ["auth.py", "models.py"],
        "intent": "implementation"
    }
)

# Retrieve relevant memories
memories = await brain.recall(
    query="authentication endpoints we discussed",
    limit=5,
    recency_weight=0.3  # Balance recent vs relevant
)

# Get current session context
context = brain.get_context()

# Proactive suggestions (called periodically)
suggestions = await brain.suggest()

# Session management
await brain.end_session()  # Triggers consolidation
```

### Voice Integration

```python
# In main.py - integrate with existing TTS pipeline
async def process_jarvis_response(text: str, is_code: bool):
    # Store the response
    await brain.remember(role="assistant", content=text)
    
    # Get relevant context for next turn
    memories = await brain.recall(context=user_query)
    
    # Inject into prompt
    enhanced_prompt = memories.inject(system_prompt)
    
    # Continue pipeline...
```

---

## Metrics & Success Criteria

### Performance Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Memory retrieval latency | <10ms p95 | `metrics.recall_latency` |
| Pre-fetch accuracy | >80% | Cache hit rate on pre-fetched memories |
| Consolidation overhead | 0ms (async) | No impact on voice interaction |
| Memory size growth | <10MB/week | Disk usage monitoring |

### Functional Metrics

| Metric | Target | Verification |
|--------|--------|--------------|
| Cross-session recall | 100% | Test asking about past sessions |
| User profile accuracy | >85% | Manual verification of learned preferences |
| Pattern detection | >3 patterns | Weekly pattern report |
| Context injection success | >90% | LLM responses reference memory |

### User Experience Metrics

- [ ] User says "you remember that?" - JARVIS does
- [ ] User surprised by relevant memory recall
- [ ] Response latency unchanged (still feels instant)
- [ ] Memory feels "magical" - anticipatory not just reactive

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Memory bloat (size grows unbounded) | Medium | Medium | Aggressive pruning, importance scoring, archival |
| Embedding latency adds to response | Low | Medium | Pre-compute embeddings, fast model (MiniLM) |
| Memory pollution (irrelevant context) | Medium | Medium | Relevance filtering, importance threshold |
| Hallucinated memories (LLM summarization) | Low | High | Verify summaries, human-in-loop for critical facts |
| Privacy concerns | Low | High | All data local, user controls retention period |
| Context injection degrades quality | Medium | Medium | A/B testing, user feedback loop |
| Disk corruption/loss | Low | High | SQLite WAL mode, regular backups |

### Rollback Plan

1. **Disable brain module** via config flag (`brain.enabled: false`)
2. **JARVIS reverts** to stateless mode seamlessly
3. **Memory data preserved** in `~/.jarvis/memory/` for future re-enablement
4. **ChromaDB and SQLite** files remain for data recovery
5. **No data loss** - user can re-enable and continue

---

## Future Extensions

### v2.0 (Post-launch)
- **Multi-user support**: Isolated memory per user/project
- **Cloud sync**: Optional encrypted backup to user's cloud
- **Cross-device**: Sync memories across machines
- **Multimodal memory**: Remember screenshots, diagrams, files

### v3.0 (Advanced)
- **Video memory**: Remember screen recordings, demos
- **Collaboration memory**: Shared team context
- **Learning mode**: Explicit user feedback for better learning

---

## Conclusion

This is NOT just adding a vector database. This is building a **cognitive memory system** that:

1. **Anticipates** rather than just recalls
2. **Learns** user patterns and preferences
3. **Consolidates** while idle (never blocks interaction)
4. **Forgets strategically** (like human memory)
5. **Feels alive** (JARVIS that truly knows you)

The key innovation is the **Predictive Memory Pre-fetching** combined with local ChromaDB for sub-5ms retrieval. This creates the JARVIS experience - an assistant that always seems to know what you need before you ask.

---

## Status

| Phase | Status |
|-------|--------|
| Proposal | ✅ Complete |
| Specs | ⏳ Pending |
| Design | ⏳ Pending |
| Implementation | ⏳ Pending |
| Testing | ⏳ Pending |

---

**Complexity**: Medium-High  
**Estimated Timeline**: 4 weeks  
**Risk Level**: Medium (manageable with phased rollout)  
**Dependencies**: ChromaDB, sentence-transformers, NetworkX  
**Privacy**: 100% local, no cloud dependencies
