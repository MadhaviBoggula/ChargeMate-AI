from datetime import datetime
from decimal import Decimal
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Charger(Base):
    __tablename__ = "chargers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("charging_stations.id", ondelete="CASCADE"), nullable=False, index=True)
    charger_code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    connector_type: Mapped[str] = mapped_column(String(50), nullable=False)
    charging_type: Mapped[str] = mapped_column(String(2), nullable=False)  # AC / DC
    power_kw: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    availability: Mapped[str] = mapped_column(String(20), nullable=False, default="available")
    price_per_kwh: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    station: Mapped["ChargingStation"] = relationship(back_populates="chargers")
