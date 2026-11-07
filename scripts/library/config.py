import os
from dataclasses import dataclass
from pathlib import Path

from psycopg.conninfo import conninfo_to_dict

REQUIRED_ENV = ("UNION_SEARCH_LIBRARY_DIR", "UNION_SEARCH_PG_DSN", "UNION_SEARCH_ES_URL", "UNION_SEARCH_ES_API_KEY", "UNION_SEARCH_ES_INDEX")


class LibraryNotConfigured(RuntimeError):
    pass


@dataclass(frozen=True)
class LibraryConfig:
    root: Path
    pg_dsn: str
    es_url: str
    es_api_key: str
    es_index: str

    @property
    def bodies_dir(self) -> Path:
        return self.root / "bodies"

    @property
    def logs_dir(self) -> Path:
        return self.root / "logs"

    @property
    def staging_dir(self) -> Path:
        return self.root / "staging"

    def public(self) -> dict:
        # 只输出位置信息，不输出凭据
        return {"root": str(self.root), "es_url": self.es_url, "es_index": self.es_index, "pg": _dsn_location(self.pg_dsn)}


def _dsn_location(dsn: str) -> str:
    # URL 和 key=value 两种写法都只取主机、端口与数据库名
    params = conninfo_to_dict(dsn)
    return f"{params.get('host', '')}:{params.get('port', '5432')}/{params.get('dbname', '')}"


def missing_env() -> list:
    return [key for key in REQUIRED_ENV if not os.getenv(key)]


def load_config() -> LibraryConfig:
    missing = missing_env()
    if missing:
        raise LibraryNotConfigured("长期资料库未配置，缺少环境变量: " + ", ".join(missing))
    root = Path(os.environ["UNION_SEARCH_LIBRARY_DIR"]).expanduser()
    if not root.is_absolute():
        raise LibraryNotConfigured("UNION_SEARCH_LIBRARY_DIR 必须是绝对路径")
    config = LibraryConfig(root, os.environ["UNION_SEARCH_PG_DSN"], os.environ["UNION_SEARCH_ES_URL"], os.environ["UNION_SEARCH_ES_API_KEY"],
                           os.environ["UNION_SEARCH_ES_INDEX"])
    for directory in (config.root, config.bodies_dir, config.logs_dir, config.staging_dir):
        directory.mkdir(parents=True, exist_ok=True)
    return config
