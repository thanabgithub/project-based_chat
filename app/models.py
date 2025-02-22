from datetime import datetime, timezone
from typing import List, Optional
from sqlmodel import Column, DateTime, Field, func, Relationship

import reflex as rx

"""
**Primary Key**

Yes, by default Reflex will create a primary key column called `id` for each table.  [(1)](https://reflex.dev/docs/database/tables/) 

Here's how it works:
- When you create a table by inheriting from `rx.Model`, an `id` field is automatically added as the primary key 
- This behavior applies to all database backends, including SQLite 
- If you define a different field with `primary_key=True`, then the default `id` field will not be created 

For example, here's a basic table definition that will automatically include an id column:

```python
class User(rx.Model, table=True):
    username: str
    email: str
```

Note that it's currently not possible to create a table without a primary key in Reflex. 
"""


class Message(rx.Model, table=True):
    """A chat message."""

    role: str
    content: Optional[str] = None
    reasoning: Optional[str] = None

    chat_id: int = Field(foreign_key="chat.id")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        ),
    )
    updated_at: datetime = Field(
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

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        ),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
    )

    # Define relationships
    messages: List[Message] = Relationship(
        back_populates="chat", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    project: "Project" = Relationship(back_populates="chats")


class Document(rx.Model, table=True):
    """A document in the knowledge base."""

    name: str
    type: str
    content: str = ""
    project_id: int = Field(foreign_key="project.id")

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        ),
    )
    updated_at: datetime = Field(
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

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        ),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
    )

    # Define relationships with cascade delete
    knowledge: List[Document] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    chats: List[Chat] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
