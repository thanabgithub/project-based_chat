"""The app state."""

from datetime import datetime, timezone
from typing import List, Optional
from sqlmodel import select, desc

import reflex as rx
from .models import Project, Chat, Message, Document


class State(rx.State):
    """The app state."""

    # Project state
    _projects: List[Project] = []
    _project_chats: List[Chat] = []
    current_project_id: Optional[int] = None
    current_chat_id: Optional[int] = None

    # UI state
    show_project_modal: bool = False
    show_chat_modal: bool = False
    show_knowledge_base: bool = False
    message: str = ""

    @rx.var
    def projects(self) -> List[Project]:
        """Get list of all projects ordered by last update."""
        return self._projects

    @rx.var
    def current_project(self) -> Optional[Project]:
        """Get the currently selected project."""
        if self.current_project_id is None:
            return None
        with rx.session() as session:
            return session.get(Project, self.current_project_id)

    @rx.var
    def current_chat(self) -> Optional[Chat]:
        """Get the currently selected chat."""
        if self.current_chat_id is None:
            return None
        with rx.session() as session:
            return session.get(Chat, self.current_chat_id)

    @rx.var
    def project_chats(self) -> List[Chat]:
        """Get chats for current project."""
        return self._project_chats

    def load_project_chats(self):
        """Load project chats ordered by last update."""
        if self.current_project_id is None:
            self._project_chats = []
        else:
            with rx.session() as session:
                self._project_chats = session.exec(
                    select(Chat)
                    .where(Chat.project_id == self.current_project_id)
                    .order_by(desc(Chat.updated_at))
                ).all()

    @rx.event
    async def handle_project_route(self):
        """Handle project route params."""
        project_id = int(self.router.page.params.get("project_id", 0))
        if project_id:
            await self.select_project(project_id)

    @rx.event
    async def handle_chat_route(self):
        """Handle chat route params."""
        project_id = int(self.router.page.params.get("project_id", 0))
        chat_id = int(self.router.page.params.get("chat_id", 0))
        if project_id:
            await self.select_project(project_id)
        if chat_id:
            await self.select_chat(chat_id)

    @rx.event
    def load_projects(self):
        """Load all projects from the database ordered by last update."""
        with rx.session() as session:
            self._projects = session.exec(
                select(Project).order_by(desc(Project.updated_at))
            ).all()

    @rx.event
    def toggle_project_modal(self):
        """Toggle the project modal."""
        self.show_project_modal = not self.show_project_modal

    @rx.event
    def toggle_chat_modal(self):
        """Toggle the chat modal."""
        self.show_chat_modal = not self.show_chat_modal

    @rx.event
    def set_show_project_modal(self, show: bool):
        """Set modal visibility directly."""
        self.show_project_modal = show

    @rx.event
    def set_show_chat_modal(self, show: bool):
        """Set chat modal visibility directly."""
        self.show_chat_modal = show

    @rx.event
    def toggle_knowledge_base(self):
        """Toggle the knowledge base sidebar."""
        self.show_knowledge_base = not self.show_knowledge_base

    @rx.event
    async def create_project(self, form_data: dict):
        """Create a new project."""
        with rx.session() as session:
            # Create new project
            project = Project(
                name=form_data["name"],
                description=form_data.get("description", ""),
                system_instructions=form_data.get("system_instructions", ""),
            )
            session.add(project)
            session.commit()
            session.refresh(project)

            # Update current project
            self.current_project_id = project.id

        # Close modal and reload projects
        self.show_project_modal = False
        self.load_project_chats()
        self.load_projects()
        return rx.redirect(f"/projects/{project.id}")

    @rx.event
    async def create_chat(self, form_data: dict):
        """Create a new chat."""
        if not self.current_project_id:
            return

        with rx.session() as session:
            chat = Chat(name=form_data["name"], project_id=self.current_project_id)
            session.add(chat)
            session.commit()
            session.refresh(chat)

            # Set as current chat
            self.current_chat_id = chat.id

        # Close modal and refresh chats
        self.show_chat_modal = False
        self.load_project_chats()
        return rx.redirect(f"/projects/{self.current_project_id}/chats/{chat.id}")

    @rx.event
    async def select_project(self, project_id: int):
        """Select a project."""
        with rx.session() as session:
            project = session.get(Project, project_id)
            if not project:
                return rx.redirect("/projects")

            project.updated_at = datetime.now(timezone.utc)
            session.add(project)
            session.commit()

        self.current_project_id = project_id
        self.current_chat_id = None  # Clear selected chat
        self.load_project_chats()
        return self.load_projects()

    @rx.event
    async def select_chat(self, chat_id: int):
        """Select a chat."""
        self.current_chat_id = chat_id
        # Update the chat's timestamp when selected
        with rx.session() as session:
            chat = session.get(Chat, chat_id)
            if not chat:
                return rx.redirect(f"/projects/{self.current_project_id}")

            chat.updated_at = datetime.now(timezone.utc)
            session.add(chat)
            session.commit()
        self.load_project_chats()  # Refresh to update order

    @rx.event
    async def send_message(self):
        """Send a chat message."""
        if not self.message.strip() or not self.current_chat_id:
            return

        with rx.session() as session:
            # Add the message
            message = Message(
                role="user", content=self.message, chat_id=self.current_chat_id
            )
            session.add(message)

            # Update the chat's timestamp
            chat = session.get(Chat, self.current_chat_id)
            chat.updated_at = datetime.now(timezone.utc)
            session.add(chat)

            session.commit()

        # Clear the input and refresh chats to update order
        self.message = ""
        self.load_project_chats()

    @rx.event
    async def delete_document(self, doc_id: int):
        """Delete a document from the knowledge base."""
        with rx.session() as session:
            document = session.get(Document, doc_id)
            if document and document.project_id == self.current_project_id:
                session.delete(document)
                session.commit()
                # Could add toast or other notification here
