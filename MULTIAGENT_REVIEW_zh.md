# MultiAgentReview（基于图谱真实 Review 标尺）说明

[English](MULTIAGENT_REVIEW.md) | [简体中文](MULTIAGENT_REVIEW_zh.md)

本文档解释本仓库 `Paper-KG-Pipeline` 的 **MultiAgentReview / MultiAgentCritic** 思路：如何用图谱中的真实 `review_stats` 做“可标定”的客观标尺、如何计算最终分数、以及如何通过配置项调整“严格程度”（strictness）。

---

## 0. 快速结论（你需要记住的几句话）

- LLM **不再直接给 1~10 分**；它只输出“相对锚点论文更好/更差/持平 + 置信度 + 理由（必须引用锚点 score10）”。
- 最终 1~10 分是 **确定性算法**算出来的：同一批 anchors + 同一份 comparisons JSON → 分数必定一致。
- 通过标准不再是固定 7.0：默认采用 **方案B**（2/3 维度 ≥ q75 且 avg ≥ q50），q50/q75 来自该 pattern 下 **全部论文**的真实分布。
- 严格质量模式下：critic 的 JSON 不合格 → 自动重试 → 仍失败 **直接终止本次 run**，不允许随便给一个 6.x 兜底。

相关代码入口：
- Anchored Critic：`Paper-KG-Pipeline/scripts/pipeline/critic.py`
- Anchor/分布索引：`Paper-KG-Pipeline/scripts/pipeline/review_index.py`
- 配置：`Paper-KG-Pipeline/scripts/pipeline/config.py`
- 运行日志：仓库根目录 `log/run_.../`

---

## 1. MultiAgentReview 是什么？（三位评审 + 三个维度）

系统固定包含 3 个评审角色（multi-agent），每个角色输出一个维度分数：

- **Methodology**：方法是否合理、技术细节是否严谨、实验是否可信
- **Novelty**：创新性是否扎实，是否只是常见堆叠
- **Storyteller**：叙事是否完整（动机→方法→实验→结论是否闭环）

最后输出：
- 每个角色的 `score`（1~10）
- `avg_score`（三个角色平均）
- `main_issue`（最低分角色映射到 `novelty / stability / domain_distance`）
- `audit`（审计信息：anchors、comparisons、loss、通过阈值与判定细节）

---

## 2. “客观标尺”来自哪里？（真实 review_stats → score10）

### 2.1 数据来源
只使用图谱导出的论文节点数据：
- `Paper-KG-Pipeline/output/nodes_paper.json`
  - 每篇 paper 带 `review_stats`：`avg_score`、`review_count`、`highest_score`、`lowest_score` 等。

### 2.2 score10 与权重（weight）
在 `ReviewIndex` 中会把真实统计映射成 1~10 标尺：

- `score10 = 1 + 9 * avg_score`
- `dispersion10 = 9 * (highest_score - lowest_score)`（分歧越大越不可靠）
- `weight = log(1 + review_count) / (1 + dispersion10)`（评论越多越可信；分歧越大权重越小）

这些值会被缓存为 `paper_summary`，并用于：
- 选锚点（anchors）
- 拟合最终分数（加权 loss）

---

## 3. Anchor（锚点论文）怎么选？为什么不是全给？

把某个 pattern 下所有论文都塞给 LLM 会导致上下文爆炸、成本高、输出不稳定。正确做法：

- **离线/索引层**：使用该 pattern 下“全部论文”计算分布（q50/q75 等）
- **在线/LLM 对标**：只给 5~9 篇锚点论文做对标

当前策略（固定 5 + 自适应加密到 9）：

1) 固定锚点（最稳、可复现）
   - 取该 pattern 下 `score10` 的分位点：q10/q25/q50/q75/q90（5 篇）
2) 可选 exemplar（如果 pattern_info 含 exemplar_paper_ids）
   - 额外补 0~2 篇最可靠 exemplar（按 weight/review_count 排序）
3) 自适应加密（必要时补齐到最多 9 篇）
   - 如果第一轮拟合不稳定（loss 大、置信度低、或对标不单调），就在当前估计分数附近补 2~4 篇更“贴近分数”的论文再对标一次

代码位置：`Paper-KG-Pipeline/scripts/pipeline/review_index.py`

---

## 4. LLM 在评审里到底做什么？（只做相对判断）

### 4.1 LLM 输出格式（comparisons）
每个角色会收到同一组 anchors（含真实 `score10`），LLM 必须返回 JSON：

- 对每篇 anchor 给出：`better / tie / worse` + `confidence(0~1)` + `rationale`
- rationale 必须包含对应锚点的 `score10: X.X`

LLM **不允许**输出最终分数。

### 4.2 从 comparisons 到概率 p_i（确定性映射）
把 judgement/confidence 映射成概率（“击败该锚点”的概率）：

- better: `p = 0.5 + 0.45 * confidence`
- tie:    `p = 0.5`
- worse:  `p = 0.5 - 0.45 * confidence`

直觉：confidence 越高，p 离 0.5 越远；tie 永远是 0.5。

---

## 5. 最终 1~10 分怎么计算？（确定性拟合）

目标：找到一个分数 S，使得对于每个锚点分数 s_i，模型预测的“胜率”接近 LLM 给的 p_i。

