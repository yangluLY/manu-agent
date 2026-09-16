from fastapi import FastAPI

from apps.api.app.core.exception_handlers import (
    app_exception_handler,
)
from apps.api.app.core.exceptions import (
    AppException,
)
from apps.api.app.routers import (
    alarms,
    machines,
    materials,
    production_records,
    work_orders,
)
from apps.api.app.routers.health import router as health_router

app = FastAPI(
    title="ManuAgent",
    version="0.141.1",
)


app.include_router(health_router)
app.include_router(machines.router)
app.include_router(alarms.router)
app.include_router(work_orders.router)
app.include_router(materials.router)
app.include_router(production_records.router)

app.add_exception_handler(
    AppException,
    app_exception_handler,
)