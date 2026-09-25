from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    func,
)
from sqlalchemy.orm import relationship
from app.db import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    column = Column(String(20), nullable=False, default="backlog")
    position = Column(Integer, nullable=False, default=0)
    planned_start = Column(Date, nullable=False)
    duration_days = Column(Integer, nullable=False, default=1)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(
            "column IN ('backlog','in_progress','review','done')",
            name="ck_task_column_valid",
        ),
        CheckConstraint("duration_days > 0", name="ck_duration_positive"),
    )

    dependencies = relationship(
        "Dependency",
        foreign_keys="Dependency.task_id",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    dependents = relationship(
        "Dependency",
        foreign_keys="Dependency.prerequisite_id",
        back_populates="prerequisite",
        cascade="all, delete-orphan",
    )


class Dependency(Base):
    __tablename__ = "dependencies"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    prerequisite_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    task = relationship("Task", foreign_keys=[task_id], back_populates="dependencies")
    prerequisite = relationship(
        "Task", foreign_keys=[prerequisite_id], back_populates="dependents"
    )

    __table_args__ = (
        UniqueConstraint("task_id", "prerequisite_id", name="uq_task_prereq_pair"),
        CheckConstraint("task_id != prerequisite_id", name="ck_no_self_reference"),
    )


class AISuggestion(Base):
    __tablename__ = "ai_suggestions"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    suggested_prerequisite_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    reason = Column(Text, nullable=False)
    evidence = Column(Text, nullable=False)
    confidence = Column(Integer, nullable=False)
    provider = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "confidence >= 0 AND confidence <= 100", name="ck_confidence_range"
        ),
        CheckConstraint(
            "status IN ('pending','approved','rejected')",
            name="ck_suggestion_status_valid",
        ),
    )