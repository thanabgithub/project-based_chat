"""Chat sidebar component."""

import reflex as rx
from app.state import State
from app.styles import sidebar_style, button_base_style
from app.components.chat_modal import chat_modal

chat_sidebar_style = {
    **sidebar_style,
    "background_color": "rgb(249, 250, 251)",  # bg-gray-50
}


def chat_button(chat: rx.Var) -> rx.Component:
    return rx.context_menu.root(
        rx.context_menu.trigger(
            rx.link(
                rx.button(
                    rx.hstack(
                        rx.icon("message-square", size=20),
                        rx.text(chat.name),
                        width="100%",
                    ),
                    style=[
                        button_base_style,
                        {
                            "width": "100%",
                            "color": "black",
                            "_hover": {"background_color": "rgb(229, 231, 235)"},
                            "background_color": rx.cond(
                                chat.id == State.current_chat_id,
                                "rgb(229, 231, 235)",
                                "transparent",
                            ),
                        },
                    ],
                ),
                href=f"/projects/{State.current_project_id}/chats/{chat.id}",
                width="100%",
            ),
        ),
        rx.context_menu.content(
            rx.context_menu.item(
                "Edit",
                on_click=[
                    lambda: State.set_chat_to_edit(chat.id),
                    State.toggle_chat_modal,
                ],
            ),
            rx.context_menu.separator(),
            rx.context_menu.item(
                "Delete",
                color_scheme="red",
                on_click=lambda: State.delete_chat(chat.id),
            ),
        ),
    )


def chat_sidebar() -> rx.Component:
    """The chat sidebar component."""
    return rx.box(
        rx.hstack(
            rx.heading("Chats", size="4"),
            rx.button(
                rx.icon("plus", color="black"),
                on_click=State.toggle_chat_modal,
                is_disabled=rx.cond(State.current_project_id == None, True, False),
                style=button_base_style,
            ),
            justify="between",
            width="100%",
            padding_bottom="1rem",
        ),
        # Chat list
        rx.vstack(
            rx.foreach(
                State.project_chats,
                chat_button,
            ),
            width="100%",
            spacing="4",
            overflow="auto",
        ),
        chat_modal(),
        style=chat_sidebar_style,
    )
