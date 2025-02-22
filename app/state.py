import os
from datetime import datetime, timezone
from typing import *
from dotenv import load_dotenv
from sqlmodel import select, desc
from sqlalchemy.orm import selectinload
import aiohttp


import reflex as rx
from .models import Project, Chat, Message, Document
from dataclasses import dataclass
import json

load_dotenv()


@dataclass
class StreamChunk:
    content: Optional[str] = None
    reasoning: Optional[str] = None
    is_done: bool = False
    error: Optional[str] = None


class StreamProcessor:
    """Stream processor that follows the official OpenRouter documentation approach."""

    def __init__(self, response, session):
        self.response = response
        self.session = session
        self.buffer = ""
        self._closed = False

    async def start(self):
        """Start processing the stream."""
        return self

    async def __aiter__(self):
        """Iterate over the stream chunks following the official approach."""
        try:
            while not self._closed:
                chunk = await self.response.content.read(1024)
                if not chunk:
                    break

                self.buffer += chunk.decode("utf-8")

                while True:
                    line_end = self.buffer.find("\n")
                    if line_end == -1:
                        break

                    line = self.buffer[:line_end].strip()
                    self.buffer = self.buffer[line_end + 1 :]

                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            self._closed = True
                            break

                        try:
                            data_obj = json.loads(data)
                            content = data_obj["choices"][0]["delta"].get("content")
                            reasoning = data_obj["choices"][0]["delta"].get("reasoning")

                            # Only yield if we have content or reasoning
                            if content or reasoning:
                                yield StreamChunk(
                                    content=content, reasoning=reasoning, is_done=False
                                )
                        except json.JSONDecodeError:
                            continue
                        except Exception as e:
                            print(f"Error processing chunk: {str(e)}")
                            continue

        except Exception as e:
            print(f"Stream error: {str(e)}")
        finally:
            await self.close()

    async def close(self):
        """Close the stream processor and clean up resources."""
        if not self._closed:
            self._closed = True
            if not self.response.closed:
                await self.response.release()
            await self.session.close()

    async def __aenter__(self):
        """Support for async context manager."""
        return await self.start()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup when exiting async context."""
        await self.close()


class ChatCompletionChunk:
    def __init__(self, chunk_data: Dict[str, Any]):
        self.choices = [Choice(choice) for choice in chunk_data.get("choices", [])]
        self.id = chunk_data.get("id")
        self.model = chunk_data.get("model")
        self.created = chunk_data.get("created")


class Choice:
    def __init__(self, choice_data: Dict[str, Any]):
        self.delta = Delta(choice_data.get("delta", {}))
        self.index = choice_data.get("index")
        self.finish_reason = choice_data.get("finish_reason")


class Delta:
    def __init__(self, delta_data: Dict[str, Any]):
        self.content = delta_data.get("content")
        self.role = delta_data.get("role")
        self.reasoning = delta_data.get("reasoning")


class AsyncOpenRouterAI:
    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.chat = self.Chat(self)

    class Chat:
        def __init__(self, client):
            self.client = client
            self.completions = self

        async def create(
            self,
            model: str,
            messages: List[Dict[str, str]],
            stream: bool = False,
            include_reasoning: bool = False,
            **kwargs,
        ) -> Union[ChatCompletionChunk, StreamProcessor]:
            """Create a chat completion with queue-based streaming."""
            url = f"{self.client.base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.client.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": model,
                "messages": messages,
                "stream": stream,
                "include_reasoning": include_reasoning,
                **kwargs,
            }

            session = aiohttp.ClientSession()
            try:
                response = await session.post(url, headers=headers, json=payload)

                if not stream:
                    try:
                        data = await response.json()
                        return ChatCompletionChunk(data)
                    finally:
                        await session.close()

                return await StreamProcessor(response, session).start()

            except Exception as e:
                await session.close()
                raise


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

    def clear_project_form(self):
        """Clear all project form data."""
        self.project_name = ""
        self.project_description = ""
        self.project_system_instructions = ""
        self.project_to_edit = None  # Add this line
        self.pending_documents = []

    @rx.event
    def toggle_chat_modal(self):
        """Toggle the chat modal."""
        self.show_chat_modal = not self.show_chat_modal

    @rx.event
    def set_show_project_modal(self, show: bool):
        """Set modal visibility directly and clean up form when closing."""

        self.show_project_modal = show
        if not show:  # When closing the modal
            self.clear_project_form()  # Clear all form data

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

    @rx.event
    def handle_project_submit(self, form_data: dict):
        """Handle project form submission - create or edit."""
        with rx.session() as session:
            was_editing = self.project_to_edit  # Store edit state
            project_id = self.project_to_edit  # Store project id being edited

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
        self.clear_project_form()
        self.load_project_chats()
        self.load_projects()

        # Only redirect if creating new project
        if not was_editing:
            return rx.redirect(f"/projects/{project.id}")
        else:
            return rx.redirect(f"/projects/{project_id}")

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
    async def delete_document(self, doc_id: int):
        """Delete a document from the knowledge base."""
        with rx.session() as session:
            document = session.get(Document, doc_id)
            if document and document.project_id == self.current_project_id:
                session.delete(document)
                session.commit()
                # Increment version to trigger re-render after delete
                self.doc_list_version += 1

    # Document form state
    document_to_edit_id: Optional[int] = None
    document_name: str = ""
    document_content: str = ""

    def set_document_name(self, name: str):
        """Set document name."""
        self.document_name = name

    def set_document_content(self, content: str):
        """Set document content."""
        self.document_content = content

    @rx.event
    def set_document_to_edit(self, doc_id: int, name: str, content: str):
        """Set document being edited and populate form fields."""
        self.document_to_edit_id = doc_id
        self.document_name = name
        self.document_content = content

    def clear_document_form(self):
        """Clear document form fields."""
        self.document_to_edit_id = None
        self.document_name = ""
        self.document_content = ""

    @rx.event
    async def handle_document_submit(self):
        """Handle document form submission."""
        with rx.session() as session:
            if self.project_to_edit:
                if self.document_to_edit_id:
                    # Update existing document
                    document = session.get(Document, self.document_to_edit_id)
                    if document:
                        document.name = self.document_name
                        document.content = self.document_content
                        document.updated_at = datetime.now(timezone.utc)
                        session.add(document)
                        session.commit()
                else:
                    # Create new document
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
                self.clear_document_form()

    show_document_modal: bool = False

    @rx.event
    def toggle_document_modal(self):
        """Toggle document modal visibility."""
        self.show_document_modal = not self.show_document_modal

    @rx.event
    def set_show_document_modal(self, show: bool):
        """Set document modal visibility."""
        self.show_document_modal = show
        if not show:
            self.clear_document_form()

    @rx.event
    def set_document_to_edit(self, doc_id: int, name: str, content: str):
        """Set document being edited and populate form fields."""
        self.document_to_edit_id = doc_id
        self.document_name = name
        self.document_content = content

    # Chat processing state
    processing: bool = False
    message: str = ""
    previous_keydown_character: str = ""
    model: str = "mistralai/codestral-2501"

    @rx.event(background=True)
    async def handle_action_bar_keydown(self, keydown_character: str):
        """Handle keyboard shortcuts."""
        async with self:
            if (
                self.previous_keydown_character == "Control"
                and keydown_character == "Enter"
            ):
                yield State.process_message
            self.previous_keydown_character = keydown_character

    @rx.event(background=True)
    async def stop_process(self):
        """Stop the current processing."""
        async with self:
            self.processing = False

    def format_messages(self, message: str) -> List[Dict[str, str]]:
        """Format chat history and current message into messages for the API."""
        messages = []

        # Get chat history
        with rx.session() as session:
            chat = session.get(Chat, self.current_chat_id)
            if chat:
                for msg in chat.messages:
                    if msg.content:
                        messages.append({"role": msg.role, "content": msg.content})

        # Add current message
        messages.append({"role": "user", "content": message})
        return messages

    @rx.event(background=True)
    async def process_message(self):
        """Process the current message with AI and add to chat history."""
        if not self.message.strip() or not self.current_chat_id:
            return

        current_message = self.message

        async with self:
            self.processing = True
            self.message = ""

        try:
            # Initialize API client
            client = AsyncOpenRouterAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv("OPENROUTER_API_KEY"),
            )

            messages = self.format_messages(current_message)

            # Create user message
            with rx.session() as session:
                message = Message(
                    role="user", content=current_message, chat_id=self.current_chat_id
                )
                session.add(message)
                session.commit()

                # Create initial assistant message
                assistant_message = Message(
                    role="assistant", chat_id=self.current_chat_id
                )
                session.add(assistant_message)
                session.commit()
                session.refresh(assistant_message)
                assistant_id = assistant_message.id

            # Get streaming response
            processor = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                include_reasoning=True,
            )

            async with processor:
                answer = ""
                reasoning = ""

                async for chunk in processor:
                    if not self.processing:
                        break

                    # Update message in database
                    with rx.session() as session:
                        message = session.get(Message, assistant_id)

                        if chunk.reasoning:
                            reasoning += chunk.reasoning
                            message.reasoning = reasoning

                        if chunk.content:
                            answer += chunk.content
                            message.content = answer

                        session.add(message)
                        session.commit()

            # Update chat timestamp
            with rx.session() as session:
                chat = session.get(Chat, self.current_chat_id)
                chat.updated_at = datetime.now(timezone.utc)
                session.add(chat)
                session.commit()

        except Exception as e:
            # Handle errors
            with rx.session() as session:
                message = session.get(Message, assistant_id)
                message.content = f"Error: {str(e)}"
                session.add(message)
                session.commit()

        finally:
            async with self:
                self.processing = False
            self.load_project_chats()
