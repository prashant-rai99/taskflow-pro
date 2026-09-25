"""
Pydantic schemas -- define the shape of data going in/out of the API.
Kept separate from SQLAlchemy models (app/models.py) so we control
exactly what a client can send and what we expose back.
"""

from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

# ---------- Task schemas ----------

VALID_COLUMNS = {"backlog", "in_progress", "review", "done"}


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    column: str = Field(default="backlog")
    position: int = Field(default=0)
    planned_start: date
    duration_days: int = Field(..., gt=0)

    @field_validator("column")
    @classmethod
    def validate_column(cls, v):
        if v not in VALID_COLUMNS:
            raise ValueError(f"column must be one of {VALID_COLUMNS}")
        return v


class TaskUpdate(BaseModel):
    """All fields optional -- used for partial updates (e.g. just moving column)."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    column: Optional[str] = None
    position: Optional[int] = None
    planned_start: Optional[date] = None
    duration_days: Optional[int] = Field(None, gt=0)

    @field_validator("column")
    @classmethod
    def validate_column(cls, v):
        if v is not None and v not in VALID_COLUMNS:
            raise ValueError(f"column must be one of {VALID_COLUMNS}")
        return v


class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    column: str
    position: int
    planned_start: date
    duration_days: int
    created_at: datetime
    updated_at: datetime

    # These two are NOT stored -- they're computed live by the engine
    # (schedule.py + status.py) and attached at response time.
    computed_start: Optional[date] = None
    computed_end: Optional[date] = None
    status: Optional[str] = None  # "ready" | "blocked"

    class Config:
        from_attributes = True  # allows building this from a SQLAlchemy object


# ---------- Dependency schemas ----------


class DependencyCreate(BaseModel):
    task_id: int
    prerequisite_id: int

    @field_validator("prerequisite_id")
    @classmethod
    def no_self_reference(cls, v, info):
        if "task_id" in info.data and v == info.data["task_id"]:
            raise ValueError("a task cannot depend on itself")
        return v


class DependencyOut(BaseModel):
    id: int
    task_id: int
    prerequisite_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Error response (used for cycle rejection etc.) ----------


class ErrorResponse(BaseModel):
    detail: str


# ---------- Board (combined view) ----------


class BoardResponse(BaseModel):
    tasks: List[TaskOut]
    dependencies: List[DependencyOut]
