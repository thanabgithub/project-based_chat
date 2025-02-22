import reflex as rx
from app.state import State


def chat_modal() -> rx.Component:
    """The chat modal component - handles both create and edit."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(State.chat_modal_title),
            rx.dialog.description(
                rx.form(
                    rx.flex(
                        rx.input(
                            placeholder="Chat Name",
                            name="name",
                            value=rx.cond(
                                State.chat_to_edit_data,
                                State.chat_to_edit_data.name,
                                "",
                            ),
                            required=True,
                            on_change=State.set_chat_name,
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
                    on_submit=State.handle_chat_submit,
                    reset_on_submit=True,
                ),
            ),
            max_width="450px",
        ),
        open=State.show_chat_modal,
        on_open_change=State.set_show_chat_modal,
    )
