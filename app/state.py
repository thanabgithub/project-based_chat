import os
from datetime import datetime, timezone
from typing import *
from dotenv import load_dotenv
from sqlmodel import select, desc
from sqlalchemy.orm import selectinload
import aiohttp

import dataclasses

import reflex as rx
from .models import Project, Chat, Message, Document
from dataclasses import dataclass
import json

load_dotenv()


@dataclasses.dataclass
class UIMessage:
    role: str
    content: Optional[str] = None
    reasoning: Optional[str] = None


def format_system_prompt(system_instructions: str, documents: list) -> str:
    """Format the system prompt with instructions and documents.

    Args:
        system_instructions: The project's system instructions
        documents: List of Document objects from the database

    Returns:
        Formatted system prompt string
    """
    # Base prompt template
    prompt_template = """<response_guidelines>
# Educational Approach
- Break down complex topics
- Build from fundamentals
- Use concrete examples
- Provide helpful analogies
- Add context and background
- Anticipate confusion points
- Write clear explanations

# Response Format
- Use markdown formatting
- Write in full sentences
- Use bullets only when requested
- Include descriptive comments
- Create clear section headers
- Maintain consistent style

# Code Examples
- Include detailed comments
- Follow project conventions
- Make code runnable
- Refer from documents
</response_guidelines>

<identity>
{system_instructions}
</identity>

<documents>
{document_sections}
</documents>"""

    # Format document sections
    doc_sections = []
    for doc in documents:
        doc_section = f"""<document>
<source>{doc.name}</source>
<document_content>
{doc.content}
</document_content>
</document>"""
        doc_sections.append(doc_section)

    # Join all document sections
    document_sections = "\n\n".join(doc_sections)

    # Format the complete prompt
    return prompt_template.format(
        system_instructions=system_instructions, document_sections=document_sections
    )


def get_messages_with_system_prompt(
    chat_messages: list, project_documents: list, system_instructions: str
) -> list:
    """Get formatted messages list with system prompt for API call.

    Args:
        chat_messages: List of chat messages
        project_documents: List of project documents
        system_instructions: Project's system instructions

    Returns:
        List of formatted messages including system prompt
    """
    # Create system prompt
    system_prompt = format_system_prompt(system_instructions, project_documents)

    # Create messages list with system prompt as first message
    messages = [{"role": "system", "content": system_prompt}]

    # Add chat messages
    for msg in chat_messages:
        if msg.get("content"):  # Only add messages with content
            messages.append({"role": msg["role"], "content": msg["content"]})

    return messages


@dataclass
class StreamChunk:
    content: Optional[str] = None
    reasoning: Optional[str] = None
    is_done: bool = False
    error: Optional[str] = None


class StreamProcessor:
    """Stream processor with proper resource management."""

    def __init__(self, response, client):
        self.response = response
        self.client = client
        self.buffer = ""
        self._closed = False

    async def start(self):
        """Start processing the stream."""
        return self

    async def __aiter__(self):
        """Iterate over the stream chunks."""
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
            # Note: Don't close the client session here as it may be reused


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
        self._session = None

    async def get_session(self):
        """Get or create an aiohttp ClientSession."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        """Close the client session if it exists."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

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

            session = await self.client.get_session()
            try:
                response = await session.post(url, headers=headers, json=payload)

                if not stream:
                    try:
                        data = await response.json()
                        return ChatCompletionChunk(data)
                    finally:
                        # For non-streaming requests, close immediately after use
                        await response.release()

                # For streaming, return StreamProcessor which will handle cleanup
                return await StreamProcessor(response, self.client).start()

            except Exception as e:
                # Ensure session is closed on error
                await self.client.close()
                raise


