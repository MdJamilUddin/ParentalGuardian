from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterIn(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128)
    accepted_terms: bool

    @field_validator("accepted_terms")
    @classmethod
    def must_accept(cls, v: bool) -> bool:
        if not v:
            raise ValueError("You must accept the privacy policy and terms")
        return v


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChildIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class DeviceOut(BaseModel):
    id: int
    name: str
    revoked: bool
    paired_at: datetime
    last_seen: datetime | None
    model_config = {"from_attributes": True}


class ChildOut(BaseModel):
    id: int
    name: str
    devices: list[DeviceOut] = []
    model_config = {"from_attributes": True}


class PairingCodeOut(BaseModel):
    code: str
    expires_at: datetime


class PairIn(BaseModel):
    code: str = Field(min_length=6, max_length=6)
    device_name: str = Field(min_length=1, max_length=100)


class PairOut(BaseModel):
    device_id: int
    device_token: str


class LocationIn(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    accuracy_m: float | None = None
    recorded_at: datetime


class UsageIn(BaseModel):
    package: str = Field(max_length=255)
    app_label: str | None = None
    day: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    seconds: int = Field(ge=0, le=86400)


class BatteryIn(BaseModel):
    level: int = Field(ge=0, le=100)
    charging: bool = False
    recorded_at: datetime


class SyncIn(BaseModel):
    locations: list[LocationIn] = Field(default_factory=list, max_length=500)
    usage: list[UsageIn] = Field(default_factory=list, max_length=500)
    battery: list[BatteryIn] = Field(default_factory=list, max_length=500)


class SyncOut(BaseModel):
    accepted_locations: int
    accepted_usage: int
    accepted_battery: int
    server_time: datetime


class LocationOut(BaseModel):
    lat: float
    lng: float
    accuracy_m: float | None
    recorded_at: datetime
    model_config = {"from_attributes": True}


class UsageOut(BaseModel):
    package: str
    app_label: str | None
    day: str
    seconds: int
    model_config = {"from_attributes": True}


class BatteryOut(BaseModel):
    level: int
    charging: bool
    recorded_at: datetime
    model_config = {"from_attributes": True}
