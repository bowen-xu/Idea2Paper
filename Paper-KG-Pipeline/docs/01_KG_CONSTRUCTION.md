# Knowledge Graph Construction Documentation

## 📋 Overview

This document provides a detailed description of the knowledge graph construction process in the Idea2Paper project, including data sources, node and edge definitions, construction workflow, parameter configuration, and execution methods.

---

## 1. Data Sources

### 1.1 Input Files

| File | Path | Description | Data Volume |
|------|------|-------------|-------------|
| **assignments.jsonl** | `data/ICLR_25/assignments.jsonl` | Paper to Pattern assignment relationships | 8,285 entries |
| **cluster_library_sorted.jsonl** | `data/ICLR_25/cluster_library_sorted.jsonl` | Pattern Cluster information | 124 entries |
| **iclr_patterns_full.jsonl** | `data/ICLR_25/iclr_patterns_full.jsonl` | Pattern detailed attributes (English full version) | 8,310 entries |

### 1.2 Data Structure Examples

**assignments.jsonl**:
```json
{
  "paper_id": "RUzSobdYy0V",
  "paper_title": "Quantifying and Mitigating...",
  "global_pattern_id": "g0",
  "pattern_id": "p0",
  "domain": "Fairness & Accountability",
  "sub_domains": ["Label Noise", "Disparity Metrics"],
  "cluster_id": 9,
  "cluster_prob": 0.384
}
```

**cluster_library_sorted.jsonl**:
```json
{
  "cluster_id": 24,
  "cluster_name": "Reframing Graph Learning Scalability",
  "size": 331,
  "coherence": {
    "centroid_mean": 0.668,
    "pairwise_sample_mean": 0.461
  },
  "exemplars": [...]
}
```

---

## 2. Node Definitions

### 2.1 Node Type Overview

| Node Type | Count | Primary Data Source | Purpose |
|-----------|-------|---------------------|---------|
| **Idea** | 8,284 | `iclr_patterns_full.jsonl` | Core innovations of papers |
| **Pattern** | 124 | `cluster_library_sorted.jsonl` | Writing patterns/method templates |
| **Domain** | 98 | `assignments.jsonl`(aggregated) | Research domains |
| **Paper** | 8,285 | `assignments.jsonl` + pattern details | Specific papers |

### 2.2 Pattern Nodes

**Data Source**: `cluster_library_sorted.jsonl` + LLM enhancement

**Key Fields**:
```json
{
  "pattern_id": "pattern_24",
  "cluster_id": 24,
  "name": "Reframing Graph Learning Scalability",
  "size": 331,
  "domain": "Machine Learning",
  "sub_domains": ["Graph Neural Networks", ...],
  "coherence": {...},

  "summary": {
    "representative_ideas": ["idea1", "idea2", ...],
    "common_problems": ["problem1", ...],
    "solution_approaches": ["solution1", ...],
    "story": ["story1", ...]
  },

  "llm_enhanced_summary": {
    "representative_ideas": "Inductive summary (single sentence)...",
    "common_problems": "Inductive summary (single sentence)...",
    "solution_approaches": "Inductive summary (single sentence)...",
    "story": "Inductive summary (single sentence)..."
  },

  "llm_enhanced": true,
  "exemplar_count": 6
}
```

**Construction Logic**:
```python
def _build_pattern_nodes(clusters):
    for cluster in clusters:
        if cluster_id == -1:
            continue  # Skip unassigned

        pattern_node = {
            'pattern_id': f"pattern_{cluster_id}",
            'name': cluster['cluster_name'],
            'size': cluster['size'],
            'coherence': cluster['coherence'],
            'summary': extract_from_exemplars(cluster)
        }
```

### 2.3 Idea Nodes

**Data Source**: `iclr_patterns_full.jsonl`

