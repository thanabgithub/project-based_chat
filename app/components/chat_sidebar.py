import reflex as rx
from app.state import State
from app.styles import chat_sidebar_style, button_style, selected_button_style


def chat_sidebar() -> rx.Component:
    """The chat sidebar component."""
    return rx.box(
        rx.hstack(
            rx.heading("Chats", size="md"),
            rx.button(
                rx.icon("add"),
                on_click=lambda: None,  # TODO: Implement new chat
            ),
            justify="space-between",
            width="100%",
            padding_bottom="1rem",
        ),
        rx.vstack(
            rx.button(
                rx.hstack(
                    rx.icon("chat"),
                    rx.text("Chat 1"),
                    width="100%",
                ),
                style=button_style,
            ),
            rx.button(
                rx.hstack(
                    rx.icon("chat"),
                    rx.text("Chat 2"),
                    width="100%",
                ),
                style=button_style,
            ),
            width="100%",
            spacing="0.5rem",
            overflow="auto",
        ),
        style=chat_sidebar_style,
    )
