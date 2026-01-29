# Idea2Story Pipeline Documentation

## 📋 Overview

This document provides a detailed description of the complete generation pipeline from user Idea to publishable Paper Story, including Pattern selection, Idea Fusion, Story generation, Critic review, intelligent correction mechanism, parameter configuration, and execution methods.

---

## 1. System Architecture

### 1.1 Overall Process

```
┌─────────────────────────────────────────────────────────────────┐
│              【Idea2Story Pipeline Complete Process】            │
└─────────────────────────────────────────────────────────────────┘

User Input Idea
    │
    ▼
【Phase 1: Pattern Selection and Classification】(approx. 1 second)
    │
    ├─ Recall Top-10 Patterns (from recall system)
    │   └─ Path 1 (Similar Idea) + Path 2 (Domain) + Path 3 (Similar Paper)
    │
    ├─ Multi-dimensional Pattern classification
    │   ├─ Stability (Robust): Top 3 ranks + Cluster Size≥15
    │   ├─ Novelty (Novel): Cluster Size<10
    │   └─ Cross-Domain: Different Domain sources
    │
    └─ Select initial Pattern (prioritize Stability dimension)
    │
    ▼
【Phase 2: Story Generation】(approx. 1-2 minutes)
    │
    └─ Generate draft Story based on Pattern
        ├─ Use skeleton_examples as template
        ├─ Inject common_tricks
        └─ Structured output (7 fields)
    │
    ▼
【Phase 3: Critic Review】(approx. 30 seconds)
    │
    └─ Multi-role review (parallel)
        ├─ Methodology Critic: Technical feasibility/rigor
        ├─ Novelty Critic: Innovation/problem novelty
        └─ Storyteller Critic: Narrative coherence/readability
        │
        └─ Calculate average score (avg_score)
    │
    ▼
【Phase 4: Decision Branch】
    │
    ├─【Decision 1】Score >= 7.0?
    │   ├─【Yes】→ Enter Phase 5: RAG deduplication
    │   └─【No】→ Enter Phase 4.1 or 4.2
    │
    ├─【Decision 2】Novelty stagnation? (novelty_score <= last + 0.5)
    │   ├─【Yes】→ Phase 4.1: Novelty mode
    │   └─【No】→ Phase 4.2: Normal correction
    │
    ├─────────────────────────────────────────────────────────────┐
    │              [Phase 4.1: Novelty Mode](3-10 minutes)        │
    ├─────────────────────────────────────────────────────────────┤
    │                                                             │
    │  Traverse Novelty dimension Patterns (max 10)               │
    │      │                                                      │
    │      ├─ For each novelty_pattern:                           │
    │      │                                                      │
    │      ├─ 1. Idea Fusion (concept fusion)                     │
    │      │     ├─ Input: user_idea + current_story + pattern    │
    │      │     ├─ LLM analysis: Concept A, Concept B, fusion    │
    │      │     └─ Output: fused_idea (fused new Idea)           │
    │      │                                                      │
    │      ├─ 2. Story Reflection (quality assessment)            │
    │      │     ├─ Input: fused_idea + current_story             │
    │      │     ├─ Assess 4 dimensions                           │
    │      │     │   ├─ concept_unity: Concept unity [0-10]       │
    │      │     │   ├─ technical_soundness: Technical feasibility│
    │      │     │   ├─ novelty_level: Novelty [0-10]             │
    │      │     │   └─ narrative_clarity: Narrative clarity      │
    │      │     └─ Output: fusion_score + suggestions            │
    │      │                                                      │
    │      ├─ 3. Regenerate Story                                 │
    │      │     └─ Based on fused_idea + reflection_guidance     │
    │      │                                                      │
    │      ├─ 4. Critic Review                                    │
    │      │     └─ Get new avg_score                             │
    │      │                                                      │
    │      ├─ 5. Score Degradation Detection                      │
    │      │     └─ If avg_score < last_score - 0.1:              │
    │      │         ├─ Rollback to previous version              │
    │      │         ├─ Mark Pattern as failed                    │
    │      │         └─ Skip this Pattern                         │
    │      │                                                      │
    │      ├─ 6. Record Best Result                               │
    │      │     └─ If avg_score > best_score:                    │
    │      │         └─ Update best_score and best_story          │
    │      │                                                      │
    │      ├─ 7. Pass Check                                       │
    │      │     └─ If avg_score >= 7.0:                          │
    │      │         └─ End early, enter Phase 5                  │
    │      │                                                      │
    │      └─ Loop End                                            │
    │           │                                                 │
    │           └─ Fallback: Return best_story (highest score)    │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
    │
    ├─────────────────────────────────────────────────────────────┐
    │              【Phase 4.2: Normal Correction】(1-2 minutes)   │
    ├─────────────────────────────────────────────────────────────┤
    │                                                             │
    │  Intelligently inject complementary Tricks                  │
    │      │                                                      │
    │      ├─ Analyze Critic feedback                             │
    │      │   ├─ novelty_score < 6.0 → Lacks novelty             │
    │      │   ├─ methodology_score < 6.0 → Lacks robustness      │
    │      │   └─ storyteller_score < 6.0 → Lacks narrative       │
    │      │                                                      │
    │      ├─ Select complementary Pattern                        │
    │      │   ├─ Lacks novelty → Long-tail injection (Rank 5-10) │
    │      │   ├─ Lacks robustness → Head injection (Rank 1-3)    │
    │      │   └─ Lacks narrative → Cross-domain injection        │
    │      │                                                      │
    │      └─ Return to Phase 2 (regenerate Story)                │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
    │
    ▼
【Phase 5: RAG Deduplication】(approx. 30 seconds)
    │
    ├─ Extract key methods (techniques)
    │
    ├─ Retrieve recent 3-year top conference papers (Embedding recall)
    │
    ├─ Calculate similarity
    │
    └─ Determine: Similarity > 0.75?
        ├─【No】→ Output Final Story ✅
        └─【Yes】→ Pivot avoidance
                  ├─ Analyze collision points
                  ├─ Generate constraints (disable tech/domain migration)
                  └─ Return to Phase 2
    │
    ▼
Output Final Story (JSON format)
```

