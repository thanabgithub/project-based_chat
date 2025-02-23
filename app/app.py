"""Main app module."""

import json
from types import SimpleNamespace
from socketio import AsyncServer

import reflex as rx
from reflex.utils import format
from app.state import State
from app.styles import base_style
from app.components.project_sidebar import project_sidebar
from app.components.chat_sidebar import chat_sidebar
from app.components.main_chat import main_chat
from app.components.project_modal import project_modal

SIDEBAR_WIDTH = "30ch"
TWO_COLUMN_TEMPLATE = f"{SIDEBAR_WIDTH} 1fr"
THREE_COLUMN_TEMPLATE = f"{SIDEBAR_WIDTH} {SIDEBAR_WIDTH} 1fr"


def index() -> rx.Component:
    """Index page that redirects to projects."""
    return rx.box(
        on_mount=lambda: rx.call_script(f"window.location.href = '/projects'")
    )


def projects() -> rx.Component:
    """Projects page - shows all projects."""
    return rx.box(
        project_modal(),
        rx.grid(
            project_sidebar(),
            rx.vstack(
                rx.heading("Select a Project", size="3", padding="1rem"),
                rx.text("Choose a project from the sidebar to begin."),
                width="100%",
                height="100%",
                justify="center",
                align="center",
            ),
            grid_template_columns=TWO_COLUMN_TEMPLATE,
            spacing="0",
            height="100vh",
            overflow="hidden",
        ),
        style=base_style,
    )


def project_chats() -> rx.Component:
    """Project chats page - shows project's chats."""
    return rx.box(
        project_modal(),
        rx.grid(
            project_sidebar(),
            chat_sidebar(),
            rx.vstack(
                rx.heading("Select a Chat", size="3", padding="1rem"),
                rx.text("Choose a chat from the sidebar to begin."),
                width="100%",
                height="100%",
                justify="center",
                align="center",
            ),
            grid_template_columns=THREE_COLUMN_TEMPLATE,
            spacing="0",
            height="100vh",
            overflow="hidden",
        ),
        style=base_style,
    )


def chat_view() -> rx.Component:
    """Individual chat view."""
    return rx.box(
        project_modal(),
        rx.grid(
            project_sidebar(),
            chat_sidebar(),
            main_chat(),
            grid_template_columns=THREE_COLUMN_TEMPLATE,
            spacing="0",
            height="100vh",
            overflow="hidden",
        ),
        style=base_style,
    )


"""
don't override component style here because it will override all interactice effects.
"""

# this setup require to handle long textarea input
sio = AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=("*"),
    cors_credentials=True,
    max_http_buffer_size=50000000000,
    ping_interval=120,
    ping_timeout=240,
    json=SimpleNamespace(
        dumps=staticmethod(format.json_dumps),
        loads=staticmethod(json.loads),
    ),
)

# Create app and add pages
app = rx.App(
    theme=rx.theme(
        appearance="light",
        accent_color="gray",
        radius="large",
    ),
    sio=sio,
)

# Add routes
app.add_page(index)
app.add_page(projects, route="/projects", on_load=State.load_projects)
app.add_page(
    project_chats, route="/projects/[project_id]", on_load=State.handle_project_route
)
app.add_page(
    chat_view,
    route="/projects/[project_id]/chats/[chat_id]",
    on_load=State.handle_chat_route,
)
