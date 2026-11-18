from fastapi import FastAPI

from app.driver.routes import router as driver_router
from app.stations.routes import router as station_router
from app.bookings.routes import router as booking_router
from app.auth.routes import router as auth_router
from app.ai.routes import router as ai_router
from app.simulation.routes import router as simulation_router
from app.recommendations.routes import router as recommendation_router


app = FastAPI(
    title="ChargeMate AI Backend"
)


@app.get("/")
def root():
    return {
        "message": "Welcome to ChargeMate AI Backend"
    }


# Register Routers
app.include_router(driver_router)
app.include_router(station_router)
app.include_router(booking_router)
app.include_router(auth_router)
app.include_router(ai_router)
app.include_router(simulation_router)
app.include_router(recommendation_router)