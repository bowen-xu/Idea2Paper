# MultiAgentReview (Based on Graph-Based Real Review Ruler) Explanation

[English](MULTIAGENT_REVIEW.md) | [简体中文](MULTIAGENT_REVIEW_zh.md)


This document explains the **MultiAgentReview / MultiAgentCritic** methodology used in `Paper-KG-Pipeline` within this repository: how to use real `review_stats` from the knowledge graph as a "calibrated" objective ruler, how to calculate final scores, and how to adjust "strictness" via configuration.

---

## 0. Quick Summary (Key Points to Remember)

* The LLM **no longer directly assigns scores from 1 to 10**; it only outputs "better/worse/tie relative to anchor papers + confidence + rationale (must cite anchor score10)".
* The final 1~10 score is calculated by a **deterministic algorithm**: The same batch of anchors + the same comparisons JSON → The score is guaranteed to be consistent.
* The passing standard is no longer a fixed 7.0: **Scheme B** is adopted by default (2/3 dimensions ≥ q75 and avg ≥ q50), where q50/q75 are derived from the real distribution of **all papers** under that pattern.
* In strict quality mode: If the critic's JSON is invalid → Auto-retry → If it still fails, **terminate the current run immediately**, disallowing arbitrary 6.x fallback scores.

Relevant Code Entry Points:

* Anchored Critic: `Paper-KG-Pipeline/scripts/pipeline/critic.py`
* Anchor/Distribution Index: `Paper-KG-Pipeline/scripts/pipeline/review_index.py`
* Configuration: `Paper-KG-Pipeline/scripts/pipeline/config.py`
* Run Logs: Repo root directory `log/run_.../`

---

## 1. What is MultiAgentReview? (Three Reviewers + Three Dimensions)

The system includes 3 fixed reviewer roles (multi-agent), each outputting a dimension score:

* **Methodology**: Whether the method is sound, technical details are rigorous, and experiments are credible.
* **Novelty**: Whether the innovation is solid or just a trivial stacking of existing methods.
* **Storyteller**: Whether the narrative is complete (Motivation → Method → Experiments → Conclusion loop is closed).

Final Output:

* `score` (1~10) for each role
* `avg_score` (Average of the three roles)
* `main_issue` (The lowest scoring role mapped to `novelty / stability / domain_distance`)
* `audit` (Audit information: anchors, comparisons, loss, passing thresholds, and decision details)

---

## 2. Where Does the "Objective Ruler" Come From? (Real review_stats → score10)

### 2.1 Data Source

Only uses paper node data exported from the graph:

* `Paper-KG-Pipeline/output/nodes_paper.json`
  * Each paper carries `review_stats`: `avg_score`, `review_count`, `highest_score`, `lowest_score`, etc.



### 2.2 score10 and Weight

In `ReviewIndex`, real statistics are mapped to a 1~10 scale:

* `score10 = 1 + 9 * avg_score`
* `dispersion10 = 9 * (highest_score - lowest_score)` (Larger divergence implies lower reliability)
* `weight = log(1 + review_count) / (1 + dispersion10)` (More reviews imply higher credibility; larger divergence implies lower weight)

These values are cached as `paper_summary` and used for:

* Selecting anchors
* Fitting the final score (Weighted Loss)

---

## 3. How are Anchors Selected? Why Not Give All?

Feeding all papers under a pattern to the LLM would lead to context explosion, high costs, and unstable outputs. The correct approach:

* **Offline/Index Layer**: Use "all papers" under that pattern to calculate the distribution (q50/q75, etc.).
* **Online/LLM Benchmarking**: Only provide 5~9 anchor papers for benchmarking.

Current Strategy (Fixed 5 + Adaptive Padding up to 9):

1. Fixed Anchors (Most stable, reproducible)
   * Take quantiles of `score10` under that pattern: q10/q25/q50/q75/q90 (5 papers).


2. Optional Exemplars (If pattern_info contains exemplar_paper_ids)
   * Supplement with 0~2 most reliable exemplars (sorted by weight/review_count).


3. Adaptive Padding (Pad up to 9 papers if necessary)
   * If the first round of fitting is unstable (high loss, low confidence, or non-monotonic benchmarking), pad with 2~4 papers closer to the "current estimated score" and benchmark again.



Code Location: `Paper-KG-Pipeline/scripts/pipeline/review_index.py`

---

## 4. What Does the LLM Actually Do in Review? (Relative Judgment Only)

### 4.1 LLM Output Format (comparisons)

Each role receives the same set of anchors (containing real `score10`), and the LLM must return JSON:

* For each anchor, provide: `better / tie / worse` + `confidence(0~1)` + `rationale`
* The rationale must cite the corresponding anchor's `score10: X.X`

The LLM is **NOT allowed** to output a final score.

### 4.2 From comparisons to Probability p_i (Deterministic Mapping)

Map judgement/confidence to probability ("probability of beating the anchor"):

* better: `p = 0.5 + 0.45 * confidence`
* tie:    `p = 0.5`
* worse:  `p = 0.5 - 0.45 * confidence`

Intuition: Higher confidence pushes p further from 0.5; tie is always 0.5.

---

## 5. How is the Final 1~10 Score Calculated? (Deterministic Fitting)

Goal: Find a score S such that for each anchor score s_i, the model's predicted "win rate" is close to the p_i given by the LLM.

* Predicted Win Rate: `sigmoid(k*(S - s_i))`
* k is a constant (default 1.2)
* Use Weighted Least Squares Fitting:
  * `loss(S) = Σ w_i * (sigmoid(k*(S-s_i)) - p_i)^2`

