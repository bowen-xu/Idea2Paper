# Three-Path Recall System Documentation

## 📋 Overview

This document provides a detailed description of the three-path recall system based on knowledge graph, including recall strategies, similarity calculation, multi-path fusion, parameter configuration, and execution methods.

---

## 1. System Architecture

### 1.1 Core Objective

**Input**: User's research Idea description (text)
**Output**: Top-10 most relevant research Patterns (writing patterns/method templates)

### 1.2 Technical Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                 Three-Path Recall System Architecture            │
└──────────────────────────────────────────────────────────────────┘

User Input Idea (text description)
    │
    ├────────────────────────────────────────────────────────────┐
    │              Three Parallel Paths (approx. 27 seconds)     │
    ├────────────────────────────────────────────────────────────┤
    │                                                            │
    │  ┌──────────────┬──────────────┬──────────────┐            │
    │  │   Path 1     │    Path 2    │    Path 3    │            │
    │  │ Similar Idea │  Domain      │ Similar Paper│            │
    │  │   Recall     │  Recall      │   Recall     │            │
    │  │ (Weight 0.4) │ (Weight 0.2) │ (Weight 0.4) │            │
    │  └──────────────┴──────────────┴──────────────┘            │
    │        │              │              │                     │
    │        │              │              │                     │
    │  ┌─────▼──────┐  ┌───▼────┐  ┌──────▼─────┐                │
    │  │【Coarse】  │  │【Domain】│  │【Coarse】  │                │
    │  │ Jaccard   │  │ Match   │  │ Jaccard   │                 │
    │  └───────────┘  └────────┘  └────────────┘                 │
    │        │              │              │                     │
    │  Traverse 8,284     Use Top-1      Traverse 8,285          │
    │  Idea descriptions  Idea's Domain  Paper titles            │
    │  Bag of words      Keyword match   Bag of words            │
    │  Fast filtering    Query graph     Fast filtering          │
    │        │              │              │                     │
    │  Top-100           Top-5           Top-100                 │
    │  Candidate Ideas   Domains         Candidate Papers        │
    │        │              │              │                     │
    │  ┌─────▼──────┐  ┌───▼────┐  ┌──────▼─────┐                │
    │  │【Fine】    │  │【Pattern】│  │【Fine】    │               │
    │  │ Embedding │  │ Recall  │  │ Embedding │                 │
    │  └───────────┘  └────────┘  └────────────┘                 │
    │        │              │              │                     │
    │  100 API calls     Query works_well 100 API calls          │
    │  Semantic          _in edges        Semantic               │
    │  similarity        Effect weighting × Paper quality        │
    │        │              │              │                     │
    │  Top-10            Top-K            Top-20                 │
    │  Similar Ideas     Patterns         Similar Papers         │
    │        │              │              │                     │
    │  ┌─────▼──────┐  ┌───▼────┐  ┌──────▼─────┐                │
    │  │【Pattern】 │  │【Pattern】│  │【Pattern】 │               │
    │  │ Extract   │  │ Score   │  │ Extract   │                 │
    │  └───────────┘  └────────┘  └────────────┘                 │
    │        │              │              │                     │
    │  Directly get      Domain relevance Query Paper→Pattern    │
    │  Idea.pattern_ids  × effectiveness  uses_pattern edge      │
    │  Weighted by sim   × confidence     Sim×quality weighted   │
    │        │              │              │                     │
    │  Pattern scores    Pattern scores   Pattern scores         │
    │  Dictionary        Dictionary       Dictionary             │
    │        │              │              │                     │
    └────────┼──────────────┼──────────────┼─────────────────────┘
             │              │              │
             └──────────────┴──────────────┘
                          │
                          ▼
               ┌──────────────────────┐
               │  [Multi-path Fusion] │
               └──────────────────────┘
                          │
                score = path1 × 0.4
                      + path2 × 0.2
                      + path3 × 0.4
                          │
                          ▼
                 Sort by fusion score
                          │
                          ▼
               ┌──────────────────────┐
               │   Top-10 Patterns    │
               │   Return to user     │
               └──────────────────────┘
```

**Architecture Description**:
- **Horizontal**: Three paths execute in parallel without interference
- **Vertical**: Two-stage optimization within each path (coarse→fine)
- **Fusion**: Weighted sum ensures diversity

### 1.3 Data Scale

```
Knowledge Graph Statistics:
  - Idea nodes:    8,284
  - Pattern nodes: 124
  - Domain nodes:  98
  - Paper nodes:   8,285
  - Total edges:   444,872