**Process Description**:
- **Phase 1-2**: Basic generation pipeline
- **Phase 3**: Quality assessment
- **Phase 4**: Core correction mechanism (two modes)
  - **Novelty Mode**: Deep exploration, Fusion+Reflection
  - **Normal Correction**: Quick injection, complementary enhancement
- **Phase 5**: Deduplication verification

### 1.2 Core Modules

| Module | File | Purpose |
|--------|------|---------|
| **Pattern Selector** | `pattern_selector.py` | Multi-dimensional Pattern classification and ranking |
| **Story Generator** | `story_generator.py` | Structured Story generation |
| **Idea Fusion** | `planner.py` | Fuse new Patterns to generate innovative Ideas |
| **Story Reflector** | `story_reflector.py` | Reflect on fusion quality |
| **Multi-Agent Critic** | `critic.py` | Three-role review |
| **Refinement Engine** | `refinement.py` | Intelligent correction and injection |
| **RAG Verifier** | `verifier.py` | Deduplication and avoidance |
| **Pipeline Manager** | `manager.py` | Process orchestration |

---

## 2. Pattern Selection and Classification

### 2.1 Multi-dimensional Classification

**Objective**: Classify recalled Top-10 Patterns into 3 dimensions to ensure diversity.

**Dimension Definitions**:

| Dimension | Definition | Selection Criteria | Purpose |
|-----------|------------|-------------------|---------|
| **Stability** | Robust | Top 3 ranks + Cluster Size ≥ 15 | Ensure basic quality, reduce risk |
| **Novelty** | Novel | Cluster Size < 10 | Enhance innovation |
| **Cross-Domain** | Cross-domain | From Path 2/3 + Different Domain from Top-1 | Introduce cross-domain perspective |

**Algorithm**:

```python
def classify_patterns(recalled_patterns, user_idea):
    """Multi-dimensional Pattern classification"""
    classified = {
        'stability': [],
        'novelty': [],
        'cross_domain': []
    }

    for rank, (pattern_id, pattern_info, score) in enumerate(recalled_patterns):
        metadata = {
            'rank': rank,
            'recall_score': score,
            'cluster_size': pattern_info.get('size', 0)
        }

        # Dimension 1: Stability (Robust)
        if rank <= 2 and metadata['cluster_size'] >= 15:
            classified['stability'].append((pattern_id, pattern_info, metadata))

        # Dimension 2: Novelty (Novel)
        if metadata['cluster_size'] < 10:
            classified['novelty'].append((pattern_id, pattern_info, metadata))

        # Dimension 3: Cross-Domain
        if rank >= 3:  # From Path 2/3
            user_domain = extract_domain(user_idea)
            pattern_domain = pattern_info.get('domain', '')
            if pattern_domain != user_domain:
                classified['cross_domain'].append((pattern_id, pattern_info, metadata))

    return classified
```

### 2.2 Pattern Selection Strategy

```python
# Priority order
1. First from Stability dimension (ensure basic quality)
2. First from Novelty dimension (if stability is empty)
3. First from Cross-Domain dimension (fallback)
```

---

## 3. Story Generation Mechanism

### 3.1 Story Data Structure

```json
{
  "title": "Paper title",
  "abstract": "Abstract (150-200 words)",
  "problem_definition": "Clear problem definition",
  "gap_pattern": "Research gap description",
  "method_skeleton": {
    "overview": "Method overview",
    "core_components": ["Component 1", "Component 2", "Component 3"],
    "technical_details": "Technical details"
  },
  "innovation_claims": [
    "Contribution 1",
    "Contribution 2",
    "Contribution 3"
  ],
  "experiments_plan": {
    "datasets": ["Dataset 1", "Dataset 2"],
    "baselines": ["Baseline method 1", "Baseline method 2"],
    "metrics": ["Evaluation metric 1", "Metric 2"],
    "ablation_studies": "Ablation experiment design"
  }
}
```

