import os
from pathlib import Path

# ===================== 路径配置 =====================
# scripts/pipeline/config.py -> scripts/pipeline -> scripts -> Paper-KG-Pipeline
CURRENT_DIR = Path(__file__).parent
PROJECT_ROOT = CURRENT_DIR.parent.parent
REPO_ROOT = PROJECT_ROOT.parent
OUTPUT_DIR = PROJECT_ROOT / "output"

# ===================== LLM API 配置 =====================
LLM_API_KEY = os.getenv("SILICONFLOW_API_KEY", "")
LLM_API_URL = os.getenv("LLM_API_URL", "https://api.siliconflow.cn/v1/chat/completions")
LLM_MODEL = os.getenv("LLM_MODEL", "Pro/zai-org/GLM-4.7")

# ===================== Run Logging 配置 =====================
LOG_ROOT = Path(os.getenv("I2P_LOG_DIR", str(REPO_ROOT / "log")))
ENABLE_RUN_LOGGING = os.getenv("I2P_ENABLE_LOGGING", "1") == "1"
LOG_MAX_TEXT_CHARS = int(os.getenv("I2P_LOG_MAX_TEXT_CHARS", "20000"))

# ===================== Pipeline 配置 =====================
class PipelineConfig:
    """Pipeline 配置参数"""
    # Pattern 选择
    SELECT_PATTERN_COUNT = 3  # 选择 3 个不同策略的 Pattern
    CONSERVATIVE_RANK_RANGE = (0, 2)  # 稳健型: Rank 1-3
    INNOVATIVE_CLUSTER_SIZE_THRESHOLD = 10  # 创新型: Cluster Size < 10

    # Critic 阈值
    PASS_SCORE = 7.0  # 评分 >= 7 为通过
    MAX_REFINE_ITERATIONS = 3  # 最多修正 3 轮

    # Pass mode (pattern-aware)
    PASS_MODE = os.getenv("I2P_PASS_MODE", "two_of_three_q75_and_avg_ge_q50")
    PASS_MIN_PATTERN_PAPERS = int(os.getenv("I2P_PASS_MIN_PATTERN_PAPERS", "20"))
    PASS_FALLBACK = os.getenv("I2P_PASS_FALLBACK", "global")  # global|fixed

    # 新颖性模式配置
    NOVELTY_MODE_MAX_PATTERNS = 3  # 新颖性模式最多尝试的 Pattern 数
    NOVELTY_SCORE_THRESHOLD = 6.0  # 新颖性得分阈值

    # RAG 查重阈值
    COLLISION_THRESHOLD = 0.75  # 相似度 > 0.75 认为撞车

    # Refinement 策略
    TAIL_INJECTION_RANK_RANGE = (4, 9)  # 长尾注入: Rank 5-10
    HEAD_INJECTION_RANK_RANGE = (0, 2)  # 头部注入: Rank 1-3
    HEAD_INJECTION_CLUSTER_THRESHOLD = 15  # 头部注入: Cluster Size > 15

    # Anchored Critic 配置
    ANCHOR_QUANTILES = [0.1, 0.25, 0.5, 0.75, 0.9]
    ANCHOR_MAX_INITIAL = 7
    ANCHOR_MAX_TOTAL = 9
    ANCHOR_MAX_EXEMPLARS = 2
    DENSIFY_OFFSETS = [-0.5, 0.5, -0.25, 0.25]
    SIGMOID_K = 1.2
    GRID_STEP = 0.01
    DENSIFY_LOSS_THRESHOLD = 0.03
    DENSIFY_MIN_AVG_CONF = 0.45

    # Critic JSON reliability (quality-first)
    CRITIC_STRICT_JSON = os.getenv("I2P_CRITIC_STRICT_JSON", "1") == "1"
    CRITIC_JSON_RETRIES = int(os.getenv("I2P_CRITIC_JSON_RETRIES", "2"))
