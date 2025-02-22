import reflex as rx
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class Document:
    """A document in the knowledge base."""

    id: int
    name: str
    type: str
    content: str


@dataclass
class Project:
    """A project containing chats and knowledge base."""

    id: int
    name: str
    description: str
    system_instructions: str
    knowledge: List[Document]


class State(rx.State):
    """The app state."""

    # List of all projects
    projects: List[Project] = []

    # Currently selected project/chat
    current_project_id: Optional[int] = None
    current_chat_id: Optional[int] = None

    # UI state
    show_project_modal: bool = False
    show_knowledge_base: bool = False

    @rx.var
    def current_project(self) -> Optional[Project]:
        """Get the currently selected project."""
        if self.current_project_id is None:
            return None
        return next((p for p in self.projects if p.id == self.current_project_id), None)

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
        project = Project(
            id=len(self.projects),
            name=form_data["name"],
            description=form_data["description"],
            system_instructions=form_data["system_instructions"],
            knowledge=[],
        )
        self.projects.append(project)
        self.show_project_modal = False
        self.current_project_id = project.id

    @rx.event
    def upload_document(self, file_data: List[dict]):
        """Upload a document to the current project."""
        if not self.current_project:
            return

        for file in file_data:
            doc = Document(
                id=len(self.current_project.knowledge),
                name=file["name"],
                type=file["type"],
            )
            self.current_project.knowledge.append(doc)