### 3.2 Generation Prompt Construction

**Initial Generation Prompt**:
```python
def _build_initial_prompt(user_idea, pattern_info):
    prompt = f"""
You are a top-tier AI researcher. Please generate an ICLR-level paper Story based on the following information.

【User Idea】
{user_idea}

【Pattern Guidance】
Name: {pattern_info['name']}
Representative ideas: {pattern_info['llm_enhanced_summary']['representative_ideas']}
Common problems: {pattern_info['llm_enhanced_summary']['common_problems']}
Solution approaches: {pattern_info['llm_enhanced_summary']['solution_approaches']}
Story framework: {pattern_info['llm_enhanced_summary']['story']}

【Task】
Generate complete paper Story (JSON format), including:
- title: Attractive title
- abstract: 150-200 word abstract
- problem_definition: Clear problem definition
- gap_pattern: Research gap
- method_skeleton: Method skeleton (overview + core_components + technical_details)
- innovation_claims: 3 core contributions
- experiments_plan: Experiment design (datasets/baselines/metrics/ablation_studies)
"""
    return prompt
```

**Refinement Prompt**:
```python
def _build_refinement_prompt(story, critic_result, fused_idea, reflection_guidance):
    prompt = f"""
【Current Story】
{json.dumps(story, indent=2)}

【Critic Review Results】
Methodology: {critic_result['methodology']['score']}/10
  Issues: {critic_result['methodology']['issues']}

Novelty: {critic_result['novelty']['score']}/10
  Issues: {critic_result['novelty']['issues']}

【Fusion Innovation Guidance】
{format_fused_idea(fused_idea)}

【Reflection Suggestions】
{format_reflection_guidance(reflection_guidance)}

⚠️ 【HOW TO USE Fused Idea Guidance】
- **Title & Abstract**: Must reflect conceptual innovation from fusion, not technical stacking
- **Problem Framing**: Adopt new problem perspective from fused idea
- **Gap Pattern**: Explain why existing methods lack this conceptual unity
- **Innovation Claims**: Frame as "transforming/reframing X from Y to Z"
- **Method**: Show how techniques CO-EVOLVE together rather than CO-EXIST

【Task】
Correct Story, focusing on solving the above issues, generate improved JSON.
"""
    return prompt
```

### 3.3 LLM API Configuration

```python
# API endpoint
LLM_API_URL = "https://api.siliconflow.cn/v1/chat/completions"

# Model selection
LLM_MODEL = "Qwen/Qwen3-14B"

# API key
LLM_API_KEY = os.getenv("SILICONFLOW_API_KEY")
```

---

## 4. Idea Fusion Mechanism

### 4.1 Design Philosophy

**Core Issue**: Simple Pattern injection leads to "technology stacking" rather than "concept integration"

**Solution**: Idea Fusion - conceptual fusion at the idea level

**Fusion Formula**:
```
Fused Idea = Concept A ⊗ Concept B
```

### 4.2 Fusion Process

```
User Idea + Current Story + New Pattern
    ↓
【Phase 1: Concept Extraction】
    ├─ Extract Concept A (from user_idea)
    ├─ Extract Concept B (from pattern)
    └─ Identify connection point
    ↓
【Phase 2: Fusion Method Analysis】
    ├─ Analyze how to integrate both concepts
    ├─ Find conceptual commonalities
    └─ Design unified framework
    ↓
【Phase 3: Generate Fused Idea】
    └─ Output: New unified research idea
```

### 4.3 Fusion Prompt Design

```python
def _build_fusion_prompt(user_idea, current_story, pattern_info):
    prompt = f"""
You are a creative research strategist. Your task is to FUSE two concepts into a unified research idea.

【User's Original Idea】
{user_idea}

【Current Story Abstract】
{current_story['abstract']}

【New Pattern to Integrate】
Name: {pattern_info['name']}
Representative Ideas: {pattern_info['llm_enhanced_summary']['representative_ideas']}
Solution Approaches: {pattern_info['llm_enhanced_summary']['solution_approaches']}

【Critical Task】
Perform CONCEPTUAL FUSION (not technical stacking):
1. Extract Concept A (core concept from user's idea)
2. Extract Concept B (core concept from pattern)
3. Analyze how these concepts can be UNIFIED
4. Generate a NEW fused idea that treats them as ONE coherent concept

Return JSON format:
{
  "concept_a": "Core concept from user idea",
  "concept_b": "Core concept from pattern",
  "fusion_approach": "How to unify these concepts",
  "fused_idea": "The unified research idea (2-3 sentences)",
  "expected_benefits": "Why this fusion creates novelty"
}
"""
    return prompt
```

