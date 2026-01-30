# Idea2Paper

把你的研究想法（Idea）自动变成“可投稿论文的 Story（论文叙事骨架）”的端到端流水线：**知识图谱召回 → Pattern 选择 → Story 生成 → 可标定 Multi-Agent Review（基于真实 review_stats）→ 迭代修正 → 查重验证 → 输出最终 Story**。

本仓库的核心实现位于 `Paper-KG-Pipeline/`，入口命令保持不变：
`python Paper-KG-Pipeline/scripts/idea2story_pipeline.py "your idea"`

## 核心特性（浓缩版）

- **知识图谱**：从 ICLR 2025 数据构建 `Idea/Pattern/Domain/Paper` 节点（当前导出：Idea 8,284 / Pattern 124 / Domain 98 / Paper 8,285）。
- **三路召回 + 两阶段加速**：Idea 相似 / Domain 泛化 / Paper 相似；粗排 Jaccard + 精排 Embedding。
- **Idea2Story 生成链路**：Pattern 选择 → Story 生成 → 评审 → 智能修正（含 Novelty 模式）→ RAG 查重与 Pivot。
- **Anchored Multi-Agent Review（可标定）**：用图谱真实 `review_stats` 作为标尺，LLM 只输出相对判断，分数由确定性算法拟合。
- **运行日志系统**：每次 run 独立目录，记录 events + LLM/embedding 调用输入输出，便于审计与回放。

---

## 你能得到什么（输出）

运行一次 pipeline 会生成：
- `Paper-KG-Pipeline/output/final_story.json`：最终 Story（标题/摘要/问题/方法/贡献/实验等结构化字段）
- `Paper-KG-Pipeline/output/pipeline_result.json`：完整链路结果（包含每轮评审、修正、查重、审计信息等）
- 仓库根 `log/run_.../`：每次运行的结构化日志（LLM/embedding 输入输出 + 关键事件）

---

## 快速开始（端到端）

### 0) 环境要求
- Python 3.10+（推荐）
- 安装依赖：`pip install -r Paper-KG-Pipeline/requirements.txt`

### 1) 准备数据（两种方式）

**方式 A（推荐，若仓库已带好 output 数据）**  
如果 `Paper-KG-Pipeline/output/` 下已存在以下文件，你可以直接跑生成链路：
- `nodes_idea.json / nodes_pattern.json / nodes_domain.json / nodes_paper.json`
- `edges.json`
- `knowledge_graph_v2.gpickle`

**方式 B（从原始数据重建知识图谱，只需一次）**  
确保 `Paper-KG-Pipeline/data/` 下有 ICLR 数据集（见 `Paper-KG-Pipeline/docs/01_KG_CONSTRUCTION.md` 的输入说明），然后执行：
```bash
python Paper-KG-Pipeline/scripts/build_entity_v3.py
python Paper-KG-Pipeline/scripts/build_edges.py
```

### 2) 配置（只改文件，不改代码）

本项目支持 **`.env` + `i2p_config.json`**，优先级固定为：
**shell export > 仓库根 `.env` > 仓库根 `i2p_config.json` > 代码默认值**

1) 复制 `.env`（放敏感 key + 常用开关）
```bash
cp .env.example .env
```
编辑 `.env`，填入你的 `SILICONFLOW_API_KEY`（不要提交到 git）。

2) （可选）复制用户配置文件（放非敏感参数）
```bash
cp i2p_config.example.json i2p_config.json
```

### 3) 运行
```bash
python Paper-KG-Pipeline/scripts/idea2story_pipeline.py "你的研究Idea描述"
```

常用模式：
- 本地无 key 冒烟（允许非严格兜底，更容易跑通）：在 `.env` 里设 `I2P_CRITIC_STRICT_JSON=0`
- 质量模式（推荐）：`SILICONFLOW_API_KEY` 有效 + `I2P_CRITIC_STRICT_JSON=1`

---

## Multi-Agent Review（可标定、可追溯）是什么？

传统“LLM 直接给 1~10 分”不可审计。本项目采用 **Anchored MultiAgentCritic**：

