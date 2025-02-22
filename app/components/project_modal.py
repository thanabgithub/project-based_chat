import reflex as rx
from app.state import State


def project_modal() -> rx.Component:
    """The new project modal component."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("New Project"),
            rx.dialog.description(
                rx.form(
                    rx.flex(
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
                        rx.flex(
                            rx.dialog.close(
                                rx.button(
                                    "Cancel",
                                    variant="soft",
                                    color_scheme="gray",
                                ),
                            ),
                            rx.dialog.close(
                                rx.button(
                                    "Create",
                                    type="submit",
                                ),
                            ),
                            spacing="3",
                            justify="end",
                        ),
                        direction="column",
                        spacing="4",
                    ),
                    on_submit=State.create_project,
                    reset_on_submit=True,
                ),
            ),
            max_width="450px",
        ),
        # Use show_project_modal to control visibility
        open=State.show_project_modal,
        # Use set_show_project_modal to handle modal open/close
        on_open_change=State.set_show_project_modal,
    )