### 4.4 Fusion Quality Criteria

```python
# Good fusion (score > 0.65):
{
  "concept_a": "Adversarial training for robustness",
  "concept_b": "Multi-task learning for generalization",
  "fusion_approach": "Treat adversarial examples as auxiliary tasks",
  "fused_idea": "Adversarial Multi-Task Learning framework where adversarial 
                perturbations are reframed as meta-learning tasks that enhance 
                model's ability to generalize across distribution shifts"
}

# Bad fusion (score < 0.65):
{
  "concept_a": "Graph neural networks",
  "concept_b": "Attention mechanism",
  "fusion_approach": "Add attention layers to GNN",
  "fused_idea": "Use attention mechanism in graph neural networks"
}
```

---

## 5. Story Reflection Mechanism

### 5.1 Reflection Objective

After Idea Fusion, evaluate whether the generated Story truly achieves conceptual integration rather than technical stacking.

### 5.2 Reflection Dimensions

```python
reflection_dimensions = {
    'concept_unity': {
        'description': 'Are concepts treated as unified whole?',
        'good_sign': 'Concepts evolve together, mutual definition',
        'bad_sign': 'Concepts exist independently, simple combination'
    },
    'technical_soundness': {
        'description': 'Is technical implementation feasible?',
        'good_sign': 'Clear technical path, reasonable assumptions',
        'bad_sign': 'Vague implementation, unrealistic assumptions'
    },
    'novelty_level': {
        'description': 'Does fusion create new perspective?',
        'good_sign': 'Problem reframing, new understanding',
        'bad_sign': 'Incremental improvement, no new insights'
    },
    'narrative_clarity': {
        'description': 'Is story narrative clear and convincing?',
        'good_sign': 'Smooth logic, compelling motivation',
        'bad_sign': 'Disconnected logic, unclear motivation'
    }
}
```

### 5.3 Reflection Prompt

```python
def _build_reflection_prompt(fused_idea, current_story):
    prompt = f"""
You are a critical reviewer. Evaluate whether the Story successfully achieves 
CONCEPTUAL FUSION rather than technical stacking.

【Fused Idea】
{fused_idea['fused_idea']}
Concept A: {fused_idea['concept_a']}
Concept B: {fused_idea['concept_b']}

【Current Story】
Title: {current_story['title']}
Abstract: {current_story['abstract']}
Method: {current_story['method_skeleton']['overview']}

【Evaluation Task】
Score each dimension [0-10]:
1. concept_unity: Are concepts unified whole or separate parts?
2. technical_soundness: Is technical implementation feasible?
3. novelty_level: Does fusion create new perspective?
4. narrative_clarity: Is story logic clear?

Return JSON:
{
  "scores": {
    "concept_unity": score,
    "technical_soundness": score,
    "novelty_level": score,
    "narrative_clarity": score
  },
  "fusion_quality": average_score / 10.0,  # [0, 1]
  "suggestions": [
    "Specific improvement suggestion 1",
    "Specific improvement suggestion 2"
  ]
}
"""
    return prompt
```

### 5.4 Quality Threshold

```python
FUSION_QUALITY_THRESHOLD = 0.65  # Minimum acceptable fusion quality

if reflection_result['fusion_quality'] < FUSION_QUALITY_THRESHOLD:
    # Skip this Pattern, try next
    continue
```

---

## 6. Multi-Agent Critic System

### 6.1 Three-Role Design

| Role | Evaluation Focus | Key Metrics |
|------|-----------------|-------------|
| **Methodology Critic** | Technical feasibility, methodological rigor | methodology_score [0-10] |
| **Novelty Critic** | Innovation level, problem novelty | novelty_score [0-10] |
| **Storyteller Critic** | Narrative coherence, readability | storyteller_score [0-10] |

### 6.2 Critic Prompts

**Methodology Critic**:
```python
def _build_methodology_prompt(story):
    prompt = f"""
You are a rigorous methodology reviewer. Evaluate the technical soundness.

【Story】
{format_story(story)}

【Evaluation Criteria】
- Technical feasibility: Is method implementable?
- Methodological rigor: Are experimental designs sound?
- Assumptions: Are assumptions reasonable?

Score [0-10] and provide specific issues.
"""
    return prompt
```

**Novelty Critic**:
```python
def _build_novelty_prompt(story):
    prompt = f"""
You are an innovation-focused reviewer. Evaluate the novelty.

【Story】
{format_story(story)}

【Evaluation Criteria】
- Problem novelty: Is problem perspective new?
- Methodological innovation: Does solution have unique aspects?
- Contribution significance: Is contribution substantial?

Score [0-10] and provide specific issues.
"""
    return prompt
```