class State(rx.State):
    # -------------------------------------------------------------------------
    # Existing state fields, events, and computed vars…
    # -------------------------------------------------------------------------

    _projects: List[Project] = []
    _project_chats: List[Chat] = []
    current_project_id: Optional[int] = None
    current_chat_id: Optional[int] = None

    show_project_modal: bool = False
    show_chat_modal: bool = False
    show_knowledge_base: bool = False

    editing_user_message_index: Optional[int] = None
    editing_assistant_content_index: Optional[int] = None
    editing_assistant_reasoning_index: Optional[int] = None
    question: str = ""  # For editing/entering user message
    answer: str = ""  # For editing assistant content
    reasoning: str = ""  # For editing assistant reasoning

    def load_messages(self):
        """Load messages from database into state."""
        if self.current_chat_id is None:
            self.messages = []
            return

        with rx.session() as session:
            chat = session.get(Chat, self.current_chat_id)
            if chat and chat.messages:
                self.messages = [
                    UIMessage(
                        role=msg.role, content=msg.content, reasoning=msg.reasoning
                    )
                    for msg in chat.messages
                ]
            else:
                self.messages = []

    # -------------------------------------------------------------------------
    # Editing Events (using current_chat messages via the ORM)
    # -------------------------------------------------------------------------

    @rx.event
    def start_editing_user_message(self, index: int):
        """Start editing a user message from the current chat."""
        if self.current_chat_id is None:
            return
        with rx.session() as session:
            chat = session.get(Chat, self.current_chat_id)
            if not chat or index < 0 or index >= len(chat.messages):
                return
            msg = chat.messages[index]
            if msg.role != "user":
                return
            self.editing_user_message_index = index
            self.question = msg.content or ""

    @rx.event
    def start_editing_assistant_content(self, index: int):
        """Start editing the assistant's content message."""
        if self.current_chat_id is None:
            return
        with rx.session() as session:
            chat = session.get(Chat, self.current_chat_id)
            if not chat or index < 0 or index >= len(chat.messages):
                return
            msg = chat.messages[index]
            if msg.role != "assistant":
                return
            self.editing_assistant_content_index = index
            self.answer = msg.content or ""

    @rx.event
    def start_editing_assistant_reasoning(self, index: int):
        """Start editing the assistant's reasoning."""
        if self.current_chat_id is None:
            return
        with rx.session() as session:
            chat = session.get(Chat, self.current_chat_id)
            if not chat or index < 0 or index >= len(chat.messages):
                return
            msg = chat.messages[index]
            if msg.role != "assistant":
                return
            self.editing_assistant_reasoning_index = index
            self.reasoning = msg.reasoning or ""

    @rx.event
    def cancel_editing(self):
        """Cancel all editing modes."""
        self.editing_user_message_index = None
        self.editing_assistant_content_index = None
        self.editing_assistant_reasoning_index = None
        self.question = ""
        self.answer = ""
        self.reasoning = ""

    @rx.event(background=True)
    async def delete_message(self, index: int):
        """Delete a specific message from the current chat."""
        async with self:
            if self.current_chat_id is None:
                return

            with rx.session() as session:
                chat = session.get(Chat, self.current_chat_id)
                if not chat or index < 0 or index >= len(chat.messages):
                    return

                msg = chat.messages[index]
                # If deleting user message, also delete the assistant's response
                if msg.role == "user" and index + 1 < len(chat.messages):
                    session.delete(chat.messages[index + 1])
                session.delete(msg)

                # Update chat timestamp
                chat.updated_at = datetime.now(timezone.utc)
                session.add(chat)
                session.commit()

            # Update the messages in state
            self.load_messages()

    @rx.event
    async def update_user_message(self):
        """Update an existing user message and regenerate the assistant's answer."""
        if self.editing_user_message_index is None or not self.question.strip():
            return

        # Update user message in DB and remove subsequent messages
        with rx.session() as session:
            chat = session.get(Chat, self.current_chat_id)
            if not chat or self.editing_user_message_index >= len(chat.messages):
                return
            user_msg = chat.messages[self.editing_user_message_index]
            if user_msg.role != "user":
                return
            user_msg.content = self.question
            session.add(user_msg)
            session.commit()

            # Remove all messages after this user message
            for msg in chat.messages[self.editing_user_message_index + 1 :]:
                session.delete(msg)
            session.commit()

    @rx.event
    def update_assistant_content(self):
        """Update the assistant's content message."""
        if self.editing_assistant_content_index is None or not self.answer.strip():
            return
        with rx.session() as session:
            chat = session.get(Chat, self.current_chat_id)
            if not chat or self.editing_assistant_content_index >= len(chat.messages):
                return
            msg = chat.messages[self.editing_assistant_content_index]
            if msg.role != "assistant":
                return
            msg.content = self.answer
            session.add(msg)
            session.commit()

    @rx.event
    def update_assistant_reasoning(self):
        """Update the assistant's reasoning with the new value in `reasoning`."""
        if self.editing_assistant_reasoning_index is None or not self.reasoning.strip():
            return
        with rx.session() as session:
            chat = session.get(Chat, self.current_chat_id)
            if not chat or self.editing_assistant_reasoning_index >= len(chat.messages):
                return
            msg = chat.messages[self.editing_assistant_reasoning_index]
            if msg.role != "assistant":
                return
            msg.reasoning = self.reasoning
            session.add(msg)
            session.commit()
        self.editing_assistant_reasoning_index = None
        self.reasoning = ""

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
        """Set modal visibility directly without clearing form data."""
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

        self.current_project_id = project_id
        self.current_chat_id = None  # Clear selected chat
        self.load_project_chats()
        return self.load_projects()

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
                # Register pending documents for the new project
                for pending in self.pending_documents:
                    document = Document(
                        project_id=project.id,
                        name=pending.get("name", ""),
                        content=pending.get("content", ""),
                        type=pending.get("type", "text"),
                    )
                    session.add(document)
                session.commit()
                # Set as current project
                self.current_project_id = project.id

        # Clear form data (including pending documents)
        self.clear_project_form()
        self.load_project_chats()
        self.load_projects()

        # Redirect appropriately
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
        # If editing an existing project, write to the database
        if self.project_to_edit:
            with rx.session() as session:
                if self.document_to_edit_id:
                    document = session.get(Document, self.document_to_edit_id)
                    if document:
                        document.name = self.document_name
                        document.content = self.document_content
                        document.updated_at = datetime.now(timezone.utc)
                        session.add(document)
                        session.commit()
                else:
                    document = Document(
                        project_id=self.project_to_edit,
                        name=self.document_name,
                        content=self.document_content,
                        type="text",
                    )
                    session.add(document)
                    session.commit()
            # Trigger a re-render if needed.
            self.doc_list_version += 1
            self.clear_document_form()
        else:
            # For new projects, add document info to pending_documents
            self.pending_documents.append(
                {
                    "name": self.document_name,
                    "content": self.document_content,
                    "type": "text",
                }
            )
            self.doc_list_version += 1
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

    # Chat state
    _temp_messages: List[UIMessage] = []  # Temporary list for streaming
    previous_keydown_character: str = ""
    messages: List[UIMessage] = []  # For UI display
    ui_messages: list[UIMessage] = []
    current_question: str = ""
    model: str = "mistralai/codestral-2501"
    processing: bool = False

    @rx.var
    def chat_messages(self) -> List[Message]:
        """Get messages for current chat from database."""
        if self.current_chat_id is None:
            return []

        with rx.session() as session:
            chat = session.get(Chat, self.current_chat_id)
            if chat:
                return chat.messages
        return []

    # Editing state
    editing_user_message_index: Optional[int] = None
    editing_assistant_content_index: Optional[int] = None
    editing_assistant_reasoning_index: Optional[int] = None
    edit_content: str = ""

    def format_messages(self) -> List[Dict[str, str]]:
        """Format chat history with system prompt for the API."""
        # Get current project and its documents
        with rx.session() as session:
            # Get project with documents
            project = session.exec(
                select(Project)
                .options(selectinload(Project.knowledge))
                .where(Project.id == self.current_project_id)
            ).first()

            if not project:
                return [
                    {"role": msg.role, "content": msg.content}
                    for msg in self.messages
                    if msg.content
                ]

            # Get messages with system prompt
            return get_messages_with_system_prompt(
                chat_messages=[
                    {"role": msg.role, "content": msg.content}
                    for msg in self.messages
                    if msg.content
                ],
                project_documents=project.knowledge,
                system_instructions=project.system_instructions,
            )

    @rx.event(background=True)
    async def handle_action_bar_keydown(self, keydown_character: str):
        """Handle keyboard shortcuts."""
        async with self:
            if (
                self.previous_keydown_character == "Control"
                and keydown_character == "Enter"
            ):
                yield State.process_question
            self.previous_keydown_character = keydown_character

    @rx.var
    def chat_messages(self) -> List[UIMessage]:
        """Get messages for current chat from database and convert to UIMessage objects."""
        if self.current_chat_id is None:
            return []

        with rx.session() as session:
            chat = session.get(Chat, self.current_chat_id)
            if chat and chat.messages:
                # Convert DB messages to UIMessage objects
                return [
                    UIMessage(
                        role=msg.role, content=msg.content, reasoning=msg.reasoning
                    )
                    for msg in chat.messages
                ]
        return []

    def load_chat_messages(self):
        """Load messages from database into state."""
        self.messages = self.chat_messages

    @rx.event(background=True)
    async def process_question(self):
        """Process message with AI and handle database storage."""
        if not self.current_question.strip():
            return

        # Initialize assistant ID only
        assistant_id = None

        async with self:
            message_text = self.current_question
            self.processing = True
            self.current_question = ""
            answer = ""  # Initialize answer within context
            reasoning = ""  # Initialize reasoning within context

            # Get existing database messages and create new ones
            with rx.session() as session:
                chat = session.get(Chat, self.current_chat_id)
                if not chat:
                    return

                # Add user message to database
                user_msg = Message(
                    role="user", content=message_text, chat_id=self.current_chat_id
                )
                session.add(user_msg)

                # Create placeholder assistant message
                assistant_msg = Message(role="assistant", chat_id=self.current_chat_id)
                session.add(assistant_msg)
                session.commit()
                assistant_id = assistant_msg.id

                # Load fresh messages
                self.messages = [
                    UIMessage(
                        role=msg.role, content=msg.content, reasoning=msg.reasoning
                    )
                    for msg in chat.messages
                ]

            # Prepare messages for API
            messages_for_api = self.format_messages()

        # Process with AI
        client = AsyncOpenRouterAI(api_key=os.getenv("OPENROUTER_API_KEY"))

        try:
            processor = await client.chat.completions.create(
                model=self.model,
                messages=messages_for_api,
                stream=True,
                include_reasoning=True,
            )

            async for chunk in processor:
                if not self.processing:
                    break

                async with self:
                    # Update answer and reasoning within context
                    if chunk.content:
                        answer = answer + chunk.content if answer else chunk.content
                    if chunk.reasoning:
                        reasoning = (
                            reasoning + chunk.reasoning
                            if reasoning
                            else chunk.reasoning
                        )

                    # Update last message with current progress
                    messages = self.messages[:]  # Create a copy
                    if messages:
                        messages[-1].content = answer
                        messages[-1].reasoning = reasoning
                        self.messages = messages

            # After streaming completes, update database
            async with self:
                with rx.session() as session:
                    assistant_msg = session.get(Message, assistant_id)
                    if assistant_msg:
                        assistant_msg.content = answer
                        assistant_msg.reasoning = reasoning
                        session.add(assistant_msg)

                        # Update chat timestamp
                        chat = session.get(Chat, self.current_chat_id)
                        if chat:
                            chat.updated_at = datetime.now(timezone.utc)
                            session.add(chat)
                        session.commit()

                        # Refresh messages from database
                        self.messages = [
                            UIMessage(
                                role=msg.role,
                                content=msg.content,
                                reasoning=msg.reasoning,
                            )
                            for msg in chat.messages
                        ]

        except Exception as e:
            async with self:
                error_message = f"Error: {str(e)}"
                messages = self.messages[:]
                if messages:
                    messages[-1].content = error_message
                    self.messages = messages

                with rx.session() as session:
                    assistant_msg = session.get(Message, assistant_id)
                    if assistant_msg:
                        assistant_msg.content = error_message
                        session.add(assistant_msg)
                        session.commit()

        finally:
            await client.close()
            async with self:
                self.processing = False

    # Update the select_chat method to use load_messages
    @rx.event
    async def select_chat(self, chat_id: int):
        """Select chat and load its messages."""
        self.current_chat_id = chat_id
        self.load_messages()  # Use the new load_messages method

        self.load_project_chats()  # Refresh to update order

    @rx.event
    def start_editing(self, index: int, field: str):
        """Start editing a specific field of a message."""
        if 0 <= index < len(self.messages):
            msg = self.messages[index]
            self.edit_content = getattr(msg, field, "")

            if field == "content":
                if msg.role == "user":
                    self.editing_user_message_index = index
                else:
                    self.editing_assistant_content_index = index
            elif field == "reasoning":
                self.editing_assistant_reasoning_index = index

    @rx.event(background=True)
    async def regenerate_response(self, user_message_index: int):
        """Regenerate the AI response for a user message after editing."""
        assistant_id = None

        async with self:
            if self.current_chat_id is None:
                return

            self.processing = True
            answer = ""
            reasoning = ""

            # Get messages and verify index
            with rx.session() as session:
                chat = session.get(Chat, self.current_chat_id)
                if not chat:
                    return

                # Get messages up to and including the user message
                messages_before = chat.messages[: user_message_index + 1]

                # Verify the message at index is a user message
                if not messages_before or messages_before[-1].role != "user":
                    return

                # Delete all messages after this user message
                for msg in chat.messages[user_message_index + 1 :]:
                    session.delete(msg)

                # Create new assistant message
                assistant_msg = Message(role="assistant", chat_id=self.current_chat_id)
                session.add(assistant_msg)
                session.commit()
                assistant_id = assistant_msg.id

                # Load current state of messages plus the new assistant message
                self.messages = [
                    UIMessage(
                        role=msg.role, content=msg.content, reasoning=msg.reasoning
                    )
                    for msg in chat.messages
                ] + [UIMessage(role="assistant", content="", reasoning="")]

            # Create a temporary message list for the API that only includes up to user_message_index
            temp_messages = self.messages[: user_message_index + 1]

            # Temporarily set self.messages to get correct format_messages output
            original_messages = self.messages.copy()
            self.messages = temp_messages
            messages_for_api = self.format_messages()
            # Restore original messages to maintain UI state
            self.messages = original_messages

            # Process with AI
            client = AsyncOpenRouterAI(api_key=os.getenv("OPENROUTER_API_KEY"))

            try:
                processor = await client.chat.completions.create(
                    model=self.model,
                    messages=messages_for_api,
                    stream=True,
                    include_reasoning=True,
                )

                async for chunk in processor:
                    if not self.processing:
                        break

                    if chunk.content:
                        answer = answer + chunk.content if answer else chunk.content
                    if chunk.reasoning:
                        reasoning = (
                            reasoning + chunk.reasoning
                            if reasoning
                            else chunk.reasoning
                        )

                    # Update last message with current progress
                    messages = self.messages[:]
                    if messages:
                        messages[-1].content = answer
                        messages[-1].reasoning = reasoning
                        self.messages = messages

                # After streaming completes, update database
                with rx.session() as session:
                    assistant_msg = session.get(Message, assistant_id)
                    if assistant_msg:
                        assistant_msg.content = answer
                        assistant_msg.reasoning = reasoning
                        session.add(assistant_msg)

                        # Update chat timestamp
                        chat = session.get(Chat, self.current_chat_id)
                        if chat:
                            chat.updated_at = datetime.now(timezone.utc)
                            session.add(chat)
                        session.commit()

                        # Refresh messages from database
                        self.messages = [
                            UIMessage(
                                role=msg.role,
                                content=msg.content,
                                reasoning=msg.reasoning,
                            )
                            for msg in chat.messages
                        ]

            except Exception as e:
                error_message = f"Error: {str(e)}"
                messages = self.messages[:]
                if messages:
                    messages[-1].content = error_message
                    self.messages = messages

                with rx.session() as session:
                    assistant_msg = session.get(Message, assistant_id)
                    if assistant_msg:
                        assistant_msg.content = error_message
                        session.add(assistant_msg)
                        session.commit()

            finally:
                await client.close()
                self.processing = False

    @rx.event(background=True)
    async def save_edit(self):
        """Save the current edit."""
        async with self:
            if self.editing_user_message_index is not None:
                self.messages[self.editing_user_message_index].content = (
                    self.edit_content
                )

                # Save changes to database
                with rx.session() as session:
                    chat = session.get(Chat, self.current_chat_id)
                    if chat and self.editing_user_message_index < len(chat.messages):
                        msg = chat.messages[self.editing_user_message_index]
                        msg.content = self.edit_content
                        session.add(msg)
                        session.commit()

                # Store the index before clearing
                index_to_regenerate = self.editing_user_message_index

                # Cancel editing first
                yield State.cancel_editing

                # Then regenerate the response using the class name
                yield State.regenerate_response(index_to_regenerate)
                return

            elif self.editing_assistant_content_index is not None:
                self.messages[self.editing_assistant_content_index].content = (
                    self.edit_content
                )
                # Save changes to database
                with rx.session() as session:
                    chat = session.get(Chat, self.current_chat_id)
                    if chat and self.editing_assistant_content_index < len(
                        chat.messages
                    ):
                        msg = chat.messages[self.editing_assistant_content_index]
                        msg.content = self.edit_content
                        session.add(msg)
                        session.commit()

            elif self.editing_assistant_reasoning_index is not None:
                self.messages[self.editing_assistant_reasoning_index].reasoning = (
                    self.edit_content
                )
                # Save changes to database
                with rx.session() as session:
                    chat = session.get(Chat, self.current_chat_id)
                    if chat and self.editing_assistant_reasoning_index < len(
                        chat.messages
                    ):
                        msg = chat.messages[self.editing_assistant_reasoning_index]
                        msg.reasoning = self.edit_content
                        session.add(msg)
                        session.commit()

            # Cancel editing for non-user message edits
            yield State.cancel_editing

    @rx.event
    def cancel_editing(self):
        """Cancel all editing."""
        self.editing_user_message_index = None
        self.editing_assistant_content_index = None
        self.editing_assistant_reasoning_index = None
        self.edit_content = ""

    @rx.event
    def set_model(self, model: str):
        """Set the AI model to use."""
        self.model = model

    @rx.event
    def set_current_question(self, message: str):
        """Set the current message being typed."""
        self.current_question = message

    @rx.event
    def set_edit_content(self, content: str):
        """Set the content being edited."""
        self.edit_content = content

    @rx.event(background=True)
    async def stop_process(self):
        """Stop the current processing."""
        async with self:
            self.processing = False
