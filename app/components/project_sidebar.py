import reflex as rx
from app.state import State
from app.styles import project_sidebar_style, button_style, selected_button_style
from app.components.project_modal import project_modal


def project_sidebar() -> rx.Component:
    """The project sidebar component."""
    return rx.box(
        rx.hstack(
            rx.heading("Projects", size="4"),
            rx.button(
                rx.icon("plus"),
                on_click=State.toggle_project_modal,
            ),
            justify="between",
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
                    style=rx.cond(
                        p.id == State.current_project_id,
                        selected_button_style,
                        button_style,
                    ),
                ),
            ),
            width="100%",
            spacing="4",
            overflow="auto",
            flex="1",
        ),
        # Add the modal component
        project_modal(),
        style=project_sidebar_style,
    )
