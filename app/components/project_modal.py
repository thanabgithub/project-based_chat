import reflex as rx
from app.state import State
from app.styles import modal_style


def project_modal() -> rx.Component:
    """The new project modal component."""
    return rx.modal(
        rx.modal_overlay(
            rx.modal_content(
                rx.modal_header(
                    rx.heading("New Project", size="lg"),
                ),
                rx.modal_body(
                    rx.form(
                        rx.vstack(
                            rx.input(
                                placeholder="Project Name",
                                name="name",
                                required=True,
                            ),
                            rx.text_area(
                                placeholder="Project Description",
                                name="description",
                            ),
                            rx.text_area(
                                placeholder="System Instructions",
                                name="system_instructions",
                            ),
                            rx.hstack(
                                rx.button(
                                    "Cancel",
                                    type_="button",
                                    on_click=State.toggle_project_modal,
                                ),
                                rx.button(
                                    "Create",
                                    type_="submit",
                                ),
                                justify="end",
                                width="100%",
                            ),
                            width="100%",
                            spacing="1rem",
                        ),
                        on_submit=State.create_project,
                    ),
                ),
                style=modal_style,
            ),
        ),
        is_open=State.show_project_modal,
    )
