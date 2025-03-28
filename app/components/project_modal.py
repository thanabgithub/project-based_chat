import reflex as rx
from app.state import State


def document_modal() -> rx.Component:
    """Document modal for adding/editing documents."""
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.button(
                "Add Document",
                variant="soft",
            ),
        ),
        rx.dialog.content(
            rx.dialog.title(
                rx.cond(State.document_to_edit_id, "Edit Document", "Add Document")
            ),
            rx.dialog.description(
                rx.flex(
                    rx.input(
                        value=State.document_name,
                        on_change=State.set_document_name,
                        placeholder="Document Name",
                        name="name",
                        required=True,
                    ),
                    rx.text_area(
                        value=State.document_content,
                        on_change=State.set_document_content,
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
                                on_click=State.clear_document_form,
                            ),
                        ),
                        rx.dialog.close(
                            rx.button(
                                "Save",
                                on_click=State.handle_document_submit,
                            ),
                        ),
                        spacing="3",
                        justify="end",
                    ),
                    direction="column",
                    spacing="4",
                )
            ),
            max_width="450px",
        ),
        open=State.show_document_modal,
        on_open_change=State.set_show_document_modal,
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
                        # Show pending documents if creating a new project.
                        rx.heading("Knowledge Base Documents", size="5"),
                        rx.cond(
                            State.project_to_edit_data,  # Editing: show existing documents
                            rx.vstack(
                                rx.foreach(
                                    State.project_to_edit_data.knowledge,
                                    lambda doc: rx.context_menu.root(
                                        rx.context_menu.trigger(
                                            rx.hstack(
                                                rx.icon("file-text", size=20),
                                                rx.text(doc.name),
                                                width="100%",
                                            ),
                                        ),
                                        rx.context_menu.content(
                                            rx.context_menu.item(
                                                "Edit",
                                                on_click=[
                                                    lambda: State.set_document_to_edit(
                                                        doc.id, doc.name, doc.content
                                                    ),
                                                    lambda: State.toggle_document_modal(),
                                                ],
                                            ),
                                            rx.context_menu.separator(),
                                            rx.context_menu.item(
                                                "Delete",
                                                color_scheme="red",
                                                on_click=lambda: State.delete_document(
                                                    doc.id
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                                document_modal(),
                                width="100%",
                                align_items="start",
                            ),
                            # Else: New project – show pending documents from the state.
                            rx.vstack(
                                rx.foreach(
                                    State.pending_documents,
                                    lambda doc: rx.hstack(
                                        rx.icon("file-text", size=20),
                                        rx.text(doc["name"]),
                                        spacing="2",
                                    ),
                                ),
                                document_modal(),
                                width="100%",
                                align_items="start",
                            ),
                        ),
                        # Project modal buttons using best practice with rx.dialog.close
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
