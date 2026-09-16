from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from apps.api.app.core.exceptions import DatabaseUnavailableException
from services.database.session import get_db

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("")
def health_check():
    return {
        "status": "ok",
    }


@router.get("/db")
def database_health_check(
    db: Session = Depends(get_db),
):
    try:
        result = db.execute(text("SELECT 1"))
        value = result.scalar()

        return {
            "status": "ok",
            "database": "connected",
            "result": value,
        }

    except SQLAlchemyError as exc:
        raise DatabaseUnavailableException() from exc
