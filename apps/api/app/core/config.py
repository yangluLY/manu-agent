from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 项目根目录：
# manu-agent/
BASE_DIR = Path(__file__).resolve().parents[4]

class Settings(BaseSettings):
    """
    应用配置。

    配置优先从系统环境变量读取，
    如果系统环境变量不存在，则读取项目根目录下的 .env 文件。
    """

    # -------------------------
    # Application
    # -------------------------

    app_name: str = "ManuAgent"
    app_env: str = "development"
    app_debug: bool = True

    # -------------------------
    # PostgreSQL
    # -------------------------

    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "manu_agent"
    database_user: str = "manu"
    database_password: str = "dev_password"

    @property
    def database_url(self) -> str:
        """
        SQLAlchemy 使用的 PostgreSQL 连接地址。
        """

        return (
            f"postgresql+psycopg://"
            f"{self.database_user}:"
            f"{self.database_password}@"
            f"{self.database_host}:"
            f"{self.database_port}/"
            f"{self.database_name}"
        )

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