**Storyteller Critic**:
```python
def _build_storyteller_prompt(story):
    prompt = f"""
You are a narrative quality reviewer. Evaluate the storytelling.

【Story】
{format_story(story)}

【Evaluation Criteria】
- Logical coherence: Does narrative flow smoothly?
- Motivation clarity: Is motivation compelling?
- Readability: Is expression clear?

Score [0-10] and provide specific issues.
"""
    return prompt
```

### 6.3 Aggregated Evaluation

```python
def aggregate_critic_results(methodology, novelty, storyteller):
    """Aggregate three critics' evaluations"""
    avg_score = (methodology['score'] + 
                novelty['score'] + 
                storyteller['score']) / 3.0

    result = {
        'avg_score': avg_score,
        'pass': avg_score >= 7.0,
        'methodology': methodology,
        'novelty': novelty,
        'storyteller': storyteller
    }

    return result
```

---

## 7. Intelligent Correction Mechanism

### 7.1 Decision Tree

```
Critic Review → avg_score < 7.0?
    │
    ├─【No】→ Pass, enter RAG deduplication
    │
    └─【Yes】→ Need correction
          │
          ├─【Decision】Novelty stagnation?
          │   (novelty_score <= last_novelty + 0.5)
          │
          ├─【Yes】→ Novelty Mode
          │   └─ Traverse Novelty Patterns
          │       ├─ Idea Fusion
          │       ├─ Story Reflection
          │       ├─ Regenerate Story
          │       ├─ Critic Review
          │       └─ Check pass/score degradation
          │
          └─【No】→ Normal Correction
              └─ Analyze Critic feedback
                  ├─ novelty_score < 6.0 → Inject Novelty Pattern
                  ├─ methodology_score < 6.0 → Inject Stability Pattern
                  └─ storyteller_score < 6.0 → Inject Cross-Domain Pattern
```

### 7.2 Novelty Mode

**Trigger Condition**:
```python
if iteration > 1:
    novelty_improvement = current_novelty - last_novelty
    if novelty_improvement <= 0.5:
        # Trigger novelty mode
        enter_novelty_mode = True
```

**Execution Process**:
```python
def novelty_mode_iteration(novelty_patterns):
    """Novelty mode: deep exploration"""
    for pattern in novelty_patterns[:10]:  # Max 10 patterns
        # 1. Idea Fusion
        fused_idea = idea_fusion(user_idea, current_story, pattern)

        # 2. Story Reflection
        reflection = story_reflection(fused_idea, current_story)
        if reflection['fusion_quality'] < 0.65:
            continue  # Skip low-quality fusion

        # 3. Regenerate Story
        new_story = generate_story(fused_idea, reflection['suggestions'])

        # 4. Critic Review
        critic_result = multi_agent_critic(new_story)

        # 5. Score Degradation Detection
        if critic_result['avg_score'] < last_score - 0.1:
            # Rollback
            current_story = rollback_to_previous()
            pattern_failure_map[pattern_id] = True
            continue

        # 6. Record Best Result
        if critic_result['avg_score'] > best_score:
            best_story = new_story
            best_score = critic_result['avg_score']

        # 7. Pass Check
        if critic_result['pass']:
            return new_story, critic_result

    # Fallback: return best version
    return best_story, best_critic_result
```

### 7.3 Normal Correction

**Injection Strategy**:
```python
def select_complementary_pattern(critic_result, classified_patterns):
    """Select complementary Pattern based on Critic feedback"""
    if critic_result['novelty']['score'] < 6.0:
        # Lacks novelty → long-tail injection
        return classified_patterns['novelty'][0]  # Rank 5-10

    elif critic_result['methodology']['score'] < 6.0:
        # Lacks robustness → head injection
        return classified_patterns['stability'][0]  # Rank 1-3

    elif critic_result['storyteller']['score'] < 6.0:
        # Lacks narrative → cross-domain injection
        return classified_patterns['cross_domain'][0]

    # Default: select from Novelty
    return classified_patterns['novelty'][0]
```

### 7.4 Score Degradation Rollback

**Detection Mechanism**:
```python
def check_score_degradation(new_score, old_score):
    """Detect significant score drop"""
    DEGRADATION_THRESHOLD = 0.1

    if new_score < old_score - DEGRADATION_THRESHOLD:
        return True  # Trigger rollback
    return False
```

**Rollback Operation**:
```python
def rollback():
    """Rollback to previous version"""
    # 1. Restore Story
    current_story = previous_story.copy()

    # 2. Mark Pattern failed
    pattern_failure_map[injected_pattern_id] = True

    # 3. Delete injected Tricks
    remove_injected_tricks()

    # 4. Don't increment iteration count
    print(f"【ROLLBACK TRIGGERED】 Score dropped, restored to previous version")
```

---

## 8. RAG Deduplication Verification

### 8.1 Verification Process

