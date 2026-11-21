from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel

CONNECTOR_STATUSES = ("active", "inactive", "faulted")


class Connector(BaseModel):
    """A supported connector type exposed by a charger."""

    __tablename__ = "connectors"

    __table_args__ = (
        UniqueConstraint(
            "charger_id",
            "connector_type",
            name="uq_connectors_charger_type",
        ),
        CheckConstraint(
            "power_kw > 0",
            name="connector_power_positive",
        ),
        CheckConstraint(
            "status IN ('active', 'inactive', 'faulted')",
            name="connector_status_valid",
        ),
    )

    charger_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chargers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    connector_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    power_kw: Mapped[Decimal] = mapped_column(
        Numeric(8, 2),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        server_default="active",
        nullable=False,
        index=True,
    )

    charger: Mapped["Charger"] = relationship(
        "Charger",
        back_populates="connectors",
    )