```

---

## 2. Three-Path Recall Strategies

### 2.1 Design Philosophy

Three-path recall captures user needs from different dimensions, avoiding duplication and information redundancy:

| Path | Matching Target | Captured Dimension | Weight | Typical Scenario |
|------|----------------|-------------------|--------|-----------------|
| **Path 1** | Idea Description | Core concept/conceptual similarity | 0.4 | User description aligns with core ideas of historical successful cases |
| **Path 2** | Domain & Sub-domains | Domain generalization ability | 0.2 | User Idea belongs to a domain with validated effective Patterns |
| **Path 3** | Paper Title | Research topic/specific problem similarity | 0.4 | User's specific problem is similar to some paper title expressions |

**Complementarity Explanation**:
- **Path 1 vs Path 3**: Path 1 focuses on "essence of ideas", Path 3 focuses on "research direction"
- **Path 2's Generalization**: Even if user Idea is completely new, as long as it belongs to a mature domain, it can recall effective Patterns commonly used in that domain

---

## 3. Path 1: Similar Idea Recall

### 3.1 Recall Process

```
User Idea (text)
    ↓ [Coarse] Jaccard fast filtering
Candidate Ideas (Top-100)
    ↓ [Fine] Embedding reranking
Similar Ideas (Top-10)
    ↓ Directly get idea.pattern_ids
Pattern set
    ↓ Weighted accumulation by similarity
Top-10 Patterns (score dictionary)
```

### 3.2 Two-Stage Recall Optimization

**Why two stages are needed?**
- Full Embedding retrieval: 8,284 API calls, takes **~7 minutes** ❌
- Two-stage recall: 100 API calls, takes **~10 seconds** ✅ (40x speedup)

**Coarse Stage (Jaccard)**:
```python
def compute_jaccard_similarity(text1, text2):
    """Calculate Jaccard similarity (bag of words model)"""
    # Tokenization
    tokens1 = set(text1.lower().split())
    tokens2 = set(text2.lower().split())

    # Jaccard = intersection/union
    intersection = len(tokens1 & tokens2)
    union = len(tokens1 | tokens2)

    return intersection / union if union > 0 else 0.0

# Coarse ranking: fast filtering of Top-100
coarse_similarities = []
for idea in ideas:  # 8,284 ideas
    sim = compute_jaccard_similarity(user_idea, idea['description'])
    if sim > 0:
        coarse_similarities.append((idea_id, sim))

coarse_similarities.sort(reverse=True)
candidates = coarse_similarities[:100]  # Coarse Top-100
```

**Fine Stage (Embedding)**:
```python
def compute_embedding_similarity(text1, text2):
    """Calculate semantic similarity using Qwen3-Embedding-4B"""
    # Get Embeddings
    emb1 = get_embedding(text1)  # API call
    emb2 = get_embedding(text2)  # API call

    # Cosine similarity
    return np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))

# Fine ranking: rerank candidates using Embedding
fine_similarities = []
for idea_id, _ in candidates:  # 100 ideas
    idea = idea_id_to_idea[idea_id]
    sim = compute_embedding_similarity(user_idea, idea['description'])
    if sim > 0:
        fine_similarities.append((idea_id, sim))

fine_similarities.sort(reverse=True)
top_ideas = fine_similarities[:10]  # Fine Top-10
```

### 3.3 Pattern Score Calculation

```python
pattern_scores = defaultdict(float)

for idea_id, similarity in top_10_ideas:
    idea = idea_id_to_idea[idea_id]

    # V3 version: directly get pattern_ids from Idea node
    for pattern_id in idea['pattern_ids']:
        # Score = similarity (accumulates when multiple Ideas use same Pattern)
        pattern_scores[pattern_id] += similarity

# Sort and keep only Top-10
sorted_patterns = sorted(pattern_scores.items(), reverse=True)
top_patterns = dict(sorted_patterns[:10])
```

**Example**:
```
User Idea: "Using Transformer for text classification"

Similar Idea_1 (similarity 0.8) → [pattern_5, pattern_10]
Similar Idea_2 (similarity 0.7) → [pattern_5, pattern_20]
Similar Idea_3 (similarity 0.6) → [pattern_10]

