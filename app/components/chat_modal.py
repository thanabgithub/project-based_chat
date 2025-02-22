import reflex as rx
from app.state import State


def chat_modal() -> rx.Component:
    """The new chat modal component."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("New Chat"),
            rx.dialog.description(
                rx.form(
                    rx.flex(
                        rx.input(
                            placeholder="Chat Name",
                            name="name",
                            required=True,
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
                    on_submit=State.create_chat,
                    reset_on_submit=True,
                ),
            ),
            max_width="450px",
        ),
        open=State.show_chat_modal,
        on_open_change=lambda show: State.set_show_chat_modal(show),
    )
