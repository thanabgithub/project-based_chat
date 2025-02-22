from datetime import datetime, timezone
from typing import List, Optional
from sqlmodel import select, desc
from sqlalchemy.orm import selectinload

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

    # Project modal state
    show_project_modal: bool = False
    project_to_edit: Optional[int] = None

    @rx.var
    def project_modal_title(self) -> str:
        """Get the title for the project modal."""
        return "Edit Project" if self.project_to_edit else "New Project"

    @rx.var
    def project_to_edit_data(self) -> Optional[Project]:
        """Get the project being edited with its knowledge documents eagerly loaded."""

        # Adding a dependency to force recomputation. This enables re-render after uploading a new document
        _ = self.doc_list_version

        if self.project_to_edit is None:
            return None
        with rx.session() as session:
            statement = (
                select(Project)
                .options(selectinload(Project.knowledge))
                .where(Project.id == self.project_to_edit)
            )
            return session.exec(statement).first()

    def toggle_project_modal(self):
        """Toggle the project modal."""
        self.show_project_modal = not self.show_project_modal
        # if not self.show_project_modal:
        #     # Clear edit state when closing
        #     self.project_to_edit = None

    @rx.event
    def set_show_project_modal(self, show: bool):
        """Set modal visibility directly."""
        self.show_project_modal = show
        # if not show:
        #     # Clear edit state when closing
        #     self.project_to_edit = None

    @rx.event
    def handle_project_submit(self, form_data: dict):
        """Handle project form submission - create or edit."""
        print(self.project_to_edit)
        with rx.session() as session:
            if self.project_to_edit:
                # Edit existing project
                project = session.get(Project, self.project_to_edit)
                if project:
                    project.name = form_data["name"]
                    project.description = form_data.get("description", "")
                    project.system_instructions = form_data.get(
                        "system_instructions", ""
                    )
                    project.updated_at = datetime.now(timezone.utc)
                    session.add(project)
                    session.commit()
                    # Update current project if editing current
                    if self.current_project_id == project.id:
                        self.current_project_id = project.id
            else:
                # Create new project
                project = Project(
                    name=form_data["name"],
                    description=form_data.get("description", ""),
                    system_instructions=form_data.get("system_instructions", ""),
                )
                session.add(project)
                session.commit()
                session.refresh(project)
                # Set as current project
                self.current_project_id = project.id

        # Close modal and reload
        self.show_project_modal = False
        self.project_to_edit = None
        self.load_project_chats()
        self.load_projects()

        # Redirect if creating new
        if not self.project_to_edit:
            return rx.redirect(f"/projects/{project.id}")

    @rx.event
    async def delete_project(self, project_id: int):
        """Delete a project."""
        with rx.session() as session:
            project = session.get(Project, project_id)
            if project:
                session.delete(project)
                session.commit()

        # Clear current if deleted
        if project_id == self.current_project_id:
            self.current_project_id = None
            self.current_chat_id = None

        # Reload and redirect
        self.load_projects()
        return rx.redirect("/projects")

    @rx.event
    async def set_project_to_edit(self, project_id: int):
        """Set which project to edit."""
        self.project_to_edit = project_id

    # Form data state
    project_name: str = ""
    project_description: str = ""
    project_system_instructions: str = ""

    def set_project_name(self, name: str):
        """Set the project name input value."""
        self.project_name = name

    def set_project_description(self, description: str):
        """Set the project description input value."""
        self.project_description = description

    def set_project_system_instructions(self, instructions: str):
        """Set the project system instructions input value."""
        self.project_system_instructions = instructions

    # Chat modal state
    chat_to_edit: Optional[int] = None
    chat_name: str = ""

    @rx.var
    def chat_modal_title(self) -> str:
        """Get the title for the chat modal."""
        return "Edit Chat" if self.chat_to_edit else "New Chat"

    @rx.var
    def chat_to_edit_data(self) -> Optional[Chat]:
        """Get the chat being edited."""
        if self.chat_to_edit is None:
            return None
        with rx.session() as session:
            return session.get(Chat, self.chat_to_edit)

    def toggle_chat_modal(self):
        """Toggle the chat modal."""
        self.show_chat_modal = not self.show_chat_modal
        if not self.show_chat_modal:
            # Clear edit state when closing
            self.chat_to_edit = None

    @rx.event
    def set_show_chat_modal(self, show: bool):
        """Set chat modal visibility directly."""
        self.show_chat_modal = show
        if not show:
            # Clear edit state when closing
            self.chat_to_edit = None

    def set_chat_name(self, name: str):
        """Set the chat name input value."""
        self.chat_name = name

    @rx.event
    async def set_chat_to_edit(self, chat_id: int):
        """Set which chat to edit."""
        self.chat_to_edit = chat_id

    @rx.event
    async def handle_chat_submit(self, form_data: dict):
        """Handle chat form submission - create or edit."""
        with rx.session() as session:
            if self.chat_to_edit:
                # Edit existing chat
                chat = session.get(Chat, self.chat_to_edit)
                if chat:
                    chat.name = form_data["name"]
                    chat.updated_at = datetime.now(timezone.utc)
                    session.add(chat)
                    session.commit()
                    # Update current chat if editing current
                    if self.current_chat_id == chat.id:
                        self.current_chat_id = chat.id
            else:
                # Create new chat
                chat = Chat(
                    name=form_data["name"],
                    project_id=self.current_project_id,
                )
                session.add(chat)
                session.commit()
                session.refresh(chat)
                # Set as current chat
                self.current_chat_id = chat.id

            # Clear form data
            self.chat_name = ""

            # Close modal and reload
            self.show_chat_modal = False
            self.chat_to_edit = None
            self.load_project_chats()

            # Redirect if creating new
            if not self.chat_to_edit:
                return rx.redirect(
                    f"/projects/{self.current_project_id}/chats/{chat.id}"
                )

    @rx.event
    async def delete_chat(self, chat_id: int):
        """Delete a chat."""
        with rx.session() as session:
            chat = session.get(Chat, chat_id)
            if chat:
                session.delete(chat)
                session.commit()

        # Clear current if deleted
        if chat_id == self.current_chat_id:
            self.current_chat_id = None

        # Reload and redirect to project
        self.load_project_chats()
        return rx.redirect(f"/projects/{self.current_project_id}")

    doc_list_version: int = 0

    document_name: str = ""
    document_content: str = ""
    pending_documents: list[dict] = []

    doc_list_version: int = 0  # Add this version counter

    @rx.event
    async def handle_document_submit(self):
        """Handle document form submission."""
        with rx.session() as session:
            if self.project_to_edit:
                # Create and save the new document
                document = Document(
                    project_id=self.project_to_edit,
                    name=self.document_name,
                    content=self.document_content,
                    type="text",
                )
                session.add(document)
                session.commit()

                # Increment version to trigger re-render
                self.doc_list_version += 1

                # Clear form fields
                self.document_name = ""
                self.document_content = ""
            else:
                # Store document data to be added when project is created
                self.pending_documents.append(
                    {
                        "name": self.document_name,
                        "content": self.document_content,
                        "type": "text",
                    }
                )

    @rx.event
    async def delete_document(self, doc_id: int):
        """Delete a document from the knowledge base."""
        with rx.session() as session:
            document = session.get(Document, doc_id)
            if document and document.project_id == self.current_project_id:
                session.delete(document)
                session.commit()
                # Increment version to trigger re-render after delete
                self.doc_list_version += 1