Path 1 scores:
  pattern_5:  0.8 + 0.7 = 1.5
  pattern_10: 0.8 + 0.6 = 1.4
  pattern_20: 0.7 = 0.7
```

---

## 4. Path 2: Domain-Related Recall

### 4.1 Recall Process

```
User Idea (text)
    ↓ Keyword matching Domain name
Related Domains (Top-5)
    ↓ Reverse lookup Pattern→Domain edges
Patterns that perform well in Domain
    ↓ Weighted by effectiveness & confidence
Top-5 Patterns (score dictionary)
```

### 4.2 Domain Matching Logic

**Method 1: Keyword Matching** (Priority):
```python
def match_domains(user_idea, domains):
    domain_scores = []
    user_tokens = set(user_idea.lower().split())

    for domain in domains:
        domain_name = domain['name']
        domain_tokens = set(domain_name.lower().split())

        # Vocabulary overlap
        match_score = len(user_tokens & domain_tokens) / max(len(user_tokens), 1)

        if match_score > 0:
            domain_scores.append((domain['domain_id'], match_score))

    domain_scores.sort(reverse=True)
    return domain_scores[:5]  # Top-5
```

**Method 2: Through Similar Idea's Domain** (Fallback):
```python
if not domain_scores:
    # Find most similar Idea
    similarities = [(idea, compute_similarity(user_idea, idea['description']))
                    for idea in ideas]
    top_idea = max(similarities, key=lambda x: x[1])[0]

    # Get that Idea's Domain (through belongs_to edge)
    for successor in G.successors(top_idea['idea_id']):
        edge_data = G[top_idea['idea_id']][successor]
        if edge_data['relation'] == 'belongs_to':
            domain_id = successor
            weight = edge_data['weight']
            domain_scores.append((domain_id, weight))
```

### 4.3 Pattern Score Calculation

```python
pattern_scores = defaultdict(float)

for domain_id, domain_weight in top_5_domains:
    # Reverse lookup: which Patterns perform well in this Domain?
    for predecessor in G.predecessors(domain_id):
        edge_data = G[predecessor][domain_id]

        if edge_data['relation'] == 'works_well_in':
            pattern_id = predecessor
            effectiveness = edge_data['effectiveness']  # [-1, 1]
            confidence = edge_data['confidence']  # [0, 1]

            # Score = Domain relevance × effectiveness × confidence
            # max(effectiveness, 0.1) avoids negative values
            score = domain_weight * max(effectiveness, 0.1) * confidence
            pattern_scores[pattern_id] += score

# Sort and keep only Top-5 (auxiliary channel)
sorted_patterns = sorted(pattern_scores.items(), reverse=True)
top_patterns = dict(sorted_patterns[:5])
```

**Edge Weight Description**:
- `effectiveness`: Pattern's effectiveness gain in that Domain (relative to baseline) [-1, 1]
  - Positive: Pattern performs better than average in that Domain
  - Negative: Pattern performs below average in that Domain
- `confidence`: Confidence based on sample size [0, 1]
  - When sample size ≥20, confidence reaches 1.0

---

## 5. Path 3: Similar Paper Recall

### 5.1 Recall Process

```
User Idea (text)
    ↓ [Coarse] Jaccard filtering (based on Paper Title)
Candidate Papers (Top-100)
    ↓ [Fine] Embedding reranking (based on Paper Title)
Similar Papers (Top-20)
    ↓ Query Paper→Pattern edge + Paper quality
Pattern set
    ↓ Similarity × quality weighted accumulation
Top-10 Patterns (score dictionary)
```

### 5.2 Two-Stage Recall

**Coarse Stage**: Same as Path 1, using Jaccard on Paper Title
**Fine Stage**: Using Embedding semantic similarity

```python
# Coarse ranking
coarse_similarities = []
for paper in papers:  # 8,285 papers
    sim = compute_jaccard_similarity(user_idea, paper['title'])
    if sim > 0:
        coarse_similarities.append((paper_id, sim))

candidates = coarse_similarities[:100]

# Fine ranking
fine_similarities = []
for paper_id, _ in candidates:
    paper = paper_id_to_paper[paper_id]
    sim = compute_embedding_similarity(user_idea, paper['title'])
    if sim > 0:
        fine_similarities.append((paper_id, sim))

