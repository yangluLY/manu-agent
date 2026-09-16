import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# ============================================================
# 把项目根目录加入 Python Path
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# 现在再导入项目代码
# ============================================================

from apps.api.app.main import app
from services.database.base import Base
from services.database.models.alarm import MachineAlarm
from services.database.models.machine import Machine
from services.database.models.material import Material
from services.database.models.production_record import ProductionRecord
from services.database.models.work_order import WorkOrder
from services.database.session import get_db

# ============================================================
# Test Database
# ============================================================

TEST_DATABASE_URL = "sqlite://"


engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
    poolclass=StaticPool,
)


TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ============================================================
# Database Fixture
# ============================================================

@pytest.fixture(scope="function")
def db_session():

    Base.metadata.create_all(
        bind=engine
    )

    db = TestingSessionLocal()

    try:
        yield db

    finally:
        db.close()

        Base.metadata.drop_all(
            bind=engine
        )


# ============================================================
# FastAPI Test Client
# ============================================================

@pytest.fixture(scope="function")
def client(db_session):

    def override_get_db():

        try:
            yield db_session

        finally:
            pass

    app.dependency_overrides[
        get_db
    ] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()