```
Final Story
    ↓
【Step 1: Extract Key Methods】
    └─ Extract techniques from method_skeleton
    ↓
【Step 2: Embed and Retrieve】
    ├─ Generate Embedding for techniques
    └─ Retrieve Top-K similar papers from database
    ↓
【Step 3: Similarity Calculation】
    └─ Calculate semantic similarity with each paper
    ↓
【Step 4: Collision Detection】
    └─ If max_similarity > 0.75 → Collision detected
    ↓
【Step 5: Pivot Avoidance】
    ├─ Analyze collision points
    ├─ Generate avoidance constraints
    └─ Return to Phase 2 (regenerate Story)
```

### 8.2 Embedding Retrieval

```python
def retrieve_similar_papers(techniques):
    """Retrieve similar papers using Embedding"""
    # Generate query Embedding
    query_text = " ".join(techniques)
    query_embedding = get_embedding(query_text)

    # Retrieve from vector database
    similar_papers = vector_db.search(
        query_embedding,
        top_k=20,
        filters={'year': {'$gte': 2022}}  # Recent 3 years
    )

    return similar_papers
```

### 8.3 Collision Detection

```python
def check_collision(story, similar_papers):
    """Check if Story collides with existing work"""
    COLLISION_THRESHOLD = 0.75

    story_text = format_story_for_comparison(story)
    story_embedding = get_embedding(story_text)

    max_similarity = 0.0
    collision_paper = None

    for paper in similar_papers:
        paper_text = paper['title'] + " " + paper['abstract']
        paper_embedding = get_embedding(paper_text)

        similarity = cosine_similarity(story_embedding, paper_embedding)

        if similarity > max_similarity:
            max_similarity = similarity
            collision_paper = paper

    if max_similarity > COLLISION_THRESHOLD:
        return True, collision_paper, max_similarity

    return False, None, 0.0
```

### 8.4 Pivot Strategy

```python
def generate_pivot_constraints(collision_paper):
    """Generate avoidance constraints"""
    constraints = {
        'forbidden_techniques': extract_techniques(collision_paper),
        'alternative_domains': suggest_alternative_domains(collision_paper),
        'pivot_direction': analyze_pivot_opportunities(collision_paper)
    }

    return constraints
```

---

## 9. Parameter Configuration

### 9.1 Core Parameters

```python
class PipelineConfig:
    # Iteration control
    MAX_ITERATIONS = 3              # Maximum iterations
    MAX_NOVELTY_PATTERNS = 10       # Max patterns in novelty mode

    # Threshold settings
    CRITIC_PASS_THRESHOLD = 7.0     # Critic pass threshold
    FUSION_QUALITY_THRESHOLD = 0.65 # Fusion quality threshold
    COLLISION_THRESHOLD = 0.75      # RAG collision threshold
    DEGRADATION_THRESHOLD = 0.1     # Score degradation threshold
    NOVELTY_STAGNATION_THRESHOLD = 0.5  # Novelty stagnation threshold

    # Pattern selection weights
    STABILITY_WEIGHT = 0.4
    NOVELTY_WEIGHT = 0.4
    CROSS_DOMAIN_WEIGHT = 0.2

    # LLM settings
    LLM_MODEL = "Qwen/Qwen3-14B"
    LLM_API_URL = "https://api.siliconflow.cn/v1/chat/completions"
    EMBEDDING_MODEL = "Qwen/Qwen3-Embedding-4B"
```

### 9.2 Prompt Templates

```python
# Located in prompts/ directory
PROMPTS = {
    'initial_generation': 'prompts/initial_story.txt',
    'refinement': 'prompts/refinement.txt',
    'idea_fusion': 'prompts/idea_fusion.txt',
    'story_reflection': 'prompts/story_reflection.txt',
    'methodology_critic': 'prompts/methodology_critic.txt',
    'novelty_critic': 'prompts/novelty_critic.txt',
    'storyteller_critic': 'prompts/storyteller_critic.txt'
}
```

---

## 10. Execution Methods

### 10.1 Command Line Execution

**Basic Usage**:
```bash
cd /Users/gaoge/code/mycode/Idea2Paper/Paper-KG-Pipeline
python scripts/run_pipeline.py --idea "Your research idea" --output output/result.json
```

**With Parameters**:
```bash
python scripts/run_pipeline.py \
    --idea "Using distillation for cross-domain text classification" \
    --max-iterations 5 \
    --critic-threshold 7.5 \
    --verbose
```

### 10.2 Programmatic Usage

```python
from pipeline_manager import PipelineManager

# Initialize Pipeline
manager = PipelineManager()

# Execute
user_idea = "Your research idea"
result = manager.run(
    user_idea=user_idea,
    max_iterations=3,
    verbose=True
)

# Process results
if result['success']:
    final_story = result['final_story']
    print(f"Title: {final_story['title']}")
    print(f"Score: {result['final_score']}")
```

### 10.3 Output Format

