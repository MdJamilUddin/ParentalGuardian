from datetime import datetime, timezone

from sqlalchemy import (Boolean, CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, String,
                        UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Parent(Base):
    __tablename__ = "parents"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    children: Mapped[list["Child"]] = relationship(back_populates="parent", cascade="all, delete-orphan")


class Child(Base):
    __tablename__ = "children"
    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[int] = mapped_column(ForeignKey("parents.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    parent: Mapped[Parent] = relationship(back_populates="children")
    devices: Mapped[list["Device"]] = relationship(back_populates="child", cascade="all, delete-orphan")


class Device(Base):
    __tablename__ = "devices"
    id: Mapped[int] = mapped_column(primary_key=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("children.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    paired_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    child: Mapped[Child] = relationship(back_populates="devices")


class PairingCode(Base):
    __tablename__ = "pairing_codes"
    id: Mapped[int] = mapped_column(primary_key=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("children.id", ondelete="CASCADE"), index=True)
    code_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    used: Mapped[bool] = mapped_column(Boolean, default=False)


class LocationPoint(Base):
    __tablename__ = "location_points"
    __table_args__ = (
        Index("ix_location_device_time", "device_id", "recorded_at"),
        CheckConstraint("lat BETWEEN -90 AND 90", name="ck_location_lat"),
        CheckConstraint("lng BETWEEN -180 AND 180", name="ck_location_lng"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"))
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    accuracy_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime)


class UsageRecord(Base):
    __tablename__ = "usage_records"
    __table_args__ = (
        UniqueConstraint("device_id", "package", "day"),
        Index("ix_usage_device_day", "device_id", "day"),
        CheckConstraint("seconds BETWEEN 0 AND 86400", name="ck_usage_seconds"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"))
    package: Mapped[str] = mapped_column(String(255))
    app_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    day: Mapped[str] = mapped_column(String(10))  # YYYY-MM-DD (the child's local date)
    seconds: Mapped[int] = mapped_column(Integer)


class BatteryReading(Base):
    __tablename__ = "battery_readings"
    __table_args__ = (
        Index("ix_battery_device_time", "device_id", "recorded_at"),
        CheckConstraint("level BETWEEN 0 AND 100", name="ck_battery_level"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"))
    level: Mapped[int] = mapped_column(Integer)
    charging: Mapped[bool] = mapped_column(Boolean, default=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime)