top_papers = fine_similarities[:20]  # Keep Top-20
```

### 5.3 Pattern Score Calculation

```python
pattern_scores = defaultdict(float)

for paper_id, title_similarity in top_20_papers:
    paper = paper_id_to_paper[paper_id]

    # Get Paper quality score
    paper_quality = _get_paper_quality(paper)

    # Query Paper→Pattern edge
    pattern_id = paper.get('pattern_id')
    if pattern_id:
        # Score = title similarity × paper quality
        score = title_similarity * paper_quality
        pattern_scores[pattern_id] += score

# Sort and keep only Top-10
sorted_patterns = sorted(pattern_scores.items(), reverse=True)
top_patterns = dict(sorted_patterns[:10])
```

**Paper Quality Score**:
```python
def _get_paper_quality(paper):
    """Calculate Paper quality score [0, 1]"""
    review_stats = paper.get('review_stats', {})
    if review_stats:
        # Use multi-dimensional review average
        avg_score = review_stats.get('avg_score', 0.5)
        return avg_score
    return 0.5  # Default value
```

---

## 6. Multi-Path Fusion

### 6.1 Weighted Fusion

```python
def fuse_recall_results(path1_scores, path2_scores, path3_scores):
    """Weighted fusion of three paths"""
    final_scores = defaultdict(float)

    # Path 1: weight 0.4
    for pattern_id, score in path1_scores.items():
        final_scores[pattern_id] += score * 0.4

    # Path 2: weight 0.2
    for pattern_id, score in path2_scores.items():
        final_scores[pattern_id] += score * 0.2

    # Path 3: weight 0.4
    for pattern_id, score in path3_scores.items():
        final_scores[pattern_id] += score * 0.4

    # Sort and return Top-10
    sorted_patterns = sorted(final_scores.items(),
                            key=lambda x: x[1],
                            reverse=True)
    return sorted_patterns[:10]
```

### 6.2 Normalization

**Why normalize?**
- Path 1 score range: [0, 10] (accumulated similarity of 10 Ideas)
- Path 2 score range: [0, 5] (5 Domains × effectiveness)
- Path 3 score range: [0, 20] (20 Papers × quality)

**Normalization method**:
```python
def normalize_scores(scores):
    """Min-Max normalization to [0, 1]"""
    if not scores:
        return {}

    values = list(scores.values())
    min_val = min(values)
    max_val = max(values)

    if max_val == min_val:
        return {k: 1.0 for k in scores}

    return {k: (v - min_val) / (max_val - min_val)
            for k, v in scores.items()}

# Apply before fusion
path1_normalized = normalize_scores(path1_scores)
path2_normalized = normalize_scores(path2_scores)
path3_normalized = normalize_scores(path3_scores)
```

---

## 7. Parameter Configuration

### 7.1 Recall Parameters

```python
class RecallConfig:
    # Path 1: Similar Idea recall
    PATH1_TOP_K_IDEAS = 10         # Recall top K most similar Ideas
    PATH1_FINAL_TOP_K = 10         # Finally keep only Top-K Patterns

    # Path 2: Domain-related recall
    PATH2_TOP_K_DOMAINS = 5        # Recall top K most related Domains
    PATH2_FINAL_TOP_K = 5          # Finally keep only Top-K Patterns

    # Path 3: Similar Paper recall
    PATH3_TOP_K_PAPERS = 20        # Recall top K most similar Papers
    PATH3_FINAL_TOP_K = 10         # Finally keep only Top-K Patterns

    # Weight of each recall path
    PATH1_WEIGHT = 0.4             # Path 1 weight (similar Idea - important)
    PATH2_WEIGHT = 0.2             # Path 2 weight (domain-related - auxiliary)
    PATH3_WEIGHT = 0.4             # Path 3 weight (similar Paper - important)

    # Final recall Top-K
    FINAL_TOP_K = 10

    # Similarity calculation method
    USE_EMBEDDING = True           # Use embedding (recommended)

    # Two-stage recall optimization
    TWO_STAGE_RECALL = True        # Enable two-stage recall (significant speedup)
    COARSE_RECALL_SIZE = 100       # Coarse recall size (Jaccard)
    FINE_RECALL_SIZE = 20          # Fine ranking size (Embedding)
```

### 7.2 Embedding API Configuration

```python
# API endpoint
EMBEDDING_API_URL = "https://api.siliconflow.cn/v1/embeddings"

