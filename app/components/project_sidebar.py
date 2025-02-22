import reflex as rx
from app.state import State
from app.styles import project_sidebar_style, button_style, selected_button_style


def project_sidebar() -> rx.Component:
    """The project sidebar component."""
    return rx.box(
        rx.hstack(
            rx.heading("Projects", size="md"),
            rx.button(
                rx.icon("add"),
                on_click=State.toggle_project_modal,
            ),
            justify="space-between",
            width="100%",
            padding_bottom="1rem",
        ),
        rx.vstack(
            rx.foreach(
                State.projects,
                lambda p: rx.button(
                    rx.hstack(
                        rx.icon("folder"),
                        rx.text(p.name),
                        width="100%",
                    ),
                    on_click=lambda: State.select_project(p.id),
                    style=(
                        selected_button_style
                        if p.id == State.current_project_id
                        else button_style
                    ),
                ),
            ),
            width="100%",
            spacing="0.5rem",
            overflow="auto",
            flex="1",
        ),
        rx.button(
            rx.hstack(
                rx.icon("settings"),
                rx.text("Settings"),
                width="100%",
            ),
            style=button_style,
        ),
        style=project_sidebar_style,
    )
