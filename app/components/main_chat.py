import reflex as rx
from app.state import State

"""
current_project and current_chat are defined as computed vars 
using the @rx.var decorator in State class 
"""


def main_chat() -> rx.Component:
    """The main chat component."""
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.heading(
                    rx.cond(
                        State.current_project,
                        State.current_project.name,
                        "Select a Project",
                    )
                    + " / "
                    + rx.cond(
                        State.current_chat,
                        State.current_chat.name,
                        "Select a Chat",
                    ),
                    size="3",
                ),
                rx.spacer(),
                rx.button(
                    "Knowledge Base",
                    right_icon="chevron_right",
                    on_click=State.toggle_knowledge_base,
                ),
                width="100%",
                padding="1rem",
                border_bottom="1px solid rgb(229, 231, 235)",
            ),
            # Chat messages area (placeholder)
            rx.box(
                rx.text("No messages yet"),
                flex="1",
                padding="1rem",
                overflow="auto",
            ),
            # Input area
            rx.hstack(
                rx.input(
                    value=State.message,
                    placeholder="Type your message...",
                    on_change=State.set_message,
                    flex="1",
                ),
                rx.button("Send", on_click=State.send_message),
                padding="1rem",
                border_top="1px solid rgb(229, 231, 235)",
                width="100%",
            ),
            height="100%",
            overflow="hidden",
        ),
        flex="1",
        height="100%",
    )