* Grid search for S over `[1,10]` (step size default 0.01), take S that minimizes loss.

This step is completely deterministic: Same anchors + Same comparisons → The resulting S is guaranteed to be consistent.

Code Location: `Paper-KG-Pipeline/scripts/pipeline/critic.py` (`_compute_score_from_comparisons`)

---

## 6. Passing Standard (Scheme B): Relative to Full Pattern Distribution

### 6.1 Why Not Use Fixed 7.0?

The real paper distribution varies across different patterns: some themes generally have lower scores or stricter reviews; a fixed 7.0 would cause "deadlocks".

### 6.2 Scheme B (Default)

For the current `pattern_id`, use the score10 of **all papers** under that pattern to calculate:

* `q50`: Median line
* `q75`: Excellence line (Top 25%)

Passing Conditions:

* (A) At least **2 dimensions have score ≥ q75**
* AND (B) **avg_score ≥ q50**

Judgment and thresholds are written to:

* `critic_result['audit']['pass']`
* Also written to `events.jsonl` under `pass_threshold_computed`

Code Location:

* Quantile Calculation: `Paper-KG-Pipeline/scripts/pipeline/review_index.py`
* Pass Judgment: `Paper-KG-Pipeline/scripts/pipeline/critic.py` (`_compute_pass_decision`)

### 6.3 Fallback When Distribution Data is Insufficient

If the number of papers under the pattern is too small (default < 20):

* Default fallback to **global distribution** (q50/q75 of all papers globally).
* Can also be configured to fallback to a fixed `PASS_SCORE`.

---

## 7. How to Configure Strictness?

All of the following are controlled via environment variables (no code changes required).

### 7.1 Critic JSON Strict Mode (Most Critical)

| Configuration | Default | Meaning |
| --- | --- | --- |
| `I2P_CRITIC_STRICT_JSON` | `1` | 1=Strict: Retries on invalid JSON, terminates run if still fails; 0=Allows neutral fallback |
| `I2P_CRITIC_JSON_RETRIES` | `2` | Maximum retries after failure (Repair/Re-emit) |

Common Usage:

* Local smoke test without key: `I2P_CRITIC_STRICT_JSON=0`
* Quality pursuit: Keep `I2P_CRITIC_STRICT_JSON=1`, and configure `SILICONFLOW_API_KEY`

### 7.2 Passing Standard Strictness (Related to Scheme B)

| Configuration | Default | Meaning |
| --- | --- | --- |
| `I2P_PASS_MODE` | `two_of_three_q75_and_avg_ge_q50` | Currently implemented Scheme B; other values fallback to fixed PASS_SCORE |
| `I2P_PASS_MIN_PATTERN_PAPERS` | `20` | Triggers fallback when pattern paper count is below this value |
| `I2P_PASS_FALLBACK` | `global` | `global`=Use global distribution; `fixed`=Use fixed `PASS_SCORE` |

### 7.3 What is the Use of the Remaining `PASS_SCORE=7.0`?

`PASS_SCORE` is now a **last resort fallback**, used only if you configure `I2P_PASS_FALLBACK=fixed` or when distributions are unavailable.

---

## 8. How to Check Logs to Confirm "Fallback/Failure"?

Every run generates a directory: Repo root `log/run_YYYYMMDD_HHMMSS_<pid>_<rand>/`

Focus on:

* `events.jsonl`
  * Presence of `critic_fallback_neutral`: Indicates you allowed fallback (strict=0) and neutral fallback was triggered.
  * Presence of `critic_invalid_output_fatal`: Indicates strict=1 and JSON failure caused termination.
  * Presence of `pass_threshold_computed`: Records q50/q75, and pass judgment details.


* `llm_calls.jsonl`
  * `simulated=true`: No key, using simulated output.
  * `ok=false`: Call failed.



---

## 9. Common Run Commands (Suggested to Copy)

### 9.1 Local Smoke Test Without Key (Allows Fallback, Test Pipeline Only)

```bash
I2P_CRITIC_STRICT_JSON=0 python Paper-KG-Pipeline/scripts/idea2story_pipeline.py "test idea"
```

### 9.2 Quality Mode (Recommended: Strict + Real Benchmarking)

```bash
export SILICONFLOW_API_KEY="your_key"
I2P_CRITIC_STRICT_JSON=1 python Paper-KG-Pipeline/scripts/idea2story_pipeline.py "your idea"
```

### 9.3 Adjusting "Insufficient Data Fallback Strategy" for Passing Threshold

```bash
# Use global distribution when pattern data is insufficient (Default)
I2P_PASS_FALLBACK=global ...

# Fallback to fixed PASS_SCORE when pattern data is insufficient (More conservative)
I2P_PASS_FALLBACK=fixed ...
```

---

## 10. How to Troubleshoot "Why is the Score Always Around 6.x?"

Common Causes:

* LLM is not doing real work (No `SILICONFLOW_API_KEY` configured), or output JSON is invalid and intercepted/retried by strict mode.
* Or the story is indeed only around the "median" compared to anchors.

Troubleshooting Order:

1. Check `log/run_.../llm_calls.jsonl` for `simulated=true`.
2. Check `events.jsonl` for `critic_invalid_output` / `critic_fallback_neutral`.
3. Check `pass_threshold_computed` for q50/q75: q75 for many patterns might naturally be around 6.x (This is normal, depends on real distribution).