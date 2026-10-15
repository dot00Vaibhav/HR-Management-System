"""Validated request models for the public API."""

from typing import Literal

from fastapi import HTTPException
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    field_validator,
    model_validator,
)

from .attendance_rules import hm, valid_date, valid_instant


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="ignore")


class EmployeeIn(StrictModel):
    emp_code: str = Field(pattern=r"^EMP\d{4,6}$")
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(max_length=120, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    department: str = Field(min_length=1, max_length=50)
    shift_start: str = "09:30"
    shift_end: str = "18:30"
    joined_on: str

    @field_validator("shift_start", "shift_end")
    @classmethod
    def shift_time(cls, v):
        hm(v)
        return v

    @field_validator("joined_on")
    @classmethod
    def date_value(cls, v):
        try:
            return valid_date(v)
        except HTTPException as exc:
            raise ValueError(exc.detail)

    @model_validator(mode="after")
    def shifts_differ(self):
        if self.shift_start == self.shift_end:
            raise ValueError("shift_start and shift_end must differ")
        return self


class PunchInIn(StrictModel):
    emp_code: str
    punched_at: StrictInt | None = None
    status: Literal["PRESENT", "WFH", "ON_DUTY"] = "PRESENT"

    @model_validator(mode="before")
    @classmethod
    def reject_null_timestamp(cls, value):
        if (
            isinstance(value, dict)
            and "punched_at" in value
            and value["punched_at"] is None
        ):
            raise ValueError(
                "punched_at must be omitted or an epoch-millisecond integer"
            )
        return value

    @field_validator("punched_at")
    @classmethod
    def timestamp(cls, v):
        return valid_instant(v)


class PunchOutIn(StrictModel):
    emp_code: str
    punched_at: StrictInt | None = None

    @model_validator(mode="before")
    @classmethod
    def reject_null_timestamp(cls, value):
        if (
            isinstance(value, dict)
            and "punched_at" in value
            and value["punched_at"] is None
        ):
            raise ValueError(
                "punched_at must be omitted or an epoch-millisecond integer"
            )
        return value

    @field_validator("punched_at")
    @classmethod
    def timestamp(cls, v):
        return valid_instant(v)


class RegularizeIn(StrictModel):
    status: Literal["PRESENT", "WFH", "ON_DUTY", "ABSENT", "LEAVE"] | None = None
    punch_in: StrictInt | None = None
    punch_out: StrictInt | None = None
    reason: str = Field(min_length=5, max_length=200)
    regularized_by: str = Field(min_length=1, max_length=50)

    @model_validator(mode="before")
    @classmethod
    def reject_null_patch_values(cls, value):
        if isinstance(value, dict):
            for key in ("status", "punch_in", "punch_out"):
                if key in value and value[key] is None:
                    raise ValueError(f"{key} cannot be null")
        return value

    @field_validator("punch_in", "punch_out")
    @classmethod
    def timestamp(cls, v):
        return valid_instant(v)
