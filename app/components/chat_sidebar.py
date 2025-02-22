"""Chat sidebar component."""

import reflex as rx
from app.state import State
from app.styles import sidebar_style, button_base_style
from app.components.chat_modal import chat_modal

chat_sidebar_style = {
    **sidebar_style,
    "background_color": "rgb(249, 250, 251)",  # bg-gray-50
}


def chat_button(chat: rx.Var) -> rx.Component:
    return rx.context_menu.root(
        rx.context_menu.trigger(
            rx.link(
                rx.button(
                    rx.hstack(
                        rx.icon("message-square", size=20),
                        rx.text(chat.name),
                        width="100%",
                    ),
                    style=[
                        button_base_style,
                        {
                            "width": "100%",
                            "color": "black",
                            "_hover": {"background_color": "rgb(229, 231, 235)"},
                            "background_color": rx.cond(
                                chat.id == State.current_chat_id,
                                "rgb(229, 231, 235)",
                                "transparent",
                            ),
                        },
                    ],
                ),
                href=f"/projects/{State.current_project_id}/chats/{chat.id}",
                width="100%",
            ),
        ),
        rx.context_menu.content(
            rx.context_menu.item(
                "Edit",
                on_click=[
                    lambda: State.set_chat_to_edit(chat.id),
                    State.toggle_chat_modal,
                ],
            ),
            rx.context_menu.separator(),
            rx.context_menu.item(
                "Delete",
                color_scheme="red",
                on_click=lambda: State.delete_chat(chat.id),
            ),
        ),
    )


def chat_sidebar() -> rx.Component:
    """The chat sidebar component."""
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.heading("Chats", size="4"),
                rx.button(
                    rx.icon("plus", color="black"),
                    on_click=State.toggle_chat_modal,
                    is_disabled=rx.cond(State.current_project_id == None, True, False),
                    style=button_base_style,
                ),
                justify="between",
                width="100%",
                padding_bottom="1rem",
            ),
            # Chat list
            rx.vstack(
                rx.foreach(
                    State.project_chats,
                    chat_button,
                ),
                width="100%",
                spacing="4",
                overflow="auto",
            ),
            width="100%",
            height="100%",
        ),
        chat_modal(),
        style=chat_sidebar_style,
    )

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