**pipeline_result.json**:
```json
{
  "success": true,
  "final_story": {
    "title": "...",
    "abstract": "...",
    "problem_definition": "...",
    "gap_pattern": "...",
    "method_skeleton": {...},
    "innovation_claims": [...],
    "experiments_plan": {...}
  },
  "final_score": 7.2,
  "final_story_source": {
    "iteration": 2,
    "score": 7.2,
    "is_best_across_iterations": true
  },
  "iterations": 3,
  "review_history": [
    {
      "iteration": 1,
      "methodology_score": 6.5,
      "novelty_score": 5.8,
      "storyteller_score": 6.2,
      "avg_score": 6.17,
      "pass": false
    },
    ...
  ],
  "refinement_history": [
    {
      "iteration": 2,
      "action": "idea_fusion",
      "pattern": "pattern_42",
      "fusion_quality": 0.72,
      "result": "success"
    },
    ...
  ]
}
```

### 10.3 Monitoring Key Metrics

**Novelty Mode Activation**:
```bash
grep "Activated【Novelty Mode】" output/log.json
```

**Fusion Quality Scores**:
```bash
grep "Fusion quality score" output/log.json
```

**Rollback Events**:
```bash
grep "【ROLLBACK TRIGGERED】" output/log.json
```

**Final Pass Status**:
```bash
grep "🎉 Critic Review Passed" output/log.json
```

---

## 11. Detailed Process Examples

### 11.1 Scenario A: Novelty Stagnation Triggers New Mode

**Initial State**:
```
Iteration 1: Novelty Score = 5.5
Iteration 2: Novelty Score = 5.6 (only 0.1 improvement < 0.5)
→ Trigger novelty mode
```

**Novelty Mode Process**:
```
1. Activate novelty mode
2. Traverse Novelty Pattern list (max 10)

  Pattern 1 (pattern_42):
    ├─ Idea Fusion: Generate fused Idea
    ├─ Story Reflection: Fusion quality score 0.72
    ├─ Generate final Story (based on reflection suggestions)
    ├─ Critic Review: 6.5/10 (did not pass)
    └─ Continue to next Pattern

  Pattern 2 (pattern_55):
    ├─ Idea Fusion: Generate fused Idea
    ├─ Story Reflection: Fusion quality score 0.68
    ├─ Generate final Story
    ├─ Critic Review: 7.2/10 (passed!)
    └─ Enter RAG deduplication

3. RAG deduplication: No collision
4. Output Final Story
```

### 11.2 Scenario B: Score Degradation Triggers Rollback

```
Iteration 3:
  Current scores: Methodology=7.0, Novelty=6.0, Storyteller=7.5

  Inject Pattern_30:
    ├─ Idea Fusion: ...
    ├─ Generate new Story
    ├─ Critic Review: Methodology=6.2 (dropped 0.8 > 0.1)
    ├─ Detected score degradation
    └─ Trigger rollback

  Rollback operation:
    ├─ Restore Story to pre-injection version
    ├─ Mark Pattern_30 as failed
    ├─ Delete injected Tricks
    └─ Continue iteration (don't increment count)

  Select next Pattern: Pattern_45
    ├─ Idea Fusion: ...
    ├─ Generate new Story
    ├─ Critic Review: Methodology=7.3 (improved)
    └─ Save results
```

---

## 12. Final Version Selection Mechanism

### 12.1 Global Optimal Tracking

**Design Philosophy**: Throughout the iteration process, each round's generated Story may have different strengths and weaknesses. The system needs to track and ultimately select the best version.

**Core Mechanism**:
```python
# Update global best version after each Critic review
if current_avg_score > global_best_score:
    global_best_story = current_story
    global_best_score = current_avg_score
    global_best_iteration = iteration_number
    print(f"🏆 Updated global best version: score {global_best_score:.2f}")
```

### 12.2 Final Output Logic

**Priority Rules**:
1. **Priority**: If there's a version that passed Critic review (avg_score >= 7.0) → Use passed version
2. **Fallback**: If no version passed → Use global best version (highest score across iterations)

**Implementation Process**:
```python
# Final version selection
final_story = current_story  # Default to current version
final_is_passed = review_history[-1]['pass']

if not final_is_passed and global_best_story is not None:
    # Did not pass but have best version
    if global_best_score > current_score:
        final_story = global_best_story  # Use best version
        print(f"✅ Using global best version (iteration {global_best_iteration}, score {global_best_score:.2f})")
```

### 12.3 Typical Scenarios

**Scenario A: Gradual Improvement, Final Pass**
```
Iteration 1: Draft → 6.17 score → Update best version
Iteration 2: Inject Novelty Pattern → 6.85 score → Update best version
Iteration 3: Continue optimization → 7.20 score → Passed! ✅
→ Output: Iteration 3's passed version
```

**Scenario B: Fluctuating, Did Not Pass**
```
Iteration 1: Draft → 6.17 score → Update best version
Iteration 2: Inject Pattern → 6.85 score → Update best version
Iteration 3: Optimized after rollback → 6.50 score → Not updated
→ Output: Iteration 2's best version (6.85 score)
```