**Key Fields**:
```json
{
  "idea_id": "idea_0",
  "description": "By analyzing the impact of label errors on group disparity metrics...",
  "base_problem": "In the evaluation of group disparity metrics...",
  "solution_pattern": "Propose a method to estimate...",
  "story": "Extend the label error problem from model performance impact to...",
  "application": "Fairness auditing in high-risk decision systems...",
  "domain": "Fairness & Accountability",
  "sub_domains": ["Label Noise", ...],
  "source_paper_ids": ["RUzSobdYy0V"],
  "pattern_ids": ["pattern_9"]
}
```

**Deduplication Strategy**: First 16 characters of MD5 hash

**Construction Logic**:
```python
def _build_idea_nodes(pattern_details):
    for paper_id, details in pattern_details.items():
        idea_text = details['idea']
        idea_hash = hashlib.md5(idea_text.encode()).hexdigest()[:16]

        if idea_hash not in self.idea_map:
            idea_node = {
                'idea_id': f"idea_{len(self.idea_nodes)}",
                'description': idea_text,
                ...
            }
```

### 2.4 Domain Nodes

**Data Source**: `assignments.jsonl`(aggregated)

**Key Fields**:
```json
{
  "domain_id": "domain_0",
  "name": "Fairness & Accountability",
  "paper_count": 69,
  "sub_domains": ["Label Noise", "Bias Mitigation", ...],
  "related_pattern_ids": ["pattern_9", "pattern_15", ...],
  "sample_paper_ids": ["RUzSobdYy0V", ...]
}
```

**Construction Logic**:
```python
def _build_domain_nodes(assignments):
    domain_stats = defaultdict(lambda: {
        'paper_count': 0,
        'sub_domains': set(),
        'related_patterns': set()
    })

    for assignment in assignments:
        domain = assignment['domain']
        domain_stats[domain]['paper_count'] += 1
        domain_stats[domain]['sub_domains'].update(assignment['sub_domains'])
```

### 2.5 Paper Nodes

**Data Source**: `assignments.jsonl` + `iclr_patterns_full.jsonl`

**Key Fields**:
```json
{
  "paper_id": "RUzSobdYy0V",
  "title": "Quantifying and Mitigating...",
  "global_pattern_id": "g0",
  "cluster_id": 9,
  "cluster_prob": 0.384,
  "domain": "Fairness & Accountability",
  "sub_domains": [...],
  "idea": "Core idea description (string)",
  "pattern_details": {...},
  "pattern_id": "pattern_9",
  "idea_id": "idea_0",
  "domain_id": "domain_0"
}
```

---

## 3. Edge Definitions

### 3.1 Edge Classification

| Edge Type | Purpose | Count |
|-----------|---------|-------|
| **Basic Connection Edges** | Establish basic relationships between entities | ~25,000 |
| **Recall Assistance Edges** | Support three-path recall strategy | ~420,000 |

### 3.2 Basic Connection Edges

#### (1) Paper → Idea (`implements`)
```python
G.add_edge(
    paper['paper_id'],
    paper['idea_id'],
    relation='implements'
)
```

#### (2) Paper → Pattern (`uses_pattern`)
```python
G.add_edge(
    paper['paper_id'],
    paper['pattern_id'],
    relation='uses_pattern',
    quality=paper_quality  # [0, 1]
)
```

**Quality Score Calculation**:
```python
def _get_paper_quality(paper):
    reviews = paper.get('reviews', [])
    if reviews:
        scores = [r['overall_score'] for r in reviews]
        avg_score = np.mean(scores)
        return (avg_score - 1) / 9  # Normalize to [0,1]
    return 0.5  # Default value (V3 currently has no review data)
```

#### (3) Paper → Domain (`in_domain`)
```python
G.add_edge(
    paper['paper_id'],
    paper['domain_id'],
    relation='in_domain'
)
```

### 3.3 Recall Assistance Edges

#### (1) Idea → Domain (`belongs_to`)

**Weight Definition**: Proportion of Idea-related Papers in that Domain

