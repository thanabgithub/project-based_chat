"""Project sidebar component."""

import reflex as rx
from app.state import State
from app.styles import sidebar_style
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
                lambda p: rx.link(
                    rx.button(
                        rx.hstack(
                            rx.icon("folder"),
                            rx.text(p.name),
                            width="100%",
                        ),
                        style={
                            "width": "100%",
                            "color": "white",
                            "_hover": {"background_color": "rgb(55, 65, 81)"},
                            "background_color": rx.cond(
                                p.id == State.current_project_id,
                                "rgb(55, 65, 81)",
                                "transparent",
                            ),
                        },
                    ),
                    href=f"/projects/{p.id}",
                    width="100%",
                ),
            ),
            width="100%",
            height="100%",
            spacing="4",
            overflow="auto",
            flex="1",
        ),
        project_modal(),
        style=project_sidebar_style,
    )