# Model selection
EMBEDDING_MODEL = "Qwen/Qwen3-Embedding-4B"

# API key
EMBEDDING_API_KEY = os.getenv("SILICONFLOW_API_KEY")
```

---

## 8. Execution Methods

### 8.1 Running Recall System Independently

**Command**:
```bash
cd /Users/gaoge/code/mycode/Idea2Paper/Paper-KG-Pipeline
python scripts/simple_recall_demo.py "Your research Idea description"
```

**Example**:
```bash
python scripts/simple_recall_demo.py "Using distillation techniques for Transformer cross-domain text classification tasks"
```

**Output**:
```
🎯 Three-Path Recall System Demo
================================================================================
【User Idea】
Using distillation techniques for Transformer cross-domain text classification tasks

🔍 [Path 1] Similar Idea Recall...
  [Coarse] Fast filtering Top-100 using Jaccard...
  [Fine] Reranking Top-10 using Embedding...
  ✓ Coarse 8284 → Fine 100 → Final 10

🌍 [Path 2] Domain-Related Recall...
  Found 3 related Domains
  ✓ Recalled 34 Patterns, kept Top-5

📄 [Path 3] Similar Paper Recall...
  [Coarse] Fast filtering Top-100 using Jaccard...
  [Fine] Reranking Top-20 using Embedding...
  ✓ Coarse 171 → Fine 100 → Final 20

🔗 Fusing three-path recall results...

📊 Recall Results Top-10
【Rank 1】 pattern_11 - Model Compression and Knowledge Distillation
  Final score: 0.1312
  ...
```

### 8.2 Using as a Class

```python
from recall_system import RecallSystem

# Initialize recall system
system = RecallSystem()

# Execute recall
user_idea = "Your research Idea"
results = system.recall(user_idea, verbose=True)

# Process results
for pattern_id, pattern_info, score in results:
    print(f"Pattern: {pattern_info['name']}, Score: {score:.4f}")
```

### 8.3 Integration into Pipeline

```python
# Use in idea2story_pipeline.py
from recall_system import RecallSystem

recall_system = RecallSystem()
recall_results = recall_system.recall(user_idea, verbose=True)

# recall_results format: [(pattern_id, pattern_info, score), ...]
```

---

## 9. Performance Optimization

### 9.1 Recall Speed Comparison

| Mode | Description | Time | API Calls |
|------|-------------|------|-----------|
| **Full Embedding** | Calculate Embedding for all 8,284 Ideas | ~7 minutes | 8,284 |
| **Two-Stage Recall** | Jaccard coarse 100→Embedding fine 10 | ~27 seconds | 100 |
| **Speedup Ratio** | - | **13x** | - |

### 9.2 Further Optimization Solutions

**Solution 1: Embedding Caching**:
```python
# Pre-compute Embeddings for all Ideas and Papers
idea_embeddings = precompute_all_embeddings(ideas)
paper_embeddings = precompute_all_embeddings(papers)

# Use cache directly during recall
user_embedding = get_embedding(user_idea)
similarities = [cosine_similarity(user_embedding, idea_emb)
                for idea_emb in idea_embeddings]
```

**Solution 2: Vector Database**:
```python
# Use vector databases like Faiss/Milvus
import faiss

# Build index
index = faiss.IndexFlatIP(embedding_dim)
index.add(idea_embeddings)

# ANN retrieval
D, I = index.search(user_embedding, k=10)  # Top-10
```
Expected speedup: **~1-3 seconds**

**Solution 3: GPU Acceleration**:
```python
# Use GPU for batch Embedding similarity calculation
import torch

user_emb = torch.tensor(user_embedding).cuda()
all_embs = torch.tensor(idea_embeddings).cuda()

similarities = torch.matmul(user_emb, all_embs.T)
```

---

## 10. Troubleshooting

### 10.1 Common Issues

**Q: All recall results are high-scoring Patterns**
```
Cause: Path 2 weight too high, causing popular Patterns to have inflated scores
Solution: Reduce PATH2_WEIGHT (0.2 → 0.1)
```

**Q: Embedding API timeout**
```
Cause: Network issues or API rate limiting
Solution:
1. Add retry mechanism
2. Add request delay (time.sleep(0.1))
3. Use caching to avoid duplicate requests
```

**Q: Recall speed is slow**
```
Cause: TWO_STAGE_RECALL=False or USE_EMBEDDING=False
Solution: Ensure two-stage recall and Embedding are enabled in config
```

**Q: Path 1 score is 0**
```
Cause: User Idea has extremely low similarity with all historical Ideas
Check: Print similarity distribution to verify if there are matching Ideas
```

### 10.2 Debug Mode

```python
# Enable detailed logging
results = system.recall(user_idea, verbose=True)

