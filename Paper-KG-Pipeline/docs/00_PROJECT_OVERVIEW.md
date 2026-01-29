# Idea2Paper Project Summary Document
[English](00_PROJECT_OVERVIEW.md) | [简体中文](00_PROJECT_OVERVIEW_zh.md)

## 📋 Project Overview

**Project Name**: Idea2Paper - Automated Academic Paper Generation System Based on Knowledge Graph

**Core Goal**: Automatically transform a user's research **Idea** into a submission-ready paper **Story** (Narrative Skeleton) that meets top-tier conference (ICLR) standards.

**Tech Stack**:

* Knowledge Graph: NetworkX
* Vector Retrieval: Embedding (Qwen3-Embedding-4B)
* Large Language Models: Qwen3-14B, Qwen2.5-7B-Instruct
* Data Source: ICLR 2025 Paper Dataset (8,285 papers)

---
# Table of Contents

- [Idea2Paper Project Summary Document](#idea2paper-project-summary-document)
  - [1. System Architecture](#1-system-architecture)
  - [2. Knowledge Graph Construction](#2-knowledge-graph-construction)
  - [3. Three-Way Retrieval System](#3-three-way-retrieval-system)
  - [4. Idea2Story Pipeline](#4-idea2story-pipeline)
  - [5. Configuration Overview](#5-configuration-overview)
  - [6. Complete Workflow](#6-complete-workflow)
  - [7. Core Innovations](#7-core-innovations)
  - [8. System Advantages](#8-system-advantages)
  - [9. Current Limitations & Future Directions](#9-current-limitations--future-directions)
  - [10. Documentation Index](#10-documentation-index)
  - [11. Code Structure](#11-code-structure)
  - [12. Key Metrics](#12-key-metrics)
  - [13. Usage Recommendations](#13-usage-recommendations)
  - [14. Troubleshooting](#14-troubleshooting)
  - [15. Summary](#15-summary)
  - [16. Acknowledgements](#16-acknowledgements)


## 1. System Architecture

### 1.1 Overall Flowchart

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       Idea2Paper Complete Workflow                      │
└─────────────────────────────────────────────────────────────────────────┘

User Input Idea
    │
    ├──────────────────────────────────────────────────────────────────────┐
    │                 Phase 1: Knowledge Graph Construction                │
    │                (One-time build, reusable subsequently)               │
    ├──────────────────────────────────────────────────────────────────────┤
    │                                                                      │
    │  1. Load ICLR Paper Data (8,285 papers)                              │
    │      ↓                                                               │
    │  2. Construct 4 Types of Nodes                                       │
    │      ├─ Idea Nodes (8,284)                                           │
    │      ├─ Pattern Nodes (124, LLM-Enhanced)                            │
    │      ├─ Domain Nodes (98)                                            │
    │      └─ Paper Nodes (8,285)                                          │
    │      ↓                                                               │
    │  3. Construct Edge Relations (444,872 edges)                         │
    │      ├─ Basic Connection Edges (Paper→Idea/Pattern/Domain)           │
    │      └─ Retrieval Auxiliary Edges (Idea→Domain, Pattern→Domain)      │
    │      ↓                                                               │
    │  4. Output Knowledge Graph                                           │
    │                                                                      │
    └──────────────────────────────────────────────────────────────────────┘
    │
    ├──────────────────────────────────────────────────────────────────────┐
    │                      Phase 2: Three-Way Retrieval                    │
    │                         (Per run, approx. 27s)                       │
    ├──────────────────────────────────────────────────────────────────────┤
    │                                                                      │
    │  ┌─────────────┬─────────────┬─────────────┐                         │
    │  │   Path 1    │   Path 2    │   Path 3    │                         │
    │  │ Similar Idea│ Domain Rel. │Similar Paper│                         │
    │  │ (Weight 0.4)│ (Weight 0.2)│ (Weight 0.4)│                         │
    │  └─────────────┴─────────────┴─────────────┘                         │
    │       │              │              │                                │
    │       │              │              │                                │
    │  Coarse: Jaccard Match Domain  Coarse: Jaccard                       │
    │  Top-100         Top-5         Top-100                               │
    │       ↓              ↓              ↓                                │
    │  Fine: Embedding Find Pattern  Fine: Embedding                       │
    │  Top-10          works_well    Top-20                                │
    │       ↓              ↓              ↓                                │
    │  Get Pattern     Get Pattern   Get Pattern                           │
    │  Score           Score         Score                                 │
    │       │              │              │                                │
    │       └──────────────┴──────────────┘                                │
    │                      ↓                                               │
    │             Weighted Fusion & Fine Ranking                           │
    │                      ↓                                               │
    │              Top-10 Patterns                                         │
    │                                                                      │
    └──────────────────────────────────────────────────────────────────────┘
    │
    ├──────────────────────────────────────────────────────────────────────┐
    │                Phase 3: Story Generation & Refinemen                 │
    │                      (3-10 minutes)                                  │
    ├──────────────────────────────────────────────────────────────────────┤
    │                                                                      │
    │  1. Multi-dimensional Pattern Classification                         │
    │      ├─ Stability                                                    │
    │      ├─ Novelty                                                      │
    │      └─ Cross-Domain                                                 │
    │      ↓                                                               │
    │  2. Select Initial Pattern → Generate Draft Story                    │
    │      ↓                                                               │
    │  3. Multi-Agent Critic Review (Methodology/Novelty/Storyteller)      │
    │      ↓                                                               │
    │  4. Decision: Score >= 7.0?                                          │
    │      ├─[Yes]→ Proceed to Phase 4                                     │
    │      └─[No] → Intelligent Refinement                                 │
    │                 │                                                    │
    │                 ├─ Novelty Stagnated? → [Novelty Mode]               │
    │                 │   ├─ Traverse Novelty Patterns                     │
    │                 │   ├─ Idea Fusion                                   │
    │                 │   ├─ Story Reflection (Quality Assessment)         │
    │                 │   ├─ Regenerate Story                              │
    │                 │   ├─ Critic Review                                 │
    │                 │   ├─ Score Dropped? → Rollback                     │
    │                 │   └─ Fallback: Select Highest Score Version        │
    │                 │                                                    │
    │                 └─ Ordinary Refinement → Inject Complementary Tricks │
    │                     ├─ Lacks Novelty → Tail Injection (Rank 5-10)    │
    │                     ├─ Lacks Stability → Head Injection (Rank 1-3)   │
    │                     └─ Return to Step 2                              │
    │                                                                      │
    └──────────────────────────────────────────────────────────────────────┘
    │
    ├──────────────────────────────────────────────────────────────────────┐
    │                    Phase 4: RAG Novelty Verification                 │
    │                            (Approx. 30s)                             │
    ├──────────────────────────────────────────────────────────────────────┤
    │                                                                      │
    │  1. Extract Key Methods → Retrieve Papers from Top Confs (Last 3 Yrs)│
    │      ↓                                                               │
    │  2. Decision: Similarity > 0.75?                                     │
    │      ├─[No] → Output Final Story                                     │
    │      └─[Yes]→ Collision! Pivot Avoidance                             │
    │                 ├─ Analyze Collision Points                          │
    │                 ├─ Generate Constraints (Disable Tech/Domain Shift)  │
    │                 └─ Return to Phase 3, Step 2                         │
    │                                                                      │
    └──────────────────────────────────────────────────────────────────────┘
    │
    ▼
Output Final Story (JSON format)

```

**Workflow Explanation**:

* **Phase 1**: Offline construction, run only once.
* **Phase 2**: Real-time retrieval, 13x speedup (27 seconds).
* **Phase 3**: Core generation, intelligent refinement mechanism.
* **Phase 4**: Deduplication/Novelty verification to avoid collision.

### 1.2 Core Modules

| Layer | Module | File/Script | Function |
| --- | --- | --- | --- |
| **Data Layer** | Knowledge Graph Construction | `build_entity_v3.py`, `build_edges.py` | Construct nodes and edges |
| **Retrieval Layer** | Three-Way Retrieval System | `recall_system.py` | Retrieve relevant Patterns |
| **Generation Layer** | Pattern Selection | `pattern_selector.py` | Multi-dimensional Pattern classification |
| **Generation Layer** | Idea Fusion | `planner.py` | Fuse innovative Ideas |
| **Generation Layer** | Story Generation | `story_generator.py` | Generate Paper Story |
| **Generation Layer** | Story Reflection | `story_reflector.py` | Assess fusion quality |
| **Generation Layer** | Critic Review | `critic.py` | Multi-agent review |
| **Generation Layer** | Intelligent Refinement | `refinement.py` | Iterative optimization |
| **Generation Layer** | RAG Verification | `verifier.py` | Deduplication and avoidance |
| **Orchestration Layer** | Pipeline Management | `manager.py`, `idea2story_pipeline.py` | Workflow orchestration |

---

## 2. Knowledge Graph Construction

### 2.1 Data Scale

```
Knowledge Graph Statistics:
├─ Total Nodes: 16,791
│  ├─ Idea:    8,284 (100% coverage)
│  ├─ Pattern: 124 (Generated via clustering)
│  ├─ Domain:  98 (Generated via aggregation)
│  └─ Paper:   8,285
└─ Total Edges:   444,872
   ├─ Basic Connection Edges: ~25,000
   └─ Retrieval Auxiliary Edges: ~420,000

```

### 2.2 Node Definitions

**Idea Node**: The core innovation of the paper

```json
{
  "idea_id": "idea_0",
  "description": "Core idea description...",
  "base_problem": "Base problem...",
  "solution_pattern": "Solution pattern...",
  "pattern_ids": ["pattern_9", ...]
}
```

**Pattern Node**: Writing trope/Method unit template

```json
{
  "pattern_id": "pattern_24",
  "name": "Reframing Graph Learning Scalability",
  "size": 331,
  "llm_enhanced_summary": {
    "representative_ideas": "Inductive summary...",
    "common_tricks": ["Trick 1", "Trick 2"]
  }
}
```

**Domain Node**: Research domain

```json
{
  "domain_id": "domain_0",
  "name": "Natural Language Processing",
  "paper_count": 1076,
  "sub_domains": ["Text Classification", ...]
}
```

**Paper Node**: Concrete paper

```json
{
  "paper_id": "RUzSobdYy0V",
  "title": "Quantifying and Mitigating...",
  "domain": "Fairness & Accountability",
  "idea": "Core idea...",
  "pattern_id": "pattern_9"
}
```

### 2.3 Edge Definitions

**Basic Connection Edges**:

* `Paper → Idea` (implements): The paper implements this Idea.
* `Paper → Pattern` (uses_pattern): The paper uses this Pattern.
* `Paper → Domain` (in_domain): The paper belongs to this Domain.

**Retrieval Auxiliary Edges**:

* `Idea → Domain` (belongs_to): Domain the Idea belongs to, weight = proportion.
* `Pattern → Domain` (works_well_in): Effectiveness of Pattern in this Domain, weight = effectiveness.
* `Idea → Paper` (similar_to_paper): Similarity weight (calculated in real-time in Path 3).

### 2.4 Execution Method

```bash
# 1. Build Nodes
python scripts/build_entity_v3.py
# Output: output/nodes_*.json (4 files)

# 2. Build Edges
python scripts/build_edges.py
# Output: output/edges.json, output/knowledge_graph_v2.gpickle
```

**Execution Time**: Node construction 15 minutes (including LLM enhancement) + Edge construction 3 minutes.

---

## 3. Three-Way Retrieval System

### 3.1 Retrieval Strategy

| Path | Matching Object | Capture Dimension | Weight | Retrieval Count |
| --- | --- | --- | --- | --- |
| **Path 1** | Idea Description | Core idea similarity | 0.4 | Top-10 Pattern |
| **Path 2** | Domain & Sub-domains | Domain generalization | 0.2 | Top-5 Pattern |
| **Path 3** | Paper Title | Research theme similarity | 0.4 | Top-10 Pattern |

### 3.2 Two-Stage Retrieval Optimization

**Performance Comparison**:

```
Full Embedding: ~7 minutes (8,284 API calls)
Two-Stage Retrieval: ~27 seconds (100 API calls)
Speedup Ratio: 13x
```

**Process**:

```
Coarse Ranking: Jaccard fast filtering Top-100 (Milliseconds)
    ↓
Fine Ranking: Embedding precise sorting Top-10/20 (~27 seconds)
```

### 3.3 Similarity Calculation

**Jaccard Similarity** (Coarse Ranking):

```python
Jaccard(A, B) = |A ∩ B| / |A ∪ B|
```

**Embedding Similarity** (Fine Ranking):

```python
Cosine(A, B) = dot(emb_A, emb_B) / (norm(emb_A) * norm(emb_B))
```

### 3.4 Execution Method

```bash
# Run independently
python scripts/simple_recall_demo.py "Your Research Idea"

# Use as a class
from recall_system import RecallSystem
system = RecallSystem()
results = system.recall(user_idea, verbose=True)

```

**Output**: List of Top-10 Patterns, each containing (pattern_id, pattern_info, score).

---

## 4. Idea2Story Pipeline

### 4.1 Core Mechanisms

#### (1) Multi-dimensional Pattern Classification

**Goal**: Ensure Pattern diversity.

**Dimensions**:

* **Stability**: Rank Top-3 + Cluster Size ≥ 15.
* **Novelty**: Cluster Size < 10.
* **Cross-Domain**: From Path 2/3 + Different Domain.

#### (2) Idea Fusion

**Goal**: Organic fusion at the conceptual level, not just technical stacking.

**Process**:

```
Original Idea + New Pattern → LLM Generated Fused Idea
    ↓
Fused Idea contains:
  - fused_core_idea: Core idea after fusion
  - conceptual_bridge: Conceptual bridge
  - reframed_problem: Reframed problem
  - innovation_angle: Unique innovation angle
```

**Example**:

```
Original Idea: Use LLM for data augmentation
New Pattern: Curriculum Learning
Fused Idea: Difficulty-adaptive curriculum learning framework generated based on LLM
```

#### (3) Story Reflection

**Goal**: Assess fusion quality and ensure conceptual unity.

**Scoring**:

```
fusion_quality = 0.4 × Coherence + 0.4 × Fusion Richness + 0.2 × Fusion Idea Reward
```

**Threshold**: `fusion_quality >= 0.65` is considered a successful fusion.

#### (4) Multi-Agent Critic Review

**Roles**:

* **Reviewer A** (Methodology): Technical soundness.
* **Reviewer B** (Novelty): Innovation.
* **Reviewer C** (Storyteller): Narrative completeness.

**Pass Standard**: Average Score >= 7.0.

#### (5) Intelligent Refinement

**Novelty Mode**:

* **Trigger**: Novelty score stagnation (≤ Previous Round + 0.5).
* **Process**: Traverse all Novelty Patterns, each undergoing Fusion → Reflection → Generation → Critic.
* **Fallback**: Select the version with the highest score.

**Score Degradation Rollback**:

* **Trigger**: Any dimension score drops > 0.1.
* **Process**: Restore Story + Mark failure + Delete Tricks + Continue iteration.

**Ordinary Refinement**:

* **Tail Injection**: Lacks novelty → Inject unpopular Patterns (Rank 5-10).
* **Head Injection**: Lacks stability → Inject mature Patterns (Rank 1-3).

#### (6) RAG Novelty Verification & Avoidance

**Verification**: Retrieve top conference papers from the last 3 years; Similarity > 0.75 is considered a collision.

**Avoidance**: Pivot strategy to generate constraints (Domain shift, setting limitations, etc.), then regenerate Story.

### 4.2 Execution Method

```bash
python scripts/idea2story_pipeline.py "Your Research Idea"
```

**Output**:

```
output/
├── final_story.json          # Final Paper Story
├── pipeline_result.json      # Complete Pipeline Result
└── log.json                  # Detailed Log
```

**Execution Time**: 3-10 minutes (depending on iteration count).

---

## 5. Configuration Overview

### 5.1 Knowledge Graph Construction

```python
# scripts/build_entity_v3.py

# Data source paths
DATA_DIR = PROJECT_ROOT / "data" / "ICLR_25"
ASSIGNMENTS_FILE = DATA_DIR / "assignments.jsonl"
CLUSTER_LIBRARY_FILE = DATA_DIR / "cluster_library_sorted.jsonl"
PATTERN_DETAILS_FILE = DATA_DIR / "iclr_patterns_full.jsonl"

# LLM API Config
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY")
LLM_API_URL = "https://api.siliconflow.cn/v1/chat/completions"
LLM_MODEL = "Qwen/Qwen2.5-7B-Instruct"
```

### 5.2 Retrieval System

```python
# scripts/recall_system.py

class RecallConfig:
    # Path Weights
    PATH1_WEIGHT = 0.4  # Similar Idea
    PATH2_WEIGHT = 0.2  # Domain Relevance
    PATH3_WEIGHT = 0.4  # Similar Paper

    # Retrieval Counts
    PATH1_TOP_K_IDEAS = 10
    PATH1_FINAL_TOP_K = 10
    PATH2_TOP_K_DOMAINS = 5
    PATH2_FINAL_TOP_K = 5
    PATH3_TOP_K_PAPERS = 20
    PATH3_FINAL_TOP_K = 10
    FINAL_TOP_K = 10

    # Two-Stage Retrieval
    USE_EMBEDDING = True
    TWO_STAGE_RECALL = True
    COARSE_RECALL_SIZE = 100
    FINE_RECALL_SIZE = 20
```

### 5.3 Pipeline

```python
# scripts/pipeline/config.py

class PipelineConfig:
    # Pattern Selection
    SELECT_PATTERN_COUNT = 3
    CONSERVATIVE_RANK_RANGE = (0, 2)
    INNOVATIVE_CLUSTER_SIZE_THRESHOLD = 10

    # Critic Threshold
    PASS_SCORE = 7.0
    MAX_REFINE_ITERATIONS = 3

    # Novelty Mode
    NOVELTY_MODE_MAX_PATTERNS = 10
    NOVELTY_SCORE_THRESHOLD = 6.0
    NOVELTY_STAGNATION_DELTA = 0.5

    # Reflection
    FUSION_QUALITY_THRESHOLD = 0.65

    # Rollback
    SCORE_DEGRADATION_THRESHOLD = 0.1

    # RAG Verification
    COLLISION_THRESHOLD = 0.75

    # Refinement Strategy
    TAIL_INJECTION_RANK_RANGE = (4, 9)
    HEAD_INJECTION_RANK_RANGE = (0, 2)
    HEAD_INJECTION_CLUSTER_THRESHOLD = 15

# LLM Config
LLM_API_KEY = os.getenv("SILICONFLOW_API_KEY")
LLM_API_URL = "https://api.siliconflow.cn/v1/chat/completions"
LLM_MODEL = "Qwen/Qwen3-14B"
```

---

## 6. Complete Workflow

### 6.1 Environment Setup

```bash
# 1. Clone Project
cd /Users/gaoge/code/mycode/Idea2Paper/Paper-KG-Pipeline

# 2. Install Dependencies
pip install -r requirements.txt

# 3. Set Environment Variable
export SILICONFLOW_API_KEY="your_api_key_here"
```

### 6.2 One-Time Build

```bash
# Build Knowledge Graph (Run only once)
python scripts/build_entity_v3.py   # 15 minutes
python scripts/build_edges.py       # 3 minutes
```

### 6.3 Use Pipeline

```bash
# Generate Paper Story
python scripts/idea2story_pipeline.py "Your Research Idea Description"

# Example
python scripts/idea2story_pipeline.py "Optimizing Large Model Inference Efficiency with Reinforcement Learning"
```

### 6.4 View Results

```bash
# View Final Story
cat output/final_story.json

# View Complete Pipeline
cat output/pipeline_result.json

# View Detailed Log
cat output/log.json | jq '.'
```

---

## 7. Core Innovations

### 7.1 Knowledge Graph Level

✅ **LLM-Enhanced Pattern**: Generate inductive summaries for each Pattern cluster.<br>
✅ **Dual-Layer Description**: Concrete examples + Global summary, enabling both learning and understanding.<br>
✅ **Quality-Oriented Edge Weights**: Calculate edge weights based on paper quality and Pattern effectiveness.<br>

### 7.2 Retrieval Level

✅ **Three-Way Complementary Retrieval**: Capture relevance from Idea, Domain, and Paper dimensions.<br>
✅ **Two-Stage Optimization**: Jaccard coarse ranking + Embedding fine ranking, 13x speedup.<br>
✅ **Real-Time Path 3 Calculation**: Avoid pre-building redundant edges, ensuring complementarity.<br>

### 7.3 Generation Level

✅ **Idea Fusion**: Organic fusion at the conceptual level rather than technical stacking.<br>
✅ **Story Reflection**: Reflect on fusion quality to assess conceptual unity.<br>
✅ **Novelty-First Mode**: Automatically upgrade to systemically improve innovation when stagnated.<br>
✅ **Intelligent Rollback**: Avoid ineffective refinement to improve iteration efficiency.<br>
✅ **Fallback Strategy**: Guarantee output quality by selecting the highest-scoring version.<br>

---

## 8. System Advantages

### 8.1 High Degree of Automation

* ✅ Fully automated process, no manual intervention required.
* ✅ Intelligent decision mechanisms (Novelty Mode, Rollback, Fallback).
* ✅ Adaptive parameter adjustment.

### 8.2 Multi-Layer Quality Assurance

1. **Pattern Layer**: LLM-enhanced high-quality Pattern library.
2. **Retrieval Layer**: Three-way complementary retrieval, comprehensive coverage.
3. **Fusion Layer**: Idea Fusion ensures conceptual unity.
4. **Reflection Layer**: Story Reflection assesses fusion quality.
5. **Review Layer**: Three-role Critic for comprehensive evaluation.
6. **Verification Layer**: RAG avoids collision.

### 8.3 Extensive Efficiency Optimization

* ✅ Two-stage retrieval speeds up by 13x (7 mins → 27 secs).
* ✅ Intelligent rollback avoids ineffective iterations.
* ✅ Pattern failure marking avoids repeated attempts.
* ✅ LLM response caching reduces API calls.

### 8.4 Strong Scalability

* ✅ Modular design, easy to add new features.
* ✅ Supports incremental updates to the knowledge graph.
* ✅ Adaptable to other conference data sources.
* ✅ Can add new retrieval paths.

---

## 9. Current Limitations & Future Directions

### 9.1 Data Level

**Current Limitation**:

* ⚠️ Domain granularity is too coarse; 98 Domains cover 8,285 papers.

**Future Direction**:

* 📌 Introduce Domain hierarchy (Main Domain → Sub-domain).
* 📌 Use sub_domains for fine-grained matching.
* 📌 Extend to Review data from more conferences.

### 9.2 Retrieval Level

**Current Limitation**:

* ⚠️ Path 2 Domain matching is based on keywords, which may not be precise.
* ⚠️ Retrieval speed still has room for optimization (27 seconds).

**Future Direction**:

* 📌 Use Embedding to calculate semantic similarity between Idea and Domain.
* 📌 Introduce vector database (Faiss/Milvus), speed up to 1-3 seconds.
* 📌 Pre-compute and cache all Embeddings.

### 9.3 Generation Level

**Current Limitation**:

* ⚠️ Fusion quality scoring relies on LLM, which may be unstable.
* ⚠️ Novelty Mode traversing 10 Patterns may be time-consuming.

**Future Direction**:

* 📌 Introduce a learnable fusion quality scoring model.
* 📌 Optimize Pattern selection order based on historical data.
* 📌 Generate multiple Story candidates in parallel.

### 9.4 Review Level

**Current Limitation**:

* ⚠️ Critic scoring relies on LLM and may fluctuate.
* ⚠️ No user feedback mechanism.

**Future Direction**:

* 📌 Collect real review data to train dedicated Critic models.
* 📌 Introduce user feedback for online learning and weight adjustment.
* 📌 A/B test effects of different strategies.

---

## 10. Documentation Index

### 10.1 Core Documentation

| Document | Path | Content |
| --- | --- | --- |
| **Project Summary** | `docs/00_PROJECT_OVERVIEW.md` | This document, overall overview |
| **KG Construction** | `docs/01_KG_CONSTRUCTION.md` | Data source, nodes, edges, execution method |
| **Retrieval System** | `docs/02_RECALL_SYSTEM.md` | Three-way retrieval, similarity calculation, config |
| **Idea2Story Pipeline** | `docs/03_IDEA2STORY_PIPELINE.md` | Pattern selection, Fusion, Reflection, Critic |

### 10.2 Auxiliary Documentation

| Document | Path | Content |
| --- | --- | --- |
| **Edge Types** | `docs/EDGE_TYPES.md` | Detailed edge definitions and weight calculations |
| **Pattern Scoring** | `docs/PATTERN_SCORING_EXPLAINED.md` | Pattern score calculation logic |
| **Two-Stage Retrieval** | `docs/TWO_STAGE_RECALL_OPTIMIZATION.md` | Retrieval performance optimization details |
| **Data Format** | `docs/Data_Format_Comparison.md` | V2 vs V3 data format changes |

### 10.3 Historical Documentation (Archived)

The following documents record system evolution history, but core content has been integrated into the 4 main documents above:

* `NOVELTY_MODE_FIX.md`
* `REFLECTION_REGENERATION_FIX.md`
* `WORKFLOW_CORRECTION_2025-01-25.md`
* `REFINE_SYSTEM_UPGRADE.md`
* `RECALL_USAGE_V3.md`
* etc.

---

## 11. Code Structure

```
Paper-KG-Pipeline/
├── data/                           # Data Sources
│   └── ICLR_25/
│       ├── assignments.jsonl
│       ├── cluster_library_sorted.jsonl
│       └── iclr_patterns_full.jsonl
│
├── output/                         # Output Files
│   ├── nodes_*.json               # 4 types of nodes
│   ├── edges.json                 # Edge data
│   ├── knowledge_graph_v2.gpickle # NetworkX graph
│   ├── final_story.json           # Final Story
│   └── pipeline_result.json       # Pipeline results
│
├── scripts/                        # Core Scripts
│   ├── build_entity_v3.py         # Build nodes
│   ├── build_edges.py             # Build edges
│   ├── recall_system.py           # Retrieval system (Class encapsulation)
│   ├── simple_recall_demo.py      # Retrieval Demo
│   ├── idea2story_pipeline.py     # Pipeline Main Entry
│   │
│   └── pipeline/                   # Pipeline Modules
│       ├── config.py              # Configuration parameters
│       ├── manager.py             # Workflow orchestration
│       ├── pattern_selector.py    # Pattern classification
│       ├── planner.py             # Idea Fusion
│       ├── story_generator.py     # Story generation
│       ├── story_reflector.py     # Story reflection
│       ├── critic.py              # Critic review
│       ├── refinement.py          # Intelligent refinement
│       ├── verifier.py            # RAG verification
│       └── utils.py               # Utility functions
│
├── docs/                           # Documentation
│   ├── 00_PROJECT_OVERVIEW.md     # Project Summary (This file)
│   ├── 01_KG_CONSTRUCTION.md      # KG Construction
│   ├── 02_RECALL_SYSTEM.md        # Retrieval System
│   └── 03_IDEA2STORY_PIPELINE.md  # Idea2Story Pipeline
│
└── requirements.txt                # Dependencies
```

---

## 12. Key Metrics

### 12.1 Data Scale

```
Knowledge Graph:
  - Nodes: 16,791
  - Edges: 444,872
  - Pattern: 124 (124 LLM-enhanced)
  - Idea Coverage: 100% (8,284/8,285)
```

### 12.2 Performance Metrics

```
Retrieval Speed:
  - Full Embedding: ~7 minutes
  - Two-Stage Retrieval: ~27 seconds
  - Speedup Ratio: 13x

Pipeline Execution Time:
  - Fastest: 3 minutes (First pass)
  - Typical: 5-7 minutes (2-3 refinement rounds)
  - Slowest: 10 minutes (Novelty Mode)
```

### 12.3 Quality Metrics

```
Critic Review:
  - Pass Standard: Average Score >= 7.0
  - Dimensions: Methodology, Novelty, Storyteller
  - Novelty Mode Boost: 0.5-1.5 points

Fusion Quality:
  - Threshold: >= 0.65
  - Typical Value: 0.68-0.75
  - Scoring Dimensions: Coherence (40%) + Fusion Richness (40%) + Fusion Idea Reward (20%)
```

---

## 13. Usage Recommendations

### 13.1 Quick Start

```bash
# 1. First Run (Build Knowledge Graph)
python scripts/build_entity_v3.py
python scripts/build_edges.py

# 2. Generate Paper Story
python scripts/idea2story_pipeline.py "Your Research Idea"

# 3. View Results
cat output/final_story.json
```

### 13.2 Parameter Tuning

**Improve Novelty**:

```python
# Increase Novelty Mode attempts
PipelineConfig.NOVELTY_MODE_MAX_PATTERNS = 15  # Default 10

# Increase Novelty weight
RecallConfig.PATH1_WEIGHT = 0.5  # Default 0.4, increase Similar Idea weight
```

**Improve Stability**:

```python
# Lower Fusion Quality Threshold
PipelineConfig.FUSION_QUALITY_THRESHOLD = 0.60  # Default 0.65

# Increase Head Pattern weight
RecallConfig.PATH3_WEIGHT = 0.5  # Default 0.4, increase High-Quality Paper weight
```

**Accelerate Retrieval**:

```python
# Reduce Retrieval Count
RecallConfig.PATH1_TOP_K_IDEAS = 5   # Default 10
RecallConfig.PATH3_TOP_K_PAPERS = 10 # Default 20
```

### 13.3 Monitoring Key Events

```bash
# ✅ Novelty mode activated
grep "激活【新颖性模式】" output/log.json

# 📊 Fusion quality evaluation
grep "融合质量评分" output/log.json

# 🔁 Rollback triggered 
grep "【ROLLBACK TRIGGERED】" output/log.json

# 🎉 Final Pass
grep "🎉 Critic 评审通过" output/log.json
```

---

## 14. Troubleshooting

### 14.1 Environment Issues

**Q: API key invalid**

```bash
# Check Environment Variable
echo $SILICONFLOW_API_KEY

# Set Environment Variable
export SILICONFLOW_API_KEY="your_key_here"
```

**Q: Missing dependencies**

```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### 14.2 Data Issues

**Q: Node files do not exist**

```bash
# Rebuild Knowledge Graph
python scripts/build_entity_v3.py
python scripts/build_edges.py
```

**Q: Retrieval result is empty**

```bash
# Check if Knowledge Graph is built successfully
ls -lh output/nodes_*.json
ls -lh output/knowledge_graph_v2.gpickle
```

### 14.3 Pipeline Issues

**Q: Fusion quality always below threshold**

```python
# Lower threshold or improve Fusion Prompt
PipelineConfig.FUSION_QUALITY_THRESHOLD = 0.60
```

**Q: Novelty Mode traversed all but still did not pass**

```
# Check fallback strategy in log
grep "兜底策略" output/log.json
# System automatically selects the highest scoring version to output
```

---

## 15. Summary

### 15.1 Core Achievements

✅ **Complete Knowledge Graph System**: 16,791 nodes, 444,872 edges. <br>
✅ **Efficient Retrieval System**: 13x speedup, second-level response.<br>
✅ **Intelligent Generation Pipeline**: Fusion + Reflection + Critic + Intelligent Refinement.<br>
✅ **Quality Assurance Mechanism**: Multi-layer checks, automatic rollback, fallback strategy.<br>
✅ **Complete Documentation System**: 4 core documents covering construction, retrieval, generation.<br>

### 15.2 Technical Highlights

✅ **Conceptual Level Fusion**: Idea Fusion achieves organic unity rather than technical stacking.<br>
✅ **Fusion Quality Reflection**: Story Reflector assesses fusion effectiveness.<br>
✅ **Novelty First**: Automatically upgrades to Novelty Mode when stagnated.<br>
✅ **Intelligent Rollback**: Avoids ineffective refinement, improving efficiency.<br>
✅ **LLM-Enhanced Pattern**: Dual-layer description improves usability.<br>

### 15.3 Application Value

✅ **Research Assistance**: Helps researchers quickly generate paper frameworks.<br>
✅ **Innovation Exploration**: Discovers new research directions through Pattern fusion.<br>
✅ **Writing Guidance**: Provides structured paper organization suggestions.<br>
✅ **Literature Survey**: Quickly locates relevant work based on Knowledge Graph.<br>

### 15.4 Future Outlook

📌 **Data Expansion**: Integrate data from more conferences (CVPR, NeurIPS, ACL, etc.).<br>
📌 **Model Optimization**: Train dedicated Fusion and Critic models.<br>
📌 **User Interaction**: Introduce user feedback for online learning and optimization.<br>
📌 **Multi-modal Support**: Integrate charts, formulas, code, and other multi-modal information.<br>

---

## 16. Acknowledgements

Thanks to the ICLR 2025 paper dataset for support, and SiliconFlow for providing LLM API services.

---

**Generated Date**: 2026-01-25
**Version**: V1.0
**Author**: Idea2Paper Team

**Contact**: Refer to core documents for detailed technical support.