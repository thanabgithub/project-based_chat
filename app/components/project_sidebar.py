"""Project sidebar component."""

import reflex as rx
from app.state import State
from app.styles import sidebar_style, button_base_style
from app.components.project_modal import project_modal

project_sidebar_style = {
    **sidebar_style,
    "background_color": "rgb(17, 24, 39)",  # bg-gray-900
    "color": "white",
}


def project_button(p: rx.Var) -> rx.Component:
    return rx.context_menu.root(
        rx.context_menu.trigger(
            rx.link(
                rx.button(
                    rx.hstack(
                        rx.icon(
                            "folder",
                            size=20,
                        ),
                        rx.text(p.name),
                        width="100%",
                    ),
                    style=[
                        button_base_style,
                        {
                            "width": "100%",
                            "color": "white",
                            "_hover": {"background_color": "rgb(55, 65, 81)"},
                            "background_color": rx.cond(
                                p.id == State.current_project_id,
                                "rgb(55, 65, 81)",
                                "transparent",
                            ),
                        },
                    ],
                ),
                href=f"/projects/{p.id}",
                width="100%",
            ),
        ),
        rx.context_menu.content(
            rx.context_menu.item(
                "Edit",
                on_click=[
                    lambda: State.set_project_to_edit(p.id),
                    State.toggle_project_modal,
                ],
            ),
            rx.context_menu.separator(),
            rx.context_menu.item(
                "Delete",
                color_scheme="red",
                on_click=lambda: State.delete_project(p.id),
            ),
        ),
    )


def project_sidebar() -> rx.Component:
    """The project sidebar component."""
    return rx.box(
        rx.hstack(
            rx.heading("Projects", size="4"),
            rx.button(
                rx.icon("plus"),
                on_click=State.toggle_project_modal,
                style=button_base_style,
            ),
            justify="between",
            width="100%",
            padding_bottom="1rem",
        ),
        rx.vstack(
            rx.foreach(
                State.projects,
                project_button,
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