# View intermediate results
print(f"Path 1 recalled Patterns: {len(path1_scores)}")
print(f"Path 2 recalled Patterns: {len(path2_scores)}")
print(f"Path 3 recalled Patterns: {len(path3_scores)}")

# View similarity distribution
for idea_id, sim in top_ideas:
    print(f"Idea {idea_id}: {sim:.3f}")
```

---

## 11. Evaluation Metrics

### 11.1 Recall Quality Evaluation

**Relevance Evaluation**:
```python
# Manually annotate relevance of Top-10 results (0-1)
relevance_scores = []
for pattern in top_10:
    score = manual_annotation(pattern, user_idea)
    relevance_scores.append(score)

avg_relevance = np.mean(relevance_scores)
print(f"Average relevance: {avg_relevance:.2f}")
```

**Diversity Evaluation**:
```python
# Calculate cluster size distribution of Top-10 Patterns
cluster_sizes = [p['size'] for p in top_10_patterns]
diversity_score = np.std(cluster_sizes) / np.mean(cluster_sizes)
print(f"Diversity score (coefficient of variation): {diversity_score:.2f}")
```

### 11.2 Performance Monitoring

```python
import time

start = time.time()
results = system.recall(user_idea)
elapsed = time.time() - start

print(f"Recall time: {elapsed:.2f} seconds")
print(f"API calls: {api_call_count}")
```

---

## 12. Extensions and Customization

### 12.1 Custom Weights

```python
# Modify in recall_system.py
class RecallConfig:
    PATH1_WEIGHT = 0.5  # Increase Path 1 weight
    PATH2_WEIGHT = 0.1  # Decrease Path 2 weight
    PATH3_WEIGHT = 0.4
```

### 12.2 Adding New Recall Paths

**Example: Path 4 - Similar Technology Stack Recall**:
```python
def _recall_path4_similar_techniques(self, user_idea):
    """Path 4: Recall through technology stack similarity"""
    # Extract technical keywords
    techniques = extract_techniques(user_idea)

    # Match Pattern's common_tricks
    pattern_scores = defaultdict(float)
    for pattern in self.patterns:
        tricks = pattern.get('common_tricks', [])
        overlap = len(set(techniques) & set(tricks))
        pattern_scores[pattern['pattern_id']] = overlap

    return pattern_scores
```

### 12.3 Domain Specialization

```python
# Adjust parameters for specific domains (e.g., NLP)
if domain == "Natural Language Processing":
    RecallConfig.PATH1_WEIGHT = 0.5  # NLP relies more on historical experience
    RecallConfig.PATH2_WEIGHT = 0.1
```

---

## 13. Summary

### System Highlights

✅ **Three-path complementary recall**: Balances similarity, domain, and quality
✅ **Two-stage optimization**: 13x speedup, achieves second-level recall
✅ **Quality-oriented recall**: Path 3 combines Review quality scores, improving recall accuracy
✅ **LLM-enhanced Patterns**: 124 Patterns with LLM inductive summaries
✅ **Extensible architecture**: Easy to add new recall paths
✅ **Complete monitoring**: Detailed logs and evaluation metrics

### Technical Features

✅ **Embedding + Jaccard hybrid strategy**: Balances accuracy and speed
✅ **Graph-structured recall**: Uses edge weights for precise score calculation
✅ **Multi-dimensional quality scoring**: Comprehensive overall_score, confidence, contribution, correctness
✅ **Real-time calculation**: Path 3 avoids pre-building redundant edges

### To Be Improved

⚠️ **Optimize Domain matching**: Introduce hierarchical structure or Embedding matching
⚠️ **Vector database**: Further improve recall efficiency to 1-3 seconds
⚠️ **Online learning**: Adjust weights based on user feedback
⚠️ **Expand Review data**: Integrate review data from more conferences

---

**Generation Time**: 2026-01-25
**Version**: V3.1
**Author**: Idea2Paper Team