```python
for idea in ideas:
    domain_counts = defaultdict(int)
    for paper_id in idea['source_paper_ids']:
        paper = paper_id_to_paper[paper_id]
        domain_counts[paper['domain_id']] += 1

    total_papers = len(idea['source_paper_ids'])
    for domain_id, count in domain_counts.items():
        weight = count / total_papers

        G.add_edge(
            idea['idea_id'],
            domain_id,
            relation='belongs_to',
            weight=weight,  # [0, 1]
            paper_count=count
        )
```

#### (2) Pattern → Domain (`works_well_in`)

**Weight Definition**:
- `effectiveness`: Pattern's effectiveness gain in that Domain (relative to baseline) [-1, 1]
- `confidence`: Confidence based on sample size [0, 1]

```python
for pattern in patterns:
    domain_papers = defaultdict(list)
    for paper_id in pattern['sample_paper_ids']:
        paper = paper_id_to_paper[paper_id]
        domain_papers[paper['domain_id']].append(paper)

    for domain_id, papers in domain_papers.items():
        qualities = [_get_paper_quality(p) for p in papers]
        avg_quality = np.mean(qualities)

        all_domain_papers = get_papers_in_domain(domain_id)
        domain_baseline = np.mean([_get_paper_quality(p) for p in all_domain_papers])

        effectiveness = avg_quality - domain_baseline  # [-1, 1]
        frequency = len(papers)
        confidence = min(frequency / 20, 1.0)  # [0, 1]

        G.add_edge(
            pattern['pattern_id'],
            domain_id,
            relation='works_well_in',
            frequency=frequency,
            effectiveness=effectiveness,
            confidence=confidence
        )
```

#### (3) Idea → Paper (`similar_to_paper`)

**Note**: This edge is **pre-built but not directly used** in V3.1. Path 3 recall has been changed to **real-time calculation** of similarity between user Idea and Paper Title.

---

## 4. Construction Workflow

### 4.1 Overall Workflow

```
┌─────────────────────────────────────────────────────────────┐
│          【Complete Knowledge Graph Construction Workflow】   │
└─────────────────────────────────────────────────────────────┘

【Phase 1: Data Loading】(approx. 1 second)
    │
    ├─ Load assignments.jsonl (8,285 papers)
    ├─ Load cluster_library_sorted.jsonl (124 Pattern Clusters)
    └─ Load iclr_patterns_full.jsonl (8,310 Pattern details)
    │
    ▼

【Phase 2: Node Construction】(approx. 2 minutes)
    │
    ├─ 1. Pattern nodes (124)
    │     ├─ Extract basic information from cluster_library
    │     ├─ Extract ideas/problems/solutions/stories from exemplars
    │     └─ Generate initial Pattern nodes
    │     ↓
    ├─ 2. LLM-enhanced Patterns (124, approx. 10 minutes)
    │     ├─ Call LLM for each Pattern
    │     ├─ Generate inductive summaries (4 dimensions)
    │     │   ├─ representative_ideas
    │     │   ├─ common_problems
    │     │   ├─ solution_approaches
    │     │   └─ story
    │     └─ Add llm_enhanced_summary field
    │     ↓
    ├─ 3. Idea nodes (8,284)
    │     ├─ Extract idea field from pattern_details
    │     ├─ MD5 hash deduplication
    │     └─ Extract base_problem/solution_pattern/story/application
    │     ↓
    ├─ 4. Domain nodes (98)
    │     ├─ Aggregate domain information from assignments
    │     ├─ Collect sub_domains
    │     ├─ Count paper_count
    │     └─ Associate related_pattern_ids
    │     ↓
    └─ 5. Paper nodes (8,285)
          ├─ Merge assignments and pattern_details
          ├─ Extract title/domain/sub_domains/idea
          └─ Preserve cluster_id/global_pattern_id
    │
    ▼

【Phase 3: Establish Associations】(approx. 1 second)
    │
    ├─ Paper → Pattern association
    │    └─ Map cluster_id to pattern_id
    │        Coverage: 5,981/8,285 (72.2%)
    │
    ├─ Paper → Idea association
    │    └─ Map through MD5 hash of idea text
    │        Coverage: 8,284/8,285 (100%)
    │
    ├─ Paper → Domain association
    │    └─ Map domain name to domain_id
    │        Coverage: 8,285/8,285 (100%)
    │
    └─ Idea → Pattern association
         └─ Establish connection through Paper intermediary
             ├─ Collect all Papers associated with each Idea
             ├─ Extract pattern_id from these Papers
             └─ Populate Idea.pattern_ids field
             Average 0.7 Patterns per Idea
    │
    ▼

【Phase 4: Save Nodes】(approx. 1 second)
    │
    ├─ Save nodes_idea.json
    ├─ Save nodes_pattern.json
    ├─ Save nodes_domain.json
    └─ Save nodes_paper.json
    │
    ▼

【Phase 5: Build Edges】(approx. 2-3 minutes)
    │
    ├─ Basic connection edges
    │    ├─ Paper → Idea (implements) 8,284 edges
    │    ├─ Paper → Pattern (uses_pattern) 5,981 edges
    │    └─ Paper → Domain (in_domain) 8,285 edges
    │
    ├─ Recall assistance edges - Path 2
    │    ├─ Idea → Domain (belongs_to)
    │    │   └─ Weight: Proportion of Idea-related Papers in that Domain
    │    │
    │    └─ Pattern → Domain (works_well_in)
    │        ├─ effectiveness: Pattern's effectiveness gain in Domain
    │        └─ confidence: Confidence based on sample size
    │
    └─ Recall assistance edges - Path 3
         └─ (Real-time calculation, not pre-built)
    │
    ▼

【Phase 6: Save Graph】(approx. 1 second)
    │
    ├─ Output edges.json
    └─ Output knowledge_graph_v2.gpickle
    │
    ▼

✅ Construction Complete
   ├─ Total nodes: 16,791
   ├─ Total edges: 444,872
   └─ Total time: approx. 15-18 minutes
```

