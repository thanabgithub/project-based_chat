"""Database models for the app."""

from datetime import datetime, timezone
from typing import List
from sqlmodel import Column, DateTime, Field, func, Relationship

import reflex as rx


class Document(rx.Model, table=True):
    """A document in the knowledge base."""

    name: str
    type: str
    content: str = ""
    project_id: int = Field(foreign_key="project.id")

    created: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        ),
    )

    # Define relationship
    project: "Project" = Relationship(back_populates="knowledge")


class Project(rx.Model, table=True):
    """A project containing chats and knowledge base."""

    name: str
    description: str = ""
    system_instructions: str = ""

    created: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        ),
    )

    # Define relationship to documents
    knowledge: List[Document] = Relationship(back_populates="project")
