from fastapi import FastAPI

from app.driver.routes import router as driver_router
from app.auth.routes import router as auth_router

app = FastAPI(
    title="ChargeMate AI Backend"
)


@app.get("/")
def root():
    return {
        "message": "Welcome to ChargeMate AI Backend"
    }


# Driver APIs
app.include_router(driver_router)

# Authentication APIs
app.include_router(auth_router)