### 4.2 Key Steps

#### Step 1: Load Data
```python
assignments = _load_assignments()      # 8,285 entries
clusters = _load_clusters()            # 124 entries
pattern_details = _load_pattern_details()  # 8,310 entries
```

#### Step 2: Build Nodes
```python
_build_pattern_nodes(clusters)         # 124 Patterns
_enhance_patterns_with_llm(clusters)   # LLM enhancement
_build_idea_nodes(pattern_details)     # 8,284 Ideas
_build_domain_nodes(assignments)       # 98 Domains
_build_paper_nodes(assignments, pattern_details)  # 8,285 Papers
```

#### Step 3: Establish Associations
```python
_link_paper_to_pattern(assignments)    # Paper → Pattern
_link_paper_to_idea()                  # Paper → Idea
_link_paper_to_domain()                # Paper → Domain
_link_idea_to_pattern()                # Idea → Pattern (via Paper intermediary)
```

#### Step 4: Build Edges
```python
_build_paper_edges()                   # Basic connection edges
_build_idea_belongs_to_domain_edges()  # Recall edges - Path 2
_build_pattern_works_well_in_domain_edges()
_build_idea_similar_to_paper_edges()   # Recall edges - Path 3
```

#### Step 5: Save Results
```python
_save_nodes()  # Save 4 types of node JSON
_save_edges()  # Save edges.json
_save_graph()  # Save knowledge_graph_v2.gpickle
```

---

## 5. LLM Enhancement Mechanism

### 5.1 Enhancement Objective

Generate inductive summaries for each Pattern cluster, preserving both specific examples and providing a global overview.

### 5.2 Prompt Design

