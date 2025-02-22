"""Main app module."""

import reflex as rx
from app.components.project_sidebar import project_sidebar
from app.components.chat_sidebar import chat_sidebar
from app.components.main_chat import main_chat
from app.components.project_modal import project_modal
from app.components.knowledge_base import knowledge_base
from app.components.chat_modal import chat_modal
from app.state import State
from app.styles import base_style


def index() -> rx.Component:
    """The main page."""
    return rx.box(
        # Add the modal here at the root level
        project_modal(),
        rx.hstack(
            # Left sidebar - Projects
            project_sidebar(),
            # Middle sidebar - Chats
            chat_sidebar(),
            # Right area - Chat and Knowledge Base
            rx.hstack(
                # Main chat area
                main_chat(),
                height="100%",
                width="100%",
                flex="1",
                overflow="hidden",
            ),
            spacing="0",
            height="100vh",
            overflow="hidden",
        ),
        style=base_style,
    )


style = {
    rx.button: {
        "padding": "0.5rem 1rem",
        "border_radius": "0.375rem",
        "text_align": "left",
        "background_color": "transparent",
    }
}
# Create the app
app = rx.App(
    theme=rx.theme(
        appearance="light",
        accent_color="gray",
        radius="medium",
    ),
    style=style,
)

# Add page and load projects on page load
app.add_page(index, on_load=State.load_projects)
