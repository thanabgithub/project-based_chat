import reflex as rx
from app.state import State
from app.styles import sidebar_style, button_base_style
from app.components.project_modal import project_modal

project_sidebar_style = {
    **sidebar_style,
    "background_color": "rgb(17, 24, 39)",  # bg-gray-900
    "color": "white",
}


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
                    style={
                        **button_base_style,
                        "color": "white",
                        "_hover": {
                            "background_color": "rgb(55, 65, 81)"
                        },  # bg-gray-700
                        "background_color": rx.cond(
                            p.id == State.current_project_id,
                            "rgb(55, 65, 81)",
                            "transparent",
                        ),
                    },
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
