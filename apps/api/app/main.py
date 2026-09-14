from fastapi import FastAPI

from apps.api.app.routers import (
    alarms,
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
app.include_router(alarms.router)
app.include_router(work_orders.router)
app.include_router(materials.router)
app.include_router(production_records.router)