- 预测胜率：`sigmoid(k*(S - s_i))`
- k 为常量（默认 1.2）
- 用加权最小二乘拟合：
  - `loss(S) = Σ w_i * (sigmoid(k*(S-s_i)) - p_i)^2`
- 在 `S ∈ [1,10]` 上网格搜索（步长默认 0.01），取 loss 最小的 S

这一步完全确定性：同一 anchors + 同一 comparisons → 得到的 S 必定一致。

代码位置：`Paper-KG-Pipeline/scripts/pipeline/critic.py`（`_compute_score_from_comparisons`）

---

## 6. 通过标准（方案B）：相对 pattern 全量分布

### 6.1 为什么不用固定 7.0？
不同 pattern 的真实论文分布不同：有的主题整体分低、审稿更严；固定 7.0 会“卡死”。

### 6.2 方案B（默认）
对当前 `pattern_id`，用该 pattern 下 **全部论文**的 score10 计算：
- `q50`：中位线
- `q75`：优秀线（前 25%）

通过条件：
- (A) 三个维度里至少 **2 个维度 score ≥ q75**
- 且 (B) **avg_score ≥ q50**

判定与阈值会写入：
- `critic_result['audit']['pass']`
- 同时写入 `events.jsonl` 的 `pass_threshold_computed`

代码位置：
- 分位数计算：`Paper-KG-Pipeline/scripts/pipeline/review_index.py`
- 通过判定：`Paper-KG-Pipeline/scripts/pipeline/critic.py`（`_compute_pass_decision`）

### 6.3 分布数据不足时的回退
如果该 pattern 下论文数量太少（默认 < 20）：
- 默认回退到 **global 分布**（全局所有论文的 q50/q75）
- 也可配置回退到固定 `PASS_SCORE`

---

## 7. 严格程度（strictness）如何配置？

下面这些都通过环境变量控制（不需要改代码）。

### 7.1 Critic JSON 严格模式（最关键）
| 配置 | 默认 | 含义 |
|---|---:|---|
| `I2P_CRITIC_STRICT_JSON` | `1` | 1=严格：JSON 不合格会重试，仍失败直接终止 run；0=允许中性兜底 |
| `I2P_CRITIC_JSON_RETRIES` | `2` | 失败后的最大重试次数（Repair/Re-emit） |

常用：
- 本地无 key 冒烟跑通链路：`I2P_CRITIC_STRICT_JSON=0`
- 追求质量：保持 `I2P_CRITIC_STRICT_JSON=1`，并配置 `SILICONFLOW_API_KEY`

### 7.2 通过标准严格程度（方案B相关）
| 配置 | 默认 | 含义 |
|---|---:|---|
| `I2P_PASS_MODE` | `two_of_three_q75_and_avg_ge_q50` | 目前实现的方案B；其它值会退回固定 PASS_SCORE |
| `I2P_PASS_MIN_PATTERN_PAPERS` | `20` | pattern 论文数少于该值时触发 fallback |
| `I2P_PASS_FALLBACK` | `global` | `global`=用全局分布；`fixed`=用固定 `PASS_SCORE` |

### 7.3 仍保留的 `PASS_SCORE=7.0` 有什么用？
`PASS_SCORE` 现在是**最后兜底**，只在你配置 `I2P_PASS_FALLBACK=fixed` 或分布不可用时使用。

---

## 8. 怎么看日志确认“有没有兜底/失败”？

每次 run 会生成目录：仓库根 `log/run_YYYYMMDD_HHMMSS_<pid>_<rand>/`

重点看：
- `events.jsonl`
  - 有 `critic_fallback_neutral`：说明你允许兜底（strict=0）且触发了中性兜底
  - 有 `critic_invalid_output_fatal`：说明 strict=1 且 JSON 失败导致终止
  - 有 `pass_threshold_computed`：记录 q50/q75、通过判定细节
- `llm_calls.jsonl`
  - `simulated=true`：没有 key，走模拟输出
  - `ok=false`：调用失败

---

## 9. 常用运行命令（建议复制）

### 9.1 本地无 key 冒烟（允许兜底，只测链路）
```bash
I2P_CRITIC_STRICT_JSON=0 python Paper-KG-Pipeline/scripts/idea2story_pipeline.py "test idea"
```

### 9.2 质量模式（推荐：严格 + 真实对标）
```bash
export SILICONFLOW_API_KEY="你的key"
I2P_CRITIC_STRICT_JSON=1 python Paper-KG-Pipeline/scripts/idea2story_pipeline.py "your idea"
```

### 9.3 调整通过门槛的“数据不足回退策略”
```bash
# pattern 数据不足时用 global 分布（默认）
I2P_PASS_FALLBACK=global ...

# pattern 数据不足时回退固定 PASS_SCORE（更保守）
I2P_PASS_FALLBACK=fixed ...
```

---

## 10. 你遇到“为什么分数总在 6.x？”时该怎么排查？

常见原因：
- LLM 没有真实工作（没有配置 `SILICONFLOW_API_KEY`），或者输出 JSON 不合格被 strict 拦截/重试
- 或者 story 与锚点相比确实只在“中位附近”

排查顺序：
1) 看 `log/run_.../llm_calls.jsonl` 是否有 `simulated=true`
2) 看 `events.jsonl` 是否出现 `critic_invalid_output` / `critic_fallback_neutral`
3) 看 `pass_threshold_computed` 的 q50/q75：很多 pattern 的 q75 可能就在 6.x（这很正常，取决于真实分布）

