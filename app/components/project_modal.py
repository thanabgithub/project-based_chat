import reflex as rx
from app.state import State


def show_document(doc):
    return rx.hstack(
        rx.icon("file-text"),
        rx.text(doc.name),
        rx.spacer(),
        rx.button(
            rx.icon("delete"), on_click=State.delete_document(doc.id), variant="ghost"
        ),
        width="100%",
    )


def project_modal() -> rx.Component:
    """The project modal component - handles both create and edit."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(State.project_modal_title),
            rx.dialog.description(
                rx.form(
                    rx.flex(
                        # Project basic info
                        rx.input(
                            placeholder="Project Name",
                            name="name",
                            value=rx.cond(
                                State.project_to_edit_data,
                                State.project_to_edit_data.name,
                                "",
                            ),
                            required=True,
                            on_change=State.set_project_name,
                            default_value=State.project_name,
                        ),
                        rx.text_area(
                            placeholder="Project Description",
                            name="description",
                            value=rx.cond(
                                State.project_to_edit_data,
                                State.project_to_edit_data.description,
                                "",
                            ),
                            on_change=State.set_project_description,
                        ),
                        rx.text_area(
                            placeholder="System Instructions",
                            name="system_instructions",
                            value=rx.cond(
                                State.project_to_edit_data,
                                State.project_to_edit_data.system_instructions,
                                "",
                            ),
                            on_change=State.set_project_system_instructions,
                        ),
                        # Knowledge Base Documents Section
                        rx.vstack(
                            rx.heading("Knowledge Base Documents", size="5"),
                            # Show existing documents if editing
                            rx.cond(
                                State.project_to_edit_data,
                                rx.foreach(
                                    State.project_to_edit_data.knowledge,
                                    lambda doc: rx.hstack(
                                        rx.icon("file-text"),
                                        rx.text(doc.name),
                                        rx.spacer(),
                                        rx.button(
                                            rx.icon("delete"),
                                            on_click=State.delete_document(doc.id),
                                            variant="ghost",
                                        ),
                                        width="100%",
                                    ),
                                ),
                            ),
                            # Document Modal
                            rx.dialog.root(
                                rx.dialog.trigger(
                                    rx.button(
                                        "Add Document",
                                        variant="soft",
                                    ),
                                ),
                                rx.dialog.content(
                                    rx.dialog.title("Add Document"),
                                    rx.dialog.description(
                                        rx.form(
                                            rx.flex(
                                                rx.input(
                                                    placeholder="Document Name",
                                                    name="name",
                                                    required=True,
                                                ),
                                                rx.text_area(
                                                    placeholder="Document Content",
                                                    name="content",
                                                    height="200px",
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
                                                            "Add",
                                                            type="submit",
                                                        ),
                                                    ),
                                                    spacing="3",
                                                    justify="end",
                                                ),
                                                direction="column",
                                                spacing="4",
                                            ),
                                            on_submit=State.handle_document_submit,
                                            reset_on_submit=True,
                                        ),
                                    ),
                                    max_width="450px",
                                ),
                            ),
                            width="100%",
                            align_items="start",
                        ),
                        # Project modal buttons
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
