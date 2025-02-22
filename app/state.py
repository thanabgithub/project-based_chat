"""The app state."""

from typing import List, Optional
from sqlmodel import select

import reflex as rx

from .models import Project


class State(rx.State):
    """The app state."""

    # Project state
    _projects: List[Project] = []
    current_project_id: Optional[int] = None

    # UI state
    show_project_modal: bool = False
    show_knowledge_base: bool = False
    message: str = ""

    @rx.var
    def projects(self) -> List[Project]:
        """Get list of all projects."""
        return self._projects

    @rx.var
    def current_project(self) -> Optional[Project]:
        """Get the currently selected project."""
        if self.current_project_id is None:
            return None
        with rx.session() as session:
            return session.get(Project, self.current_project_id)

    @rx.event
    def load_projects(self):
        """Load all projects from the database."""
        with rx.session() as session:
            self._projects = session.exec(select(Project)).all()

    @rx.event
    def toggle_project_modal(self):
        """Toggle the project modal."""
        self.show_project_modal = not self.show_project_modal

    @rx.event
    def set_show_project_modal(self, show: bool):
        """Set modal visibility directly."""
        self.show_project_modal = show

    @rx.event
    def toggle_knowledge_base(self):
        """Toggle the knowledge base sidebar."""
        self.show_knowledge_base = not self.show_knowledge_base

    @rx.event
    def send_message(self):
        """Send a chat message."""
        if self.message.strip():
            # Logic for sending message would go here
            self.message = ""  # Clear the input

    @rx.event
    def create_project(self, form_data: dict):
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
        # Use State.load_projects instead of self.load_projects
        return State.load_projects

    @rx.event
    def select_project(self, project_id: int):
        """Select a project."""
        self.current_project_id = project_id
