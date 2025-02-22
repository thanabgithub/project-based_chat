"""The app state."""

from typing import List, Optional
from sqlmodel import select

import reflex as rx

from .models import Project, Document


class State(rx.State):
    """The app state."""

    # Initialize projects as empty list
    _projects: List[Project] = []

    # Currently selected project/chat
    current_project_id: Optional[int] = None
    current_chat_id: Optional[int] = None

    # UI state
    show_project_modal: bool = False
    show_knowledge_base: bool = False
    message: str = ""
    chat_messages: List[str] = []

    @rx.var
    def projects(self) -> List[Project]:
        """Get list of all projects."""
        return self._projects

    @rx.event
    def load_projects(self):
        """Load all projects from the database."""
        with rx.session() as session:
            self._projects = session.exec(select(Project)).all()

    @rx.var
    def current_project(self) -> Optional[Project]:
        """Get the currently selected project."""
        if self.current_project_id is None:
            return None
        with rx.session() as session:
            return session.get(Project, self.current_project_id)

    @rx.event
    def send_message(self):
        """Send a chat message."""
        if self.message.strip():
            self.chat_messages.append(self.message)
            self.message = ""

    @rx.event
    def toggle_project_modal(self):
        """Toggle the new project modal."""
        self.show_project_modal = not self.show_project_modal

    @rx.event
    def toggle_knowledge_base(self):
        """Toggle the knowledge base sidebar."""
        self.show_knowledge_base = not self.show_knowledge_base

    @rx.event
    def select_project(self, project_id: int):
        """Select a project."""
        self.current_project_id = project_id
        self.current_chat_id = None

    @rx.event
    def create_project(self, form_data: dict):
        """Create a new project."""
        with rx.session() as session:
            project = Project(
                name=form_data["name"],
                description=form_data.get("description", ""),
                system_instructions=form_data.get("system_instructions", ""),
            )
            session.add(project)
            session.commit()
            session.refresh(project)
            self.current_project_id = project.id

        self.show_project_modal = False
        # Reload projects after creating new one
        return self.load_projects

    @rx.event
    async def upload_document(self, files: List[rx.UploadFile]):
        """Upload a document to the current project."""
        if not self.current_project:
            return

        with rx.session() as session:
            for file in files:
                # Read the file content
                content = await file.read()
                content_str = content.decode("utf-8")

                doc = Document(
                    name=file.filename,
                    type=file.content_type,
                    content=content_str,
                    project_id=self.current_project_id,
                )
                session.add(doc)
            session.commit()

    @rx.event
    def delete_document(self, doc_id: int):
        """Delete a document from the current project."""
        with rx.session() as session:
            doc = session.get(Document, doc_id)
            if doc:
                session.delete(doc)
                session.commit()
