from fastapi import FastAPI

from apps.api.app.routers import alarms, work_orders
from apps.api.app.routers.health import router as health_router
from apps.api.app.routers.machines import router as machines_router

app = FastAPI(
    title="ManuAgent",
    version="0.141.1",
)


app.include_router(health_router)
app.include_router(machines_router)
app.include_router(alarms.router)
app.include_router(work_orders.router)