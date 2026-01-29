<p align="center">
  <img src="assets/images/logo.png" alt="Idea2Paper Logo" width="120">
</p>

<h1 align="center">
  Idea2Paper: Automated Pipeline for Transforming Research Concepts into Complete Scientific Narratives
</h1>

<p align="center">
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/Python-3.10%2B-green" />
  </a>
  <a href="https://arxiv.org/abs/2601.20833">
    <img src="https://img.shields.io/badge/arXiv-2601.20833-b31b1b.svg" />
  </a>
</p>


<p align="center">
  <a href="./README.md">English</a>
  &nbsp;|&nbsp;
  <a href="./README_zh.md">简体中文</a>
</p>


---

## 🚀 Overview
**Idea2Paper** is an end-to-end pipeline that transforms your research **Idea** into a submission-ready **Story** (Scientific Narrative Skeleton).

**Pipeline**: 💡 **KG Retrieval** → 🧩 **Pattern Selection** → ✍️ **Story Generation** → 👥 **Calibrated Review** → 🔁 **Refinement** → 🧪 **Novelty Verification**

<p align="center">
  <img src="assets/images/idea2storypipeline.png" width="800">
</p>

### Core Features

- **Knowledge Graph**:  Built from 8,000+ ICLR papers

- **Three-Way Retrieval + Two-Stage Acceleration**: Coarse ranking (Jaccard) + Fine ranking (Embedding). 

- **Anchored Multi-Agent Review (Calibrated)**: Uses real review statistics as anchors to ensure objective, traceable scoring.

- **Runtime Log System**: Independent directory for each run, recording events + LLM/embedding inputs and outputs for auditing and replay.

<details><summary><h3>Table of Contents </h3></summary>