1) **真实标尺来自图谱数据**  
只使用 `Paper-KG-Pipeline/output/nodes_paper.json` 的 `review_stats`（真实均分/评审数/分歧）构造 `score10` 标尺。

2) **LLM 只做相对判断，不直接给分**  
给 LLM 一组“锚点论文”（anchors，含真实 `score10`），LLM 只输出：
`better|tie|worse + confidence + rationale(必须引用该 anchor 的 score10)`

3) **最终 1~10 分由确定性算法拟合得到**  
同一批 anchors + 同一份 comparisons JSON → 分数必定一致；并在 `audit` 中保留证据链：
`pattern_id + anchors(paper_id/title/score10/review_count/weight) + comparisons + loss -> score`

4) **通过标准（更客观）基于 pattern 全量真实分布**  
默认采用“方案B”：对当前 `pattern_id` 的全量论文 `score10` 分布计算 `q50/q75`：
- 三个维度至少 **2 个 ≥ q75**
- 且 **avg ≥ q50**
并把阈值与判定细节写入 `audit.pass` 和运行事件日志。

更详细解释见：`MULTIAGENT_REVIEW.md`

---

## 日志与调试（强烈建议看）

每次运行会创建目录：`log/run_YYYYMMDD_HHMMSS_<pid>_<rand>/`
- `meta.json`：运行元信息（idea/argv/入口等）
- `events.jsonl`：关键流程事件（召回、pattern 选择、每轮 critic、回滚/pivot、通过阈值等）
- `llm_calls.jsonl`：每次 LLM chat 的输入/输出/耗时/是否成功（不会记录 key 明文）
- `embedding_calls.jsonl`：每次 embedding 调用信息

常见排查：
- 分数总在 6.x：先看 `events.jsonl` 的 `pass_threshold_computed`（很多 pattern 的 q75 本来就在 6.x）
- 严格模式失败：看 `events.jsonl` 是否有 `critic_invalid_output_*`（JSON 校验失败会重试，仍失败直接终止）

---

## 配置说明（.env / i2p_config.json）

### `.env`（敏感信息 + 常用开关）
- `.env` 会在入口脚本启动时自动加载（不需要手动 export）
- **布尔值只认 `1/0`（只有 `1` 为 true）**
- 参考并复制：`.env.example`

最关键：
- `SILICONFLOW_API_KEY`：SiliconFlow API Key（LLM + embeddings）
- `I2P_CRITIC_STRICT_JSON`：评审 JSON 严格模式（1=质量优先；0=无 key 冒烟）

### `i2p_config.json`（非敏感集中配置）
- 参考并复制：`i2p_config.example.json`
- 适合放：pass 规则、日志目录、anchors 参数、LLM url/model 等
- 配置文件路径可用 env 指定：`I2P_CONFIG_PATH=/abs/path/to/i2p_config.json`

---

## 项目结构（工程化分层）

核心实现：
- `Paper-KG-Pipeline/src/idea2paper/`：库代码（infra/review/pipeline/recall）
入口脚本（命令不变）：
- `Paper-KG-Pipeline/scripts/idea2story_pipeline.py`：端到端 pipeline 入口
- `Paper-KG-Pipeline/scripts/simple_recall_demo.py`：仅召回 demo
数据/产物：
- `Paper-KG-Pipeline/output/`：图谱与运行产物（nodes/edges/graph/story/result）
- 仓库根 `log/`：每次 run 的审计日志

兼容层：
- `Paper-KG-Pipeline/scripts/pipeline/`：兼容 shim（旧 import 不断，新代码建议走 `src/idea2paper`）

---

## 更多文档（可选）

如果你需要更深的实现细节：
- `Paper-KG-Pipeline/docs/00_PROJECT_OVERVIEW.md`：整体架构与流程
- `Paper-KG-Pipeline/docs/01_KG_CONSTRUCTION.md`：知识图谱构建
- `Paper-KG-Pipeline/docs/02_RECALL_SYSTEM.md`：三路召回与两阶段优化
- `Paper-KG-Pipeline/docs/03_IDEA2STORY_PIPELINE.md`：生成/评审/修正/查重完整机制
