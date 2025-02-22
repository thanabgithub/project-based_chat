import reflex as rx
from app.components.project_sidebar import project_sidebar
from app.components.chat_sidebar import chat_sidebar
from app.components.main_chat import main_chat
from app.components.project_modal import project_modal
from app.components.knowledge_base import knowledge_base
from app.styles import base_style


def index() -> rx.Component:
    """The main page."""
    return rx.box(
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
        # Modal for creating new projects
        style=base_style,
    )


# Create the app
app = rx.App(
    theme=rx.theme(
        appearance="light",
        accent_color="gray",
        radius="medium",
    )
)
app.add_page(index)
