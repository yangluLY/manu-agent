
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import declarative_base  # noqa: F401

# 如果项目已有统一 Base，改成导入现有 Base。
from services.database.base import Base


class User(Base):
    __tablename__ = "auth_users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(
        String(80),
        nullable=False,
        unique=True,
        index=True,
    )

    password_hash = Column(
        String(512),
        nullable=False,
    )

    # viewer：普通用户
    # workflow_approver：工作流审批员
    role = Column(
        String(40),
        nullable=False,
        default="viewer",
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