```python
def _build_llm_prompt_for_pattern(pattern_node, exemplars):
    prompt = f"""
You are an academic research expert. Based on the Pattern information from the following {len(exemplars)} papers,
generate an inductive summary for Pattern Cluster "{pattern_node['name']}".

【Paper Pattern Information】
{format_exemplars(exemplars)}

【Task】
Please generate inductive summaries for 4 dimensions (each 1 sentence, 80-120 words):
1. representative_ideas: Representative research ideas
2. common_problems: Common problems addressed
3. solution_approaches: Solution approach characteristics
4. story: Research narrative framework

Return JSON format.
"""
    return prompt
```

### 5.3 API Configuration

```python
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY")
LLM_API_URL = "https://api.siliconflow.cn/v1/chat/completions"
LLM_MODEL = "Qwen/Qwen2.5-7B-Instruct"
```

---

## 6. Parameter Configuration

### 6.1 Path Configuration

```python
# Data input paths
DATA_DIR = PROJECT_ROOT / "data" / "ICLR_25"
ASSIGNMENTS_FILE = DATA_DIR / "assignments.jsonl"
CLUSTER_LIBRARY_FILE = DATA_DIR / "cluster_library_sorted.jsonl"
PATTERN_DETAILS_FILE = DATA_DIR / "iclr_patterns_full.jsonl"

# Output paths
OUTPUT_DIR = PROJECT_ROOT / "output"
NODES_IDEA = OUTPUT_DIR / "nodes_idea.json"
NODES_PATTERN = OUTPUT_DIR / "nodes_pattern.json"
NODES_DOMAIN = OUTPUT_DIR / "nodes_domain.json"
NODES_PAPER = OUTPUT_DIR / "nodes_paper.json"
EDGES_FILE = OUTPUT_DIR / "edges.json"
GRAPH_FILE = OUTPUT_DIR / "knowledge_graph_v2.gpickle"
```

### 6.2 LLM Configuration

```python
# API key (environment variable)
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY")

# API endpoint
LLM_API_URL = "https://api.siliconflow.cn/v1/chat/completions"

# Model selection
LLM_MODEL = "Qwen/Qwen2.5-7B-Instruct"  # Node construction
# or "Qwen/Qwen3-14B"  # Pipeline generation
```

### 6.3 Edge Construction Configuration

```python
# Pattern-Domain edge weight calculation
BASELINE_SAMPLE_SIZE = 20  # Sample size threshold for confidence to reach 1.0

# Paper quality scoring
# Prioritize using review_stats.avg_score (based on multi-dimensional Review scores)
# Use default value 0.5 when no review data is available
```

---

## 7. Execution Methods

### 7.1 Environment Setup

**Dependency Installation**:
```bash
cd /Users/gaoge/code/mycode/Idea2Paper/Paper-KG-Pipeline
pip install -r requirements.txt
```

**Environment Variable Setup**:
```bash
export SILICONFLOW_API_KEY="your_api_key_here"
```

### 7.2 Build Nodes

**Command**:
```bash
python scripts/build_entity_v3.py
```

**Output**:
```
output/
├── nodes_idea.json           # 8,284 Idea nodes
├── nodes_pattern.json        # 124 Pattern nodes
├── nodes_domain.json         # 98 Domain nodes
├── nodes_paper.json          # 8,285 Paper nodes
└── knowledge_graph_stats.json # Statistics
```

**Execution Time**: Approx. 10-15 minutes (including LLM enhancement)

### 7.3 Build Edges

**Command**:
```bash
python scripts/build_edges.py
```

**Output**:
```
output/
├── edges.json                # Edge data (JSON format)
└── knowledge_graph_v2.gpickle # Complete graph (NetworkX format)
```

**Execution Time**: Approx. 2-3 minutes

### 7.4 Verify Graph

**Python Interactive Verification**:
```python
import json
import pickle

# Load nodes
with open('output/nodes_pattern.json') as f:
    patterns = json.load(f)
print(f"Pattern count: {len(patterns)}")

# Load graph
with open('output/knowledge_graph_v2.gpickle', 'rb') as f:
    G = pickle.load(f)
print(f"Node count: {G.number_of_nodes()}")
print(f"Edge count: {G.number_of_edges()}")
```

