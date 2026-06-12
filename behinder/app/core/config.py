"""
核心配置模块 — 读取 .env 文件，全局单例
"""
import json
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import field_validator

# 项目根目录（behinder/ 的上级目录，即包含 agent_rag/fronter/behinder/ 的目录）
# __file__ = behinder/app/core/config.py → parent×4 = 项目根目录
_PROJ_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_DATA_DIR = _PROJ_ROOT / "data"
PROJECT_ROOT = _PROJ_ROOT  # 公开导出，供其他模块使用


class Settings(BaseSettings):
    # ---- LLM ----
    openai_api_key: str = "sk-placeholder"
    openai_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_model: str = "qwen-plus"
    embedding_model: str = "text-embedding-v2"

    # ---- Database ----
    # Windows 绝对路径用 3 个斜杠（4 个斜杠仅用于 Unix 绝对路径 /home/...）
    _db_path = str(_DATA_DIR / "app.db").replace("\\", "/")
    database_url: str = f"sqlite+aiosqlite:///{_db_path}"

    # ---- Chroma ----
    chroma_persist_dir: str = str(_DATA_DIR / "chroma")

    # ---- BM25 ----
    bm25_index_dir: str = str(_DATA_DIR / "bm25")

    # ---- Reranker ----
    reranker_model: str = "qwen3-rerank"

    # ---- RAG 参数 ----
    chunk_size: int = 512
    chunk_overlap: int = 64
    bm25_top_k: int = 10
    vector_top_k: int = 10
    rerank_top_k: int = 5

    # ---- 服务 ----
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return [v]
        return v

    model_config = {
        "env_file": str(_PROJ_ROOT / "behinder" / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()

# 确保数据目录存在
for _dir in [settings.chroma_persist_dir, settings.bm25_index_dir, str(_DATA_DIR)]:
    Path(_dir).mkdir(parents=True, exist_ok=True)
