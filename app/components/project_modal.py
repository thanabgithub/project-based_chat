import reflex as rx
from app.state import State


def project_modal() -> rx.Component:
    """The project modal component - handles both create and edit."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(State.project_modal_title),
            rx.dialog.description(
                rx.form(
                    rx.flex(
                        rx.input(
                            placeholder="Project Name",
                            name="name",
                            value=rx.cond(
                                State.project_to_edit_data,
                                State.project_to_edit_data.name,
                                "",
                            ),
                            required=True,
                            on_change=State.set_project_name,  # Add handler
                        ),
                        rx.text_area(
                            placeholder="Project Description",
                            name="description",
                            value=rx.cond(
                                State.project_to_edit_data,
                                State.project_to_edit_data.description,
                                "",
                            ),
                            on_change=State.set_project_description,  # Add handler
                        ),
                        rx.text_area(
                            placeholder="System Instructions",
                            name="system_instructions",
                            value=rx.cond(
                                State.project_to_edit_data,
                                State.project_to_edit_data.system_instructions,
                                "",
                            ),
                            on_change=State.set_project_system_instructions,  # Add handler
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
                                    "Done",
                                    type="submit",
                                ),
                            ),
                            spacing="3",
                            justify="end",
                        ),
                        direction="column",
                        spacing="4",
                    ),
                    on_submit=State.handle_project_submit,
                    reset_on_submit=True,
                ),
            ),
            max_width="450px",
        ),
        open=State.show_project_modal,
        on_open_change=State.set_show_project_modal,
    )
