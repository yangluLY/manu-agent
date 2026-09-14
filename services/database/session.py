from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from apps.api.app.core.config import settings

# 1. 创建 SQLAlchemy Engine
#
# Engine 可以理解为：
# Python 应用连接 PostgreSQL 的“数据库连接管理器”。
#
# 它内部还会维护数据库连接池。
engine = create_engine(
    settings.database_url,
    echo=settings.app_debug,
    pool_pre_ping=True,
)


# 2. 创建 Session 工厂
#
# SessionLocal 本身不是数据库连接，
# 它是用来创建 Session 的“工厂”。
SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    expire_on_commit=False,
)


# 3. FastAPI 数据库依赖
#
# 每次 HTTP 请求需要访问数据库时：
#
# 创建 Session
#     ↓
# Router / Service 使用 Session
#     ↓
# 请求结束
#     ↓
# 自动关闭 Session
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()