**Scenario C: Novelty Mode Traversal**
```
Novelty mode:
  Pattern 1 → 6.50 score → Update best version
  Pattern 2 → 6.35 score → Not updated
  Pattern 3 → 6.80 score → Update best version
  Pattern 4 → 7.10 score → Passed! ✅
→ Output: Pattern 4's passed version
```

### 12.4 Output Information

**pipeline_result.json**:
```json
{
  "success": true,
  "final_story": {...},
  "final_story_source": {
    "iteration": 2,
    "score": 6.85,
    "is_best_across_iterations": true
  },
  "iterations": 3,
  "review_history": [...]
}
```

**Log Output**:
```
🎯 Final Version Selection Logic
================================================================================
📊 Current version: avg_score=6.50, status=did not pass
🏆 Global best version: avg_score=6.85 (iteration 2)

✅ Using global best version as final output (higher score)
================================================================================

🎉 Pipeline Complete!
================================================================================
✅ Status: Requires manual review
📊 Iterations: 3
🏆 Final version source: Iteration 2
📝 Final Story:
   Title: ...
   Abstract: ...
================================================================================
```

---

## 13. Troubleshooting

### 13.1 Common Issues

**Q: Novelty mode traversed all Patterns but still did not pass**
```
Cause: All Novelty Patterns don't fit
Solution: Fallback strategy automatically selects highest-scoring version
Check: "fallback strategy" keyword in output/log.json
```

**Q: Fusion quality score always below 0.65**
```
Cause: Pattern and Idea have too much conceptual distance
Solution:
1. Check if Pattern selection is reasonable
2. Adjust FUSION_QUALITY_THRESHOLD (0.65 → 0.60)
3. Improve Fusion Prompt
```

**Q: Frequent rollbacks**
```
Cause: Injected Patterns cause score drops
Check:
1. Which Patterns failed recorded in pattern_failure_map
2. Are some Patterns completely incompatible with Idea
Solution: Optimize Pattern selection strategy
```

**Q: RAG deduplication always finds collision**
```
Cause: Idea itself highly overlaps with existing work
Solution: Pivot strategy generates avoidance constraints
Check: Need to adjust COLLISION_THRESHOLD (0.75 → 0.80)
```

### 13.2 Debug Mode

**Enable Detailed Logging**:
```python
# Add in manager.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Print Intermediate Results**:
```python
# Add prints at key steps
print(f"[DEBUG] Fused Idea: {fused_idea}")
print(f"[DEBUG] Reflection Quality: {reflection_result['fusion_quality']}")
print(f"[DEBUG] Critic Scores: {critic_result}")
```

---

## 14. Performance Optimization

### 14.1 Parallel Generation

```python
from concurrent.futures import ThreadPoolExecutor

def parallel_story_generation(patterns):
    """Generate multiple Stories in parallel"""
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(generate_story, p) for p in patterns]
        results = [f.result() for f in futures]
    return results
```

### 14.2 Cache LLM Responses

```python
import hashlib
import json

cache = {}

def cached_llm_call(prompt):
    """Cache LLM call results"""
    key = hashlib.md5(prompt.encode()).hexdigest()
    if key in cache:
        return cache[key]

    result = call_llm(prompt)
    cache[key] = result
    return result
```

---

## 15. Summary

### Core Achievements

✅ **Complete Idea2Story Pipeline**: From user Idea to publishable Story
✅ **Idea Fusion mechanism**: Achieves organic Pattern fusion rather than crude concatenation
✅ **Story Reflection**: Ensures fusion quality, evaluates conceptual unity
✅ **Intelligent correction**: Novelty mode + score degradation rollback + fallback strategy
✅ **Multi-role Critic**: Three-dimensional review, comprehensive Story quality evaluation
✅ **RAG deduplication**: Avoids collision with existing work

### Technical Features

✅ **Adaptive iteration**: Automatically selects correction strategy based on review results
✅ **Quality assurance**: Multi-level quality checks (Reflection+Critic+RAG)
✅ **Fault tolerance**: Rollback + failure marking + fallback strategy
✅ **Global optimal tracking**: Records best version each iteration, outputs passed version or highest-scoring version
✅ **Unified diagnostic mapping**: Three Critic roles directly map to three Pattern dimensions, achieving architectural consistency
✅ **Complete logging**: Detailed recording of every decision and result

### Innovations

✅ **Conceptual-level fusion**: Idea Fusion focuses on conceptual unity rather than technical concatenation
✅ **Fusion quality reflection**: Story Reflector evaluates fusion effectiveness
✅ **Novelty priority**: Automatically upgrades to novelty mode when stagnating
✅ **Intelligent rollback**: Avoids ineffective corrections, improves iteration efficiency

---

**Generation Time**: 2026-01-25
**Version**: V1.0
**Author**: Idea2Paper Team