---

## 8. Output Statistics

### 8.1 Node Statistics

```
Total nodes:  9,411
  - Idea:      8,284 (100% coverage)
  - Pattern:   124
  - Domain:    98
  - Paper:     8,285
```

### 8.2 Edge Statistics

```
【Basic Connection Edges】
  Paper→Idea:      8,284 edges
  Paper→Pattern:   5,981 edges (72.2% coverage)
  Paper→Domain:    8,285 edges

【Recall Edges - Path 2】
  Idea→Domain:     ~15,000 edges
  Pattern→Domain:  ~3,500 edges

【Recall Edges - Path 3】
  (Real-time calculation, no pre-built edges)

Total edges: 444,872
```

### 8.3 Data Quality

```
✅ Idea coverage: 100% (8,284/8,285)
✅ Pattern coverage: 72.2% (based on cluster assignment)
✅ LLM enhancement: 124/124 Pattern nodes
✅ Clustering quality: Quantifiable evaluation (coherence metric)
```

---

## 9. Troubleshooting

### 9.1 Common Issues

**Q: LLM API call failure**
```
Error: Connection timeout / API key invalid
Solution:
1. Check network connection
2. Verify SILICONFLOW_API_KEY environment variable
3. Check API quota
```

**Q: Insufficient memory**
```
Error: MemoryError
Solution:
1. Reduce number of exemplars for LLM enhancement (default 20→10)
2. Process Pattern nodes in batches
```

**Q: Output file already exists**
```
Behavior: Automatic overwrite
Recommendation: Backup important output/ files before running
```

### 9.2 Log Viewing

The construction process outputs detailed logs:
```
🚀 Starting Knowledge Graph Construction V3 (ICLR data source)
【Step 1】Load data
  ✅ Loaded 8285 paper assignments
【Step 2】Build nodes
  ✓ Created 124 Pattern nodes
  ✓ LLM enhancement: 124/124 completed
【Step 3】Establish node associations
  ✓ Total 8284 Idea->Pattern connections established
【Step 4】Save nodes
【Step 5】Statistics
✅ Knowledge Graph Construction Complete!
```

---

## 10. Extensions and Optimizations

### 10.1 Data Source Extension

**Adding New Conference Data**:
1. Prepare JSONL files consistent with ICLR format
2. Modify `DATA_DIR` path
3. Re-run `build_entity_v3.py`

### 10.2 Review Data Extension

**Current Status**: Paper nodes have integrated ICLR 2025 review data, including multi-dimensional scores

**Data Structure**:
```json
{
  "paper_id": "xxx",
  "review_ids": ["review_1", "review_2", ...],
  "review_stats": {
    "review_count": 4,
    "avg_score": 0.656,
    "highest_score": 0.790,
    "lowest_score": 0.575
  }
}
```

**Extension Plan**: Can add review data from more conferences to enrich the knowledge graph

### 10.3 Performance Optimization

**LLM Enhancement Acceleration**:
```python
# Parallel processing of Patterns
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(_enhance_single_pattern, p)
               for p in pattern_nodes]
```

---

## 11. Summary

### Core Achievements

✅ Successfully built knowledge graph based on ICLR data source
✅ Achieved 100% Idea coverage
✅ Introduced LLM enhancement, generating inductive summaries for each Pattern
✅ Preserved clustering quality metrics (coherence)
✅ Modular code, easy to extend

### Technical Features

✅ **LLM Integration**: Using SiliconFlow API to enhance Pattern descriptions
✅ **Prompt Engineering**: Structured prompt design
✅ **Fault Tolerance**: Automatic JSON parsing and repair
✅ **Dual-Layer Description**: Specific examples + global summary

### Extensibility

✅ Supports incremental updates
✅ Adaptable to other conference data sources
✅ Provides complete node foundation for recall system

---

**Generation Time**: 2026-01-25
**Version**: V3.1
**Author**: Idea2Paper Team