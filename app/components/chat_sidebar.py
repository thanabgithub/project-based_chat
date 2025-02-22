import reflex as rx
from app.state import State
from app.styles import chat_sidebar_style, button_style, selected_button_style
from app.components.chat_modal import chat_modal


def chat_sidebar() -> rx.Component:
    """The chat sidebar component."""
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.heading("Chats", size="4"),
                rx.button(
                    rx.icon("plus"),
                    on_click=State.toggle_chat_modal,
                    # Only enable if project is selected
                    is_disabled=rx.cond(State.current_project_id == None, True, False),
                ),
                justify="between",
                width="100%",
                padding_bottom="1rem",
            ),
            # Chat list
            rx.vstack(
                rx.foreach(
                    State.project_chats,
                    lambda chat: rx.button(
                        rx.hstack(
                            rx.icon("message-square"),
                            rx.text(chat.name),
                            width="100%",
                        ),
                        on_click=lambda: State.select_chat(chat.id),
                        style=rx.cond(
                            chat.id == State.current_chat_id,
                            selected_button_style,
                            button_style,
                        ),
                    ),
                ),
                width="100%",
                spacing="4",
                overflow="auto",
            ),
            width="100%",
            height="100%",
        ),
        # Add chat modal
        chat_modal(),
        style=chat_sidebar_style,
    )
