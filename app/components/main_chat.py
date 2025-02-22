import reflex as rx
from app.state import State


def main_chat() -> rx.Component:
    """The main chat component."""
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.heading(
                    (
                        State.current_project.name
                        if State.current_project
                        else "Select a Project"
                    ),
                    size="lg",
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
                    placeholder="Type your message...",
                    flex="1",
                ),
                rx.button("Send", on_click=lambda: None),  # TODO: Implement send
                padding="1rem",
                border_top="1px solid rgb(229, 231, 235)",
            ),
            height="100%",
            overflow="hidden",
        ),
        flex="1",
        height="100%",
    )
