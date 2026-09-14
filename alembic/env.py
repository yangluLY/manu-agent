from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# 我们自己的项目配置
from apps.api.app.core.config import settings

# ORM Base
from services.database.base import Base

# 一定要导入 Model
# 否则 Base.metadata 可能不知道 Machine 存在
from services.database.models.machine import Machine  # noqa: F401

config = context.config


if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# 告诉 Alembic：
# 数据库连接地址使用项目 .env 中的配置
config.set_main_option(
    "sqlalchemy.url",
    settings.database_url,
)


# 告诉 Alembic：
# ORM 的表结构都放在 Base.metadata 里
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()