- [🔥 Quick Start](#-quick-start-)
- [🗂️ Project Structure](#-project-structure-)
- [⚙️ Configuration Guide](#-configuration-guide-env--i2p_configjson)
- [🤖 What is Multi-Agent Review?](#-what-is-multi-agent-review-calibrated--traceable)
- [🧾 Logs & Debugging](#-logs--debugging-highly-recommended)
- [📖 More Documentation](#-more-documentation-optional)
- [📌 Citation](#-citation)

</details>

---

## 🔥 Quick Start
### 1. Prerequisites & Installation

* Python 3.10+ (recommended)
```bash
git clone https://github.com/AgentAlphaAGI/Idea2Paper.git
cd Idea2Paper/Paper-KG-Pipeline
pip install -r requirements.txt
```

### 2. Prepare Data (Two Methods)

##### **Method A: Using a pre-built Knowledge Graph (recommended)**

The KG construction step is a **one-time** process. If the following cached outputs already exist under `Paper-KG-Pipeline`, you can run the generation pipeline directly.

```text
Paper-KG-Pipeline/
└── output/
    ├── nodes_idea.json
    ├── nodes_pattern.json
    ├── nodes_domain.json
    ├── nodes_paper.json
    ├── edges.json
    └── knowledge_graph_v2.gpickle  # serialized graph cache
```

##### **Method B: Build the Knowledge Graph (one-time setup)**

1. Make sure the ICLR dataset is placed under:
   - `Paper-KG-Pipeline/data/`

   *Refer to the dataset input instructions:`Paper-KG-Pipeline/docs/01_KG_CONSTRUCTION.md`*

2. Run the KG construction scripts:

```bash
python Paper-KG-Pipeline/scripts/build_entity_v3.py
python Paper-KG-Pipeline/scripts/build_edges.py
```


### 3. Configuration

This project supports `.env` + `i2p_config.json`. The priority order is fixed as: `shell export` > Repo root `.env` > Repo root `i2p_config.json` > Code defaults.

Copy the example environment file and set your `SILICONFLOW_API_KEY`:
```bash
cp .env.example .env
```


Edit `.env` and fill in your `SILICONFLOW_API_KEY` (Do not commit this to git).
2. (Optional) Copy user configuration file (Place non-sensitive parameters here)
```bash
cp i2p_config.example.json i2p_config.json
```


### 4. Generate Story

```bash
python Paper-KG-Pipeline/scripts/idea2story_pipeline.py "Your Research Idea Description"
```
**Common Modes:**

* **Local No-Key Smoke Test** (Allows non-strict fallback, easier to run through): Set `I2P_CRITIC_STRICT_JSON=0` in `.env`.
* **Quality Mode** (Recommended): `SILICONFLOW_API_KEY` valid + `I2P_CRITIC_STRICT_JSON=1`.

**Output**
```text
output/
├── final_story.json          # Final generated paper story
├── pipeline_result.json      # Full pipeline results
└── log.json                  # Detailed logs
```

Check `final_story.json` for the result and `pipeline_result.json` for the full process.

#### For advanced usage, configuration options, and troubleshooting, see our [User Guide](./Paper-KG-Pipeline/README.md).

---

## 🗂️ Project Structure
```text
Paper-KG-Pipeline/
├── data/ICLR_25/               # Data source
├── output/                     # Output files
├── scripts/
│   ├── build_entity_v3.py      # Build nodes
│   ├── build_edges.py          # Build edges
│   ├── recall_system.py        # Retrieval system
│   ├── idea2story_pipeline.py  # Pipeline main entry
│   └── pipeline/               # Pipeline modules
│       ├── config.py
│       ├── manager.py
│       ├── pattern_selector.py
│       ├── planner.py          # Idea Fusion
│       ├── story_generator.py
│       ├── story_reflector.py  # Story Reflection
│       ├── critic.py
│       ├── refinement.py
│       └── verifier.py
└── docs/                       # Core documentation (4 files)
    ├── 00_PROJECT_OVERVIEW.md
    ├── 01_KG_CONSTRUCTION.md
    ├── 02_RECALL_SYSTEM.md
    └── 03_IDEA2STORY_PIPELINE.md
```

### Engineering Layering

**Core Implementation:**
- `Paper-KG-Pipeline/src/idea2paper/`: Library code (infra / review / pipeline / recall).

**Entry Scripts (Commands unchanged):**
- `Paper-KG-Pipeline/scripts/idea2story_pipeline.py`: End-to-end pipeline entry.
- `Paper-KG-Pipeline/scripts/simple_recall_demo.py`: Retrieval-only demo.

**Data / Artifacts:**
- `Paper-KG-Pipeline/output/`: Knowledge Graph and run artifacts (nodes / edges / graph / story / result).
- Repo root `log/`: Audit logs for every run.
 
**Compatibility Layer:**
- `Paper-KG-Pipeline/scripts/pipeline/`: Compatibility shims (Prevents old imports from breaking; new code suggested to go via `src/idea2paper`).

---

## ⚙️ Configuration Guide (.env / i2p_config.json)
### .env (Sensitive Info + Common Toggles)

- `.env` is automatically loaded when the entry script starts (no need to manually export).
- Boolean values recognize `1/0` only (Only `1` is true).
- Reference and copy: `.env.example`

**Most Critical:**

* `SILICONFLOW_API_KEY`: SiliconFlow API Key (LLM + embeddings).
* `I2P_CRITIC_STRICT_JSON`: Review JSON Strict Mode (1=Quality First; 0=No-Key Smoke Test).

### i2p_config.json (Centralized Non-Sensitive Config)

- Reference and copy: `i2p_config.example.json`
- Suitable for: Pass rules, log directories, anchor parameters, LLM url/model, etc.
- Config file path can be specified via env: `I2P_CONFIG_PATH=/abs/path/to/i2p_config.json`

---

## 🤖 What is Multi-Agent Review (Calibrated & Traceable)?
Traditional "LLM directly giving a 1~10 score" is not auditable. This project uses **Anchored MultiAgentCritic**:

1. **Real Ruler from Graph Data**
Uses `review_stats` (real mean score / review count / divergence) from `Paper-KG-Pipeline/output/nodes_paper.json` to construct a `score10` ruler.
2. **LLM Makes Relative Judgments Only, No Direct Scoring**
The LLM is given a set of "anchor papers" (containing real `score10`). The LLM only outputs: `better|tie|worse` + `confidence` + `rationale` (Must cite the score10 of the anchor). 


3. **Final 1~10 Score Fitted by Deterministic Algorithm**
Same batch of anchors + same comparisons JSON → Score is guaranteed to be consistent; Evidence chain preserved in `audit`: `pattern_id` + `anchors(paper_id/title/score10/review_count/weight)` + `comparisons` + `loss` -> `score`.

**Passing Standard (More Objective) Based on Full Pattern Reality**
Default uses "Scheme B": Calculate `q50/q75` on the full `score10` distribution of papers for the current `pattern_id`:

* At least 2 out of three dimensions ≥ `q75`
* And `avg` ≥ `q50`
* Thresholds and judgment details are written into `audit.pass` and runtime event logs.

For a more detailed explanation, see: [MULTIAGENT_REVIEW](MULTIAGENT_REVIEW.md)

---

## 🧾 Logs & Debugging (Highly Recommended)
Every run creates a directory: `log/run_YYYYMMDD_HHMMSS_<pid>_<rand>/`

* `meta.json`: Run meta-info (idea / argv / entry point, etc.)
* `events.jsonl`: Key process events (Retrieval, Pattern Selection, Review Rounds, Rollback/Pivot, Threshold Pass, etc.)
* `llm_calls.jsonl`: Input/Output/Duration/Success status for every LLM chat (Plaintext keys are not recorded).
* `embedding_calls.jsonl`: Info for every embedding call.

**Common Troubleshooting:**

* **Score always around 6.x:** Check `pass_threshold_computed` in `events.jsonl` (The `q75` for many patterns is naturally around 6.x).
* **Strict Mode Failure:** Check `events.jsonl` for `critic_invalid_output_*` (JSON validation failure triggers retries; if it still fails, the process terminates).

---

## 📖 More Documentation (Optional)
If you need deeper implementation details:

| No.   | Document                                                                     | Content                                                                          | Target Audience |
| ----- |------------------------------------------------------------------------------| -------------------------------------------------------------------------------- | --------------- |
| **0** | [Project Overview](Paper-KG-Pipeline/docs/00_PROJECT_OVERVIEW.md)            | Overall Architecture and Process  | Everyone        |
| **1** | [Knowledge Graph Construction](Paper-KG-Pipeline/docs/01_KG_CONSTRUCTION.md) | Knowledge Graph Construction                | Developers      |
| **2** | [Retrieval System](Paper-KG-Pipeline/docs/02_RECALL_SYSTEM.md)               | Three-Way Recall and Two-Phase Optimization | Developers      |
| **3** | [Idea2Story Pipeline](Paper-KG-Pipeline/docs/03_IDEA2STORY_PIPELINE.md)      | Complete Generation/Review/Revision/Duplicate Check Mechanism                 | Developers      |

### Documentation Highlights

✅ **Full Coverage**: From data construction to the full generation pipeline<br>
✅ **Run Guide**: Each document includes detailed execution instructions and parameter configuration<br>
✅ **Flowcharts**: Uses Mermaid diagrams to clearly illustrate the architecture and workflow<br>
✅ **Troubleshooting**: Includes common issues and solutions<br>

---

## 📌 Citation
If you find this project useful, please consider citing our paper:

```bibtex
@article{idea2story2026,
  title={Idea2Story: An Automated Pipeline for Transforming Research Concepts into Complete Scientific Narratives},
  journal={arXiv preprint arXiv:2601.20833},
  year={2026},
  doi={10.48550/arXiv.2601.20833},
  url={https://arxiv.org/abs/2601.20833}
}