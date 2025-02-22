from datetime import datetime, timezone
from typing import List, Optional
from sqlmodel import Column, DateTime, Field, func, Relationship

import reflex as rx


class Message(rx.Model, table=True):
    """A chat message."""

    role: str
    content: Optional[str] = None
    reasoning: Optional[str] = None

    chat_id: int = Field(foreign_key="chat.id")
    created: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        ),
    )
    updated: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
    )

    # Define relationship
    chat: "Chat" = Relationship(back_populates="messages")


class Chat(rx.Model, table=True):
    """A chat session containing messages."""

    name: str
    project_id: int = Field(foreign_key="project.id")

    created: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        ),
    )
    updated: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
    )

    # Define relationships
    messages: List[Message] = Relationship(back_populates="chat")
    project: "Project" = Relationship(back_populates="chats")


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
    updated: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
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
    updated: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
    )

    # Define relationships
    knowledge: List[Document] = Relationship(back_populates="project")
    chats: List[Chat] = Relationship(back_populates="project")
