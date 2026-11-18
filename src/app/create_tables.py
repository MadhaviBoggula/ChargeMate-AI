from app.database.database import Base, engine

# Import all models
from app.driver.models import *
from app.bookings.models import *
from app.auth.models import *

print("Creating tables...")

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

print("Done!")