import reflex as rx
from app.state import State, Message

# Styles
shadow = "rgba(0, 0, 0, 0.15) 0px 2px 8px"
message_style = {
    "padding_inline": "1em",
    "margin_block": "0.25em",
    "border_radius": "1rem",
    "display": "inline-block",
    "color": "black",
    "width": "100%",
    "border": "1px solid #E9E9E9",
    "box_shadow": "none",
}

answer_style = {
    **message_style,
    "background_color": "#F9F9F9",
}

input_style = {
    "border": "none",
    "padding": "0.5em",
    "width": "100%",
    "color": "black",
    "background_color": "transparent",
    "outline": "none",
    "box_shadow": "none",
    "font_size": "1em",
    "min_height": "6em",
    "height": "100%",
    "max_height": "60vh",
    "overflow_y": "auto",
    "resize": "vertical",
    "_focus": {"border": "none", "outline": "none", "box_shadow": "none"},
    "_placeholder": {"color": "#A3A3A3"},
}

input_container_style = {
    "border": "1px solid #E9E9E9",
    "border_radius": "15px",
    "padding": "1em",
    "width": "100%",
    "background_color": "white",
    "box_shadow": shadow,
}

select_style = {
    "border": "1px solid #E9E9E9",
    "padding": "0.5em",
    "border_radius": "1em",
    "background_color": "#F5F5F5",
    "color": "black",
    "width": "auto",
    "min_width": "150px",
}

button_style = {
    "background_color": "#FFFFFF",
    "border": "1px solid #E9E9E9",
    "border_radius": "8px",
    "padding": "0.5em",
    "color": "black",
}

chat_style = {
    "padding": "2em",
    "height": "100vh",
    "overflow_y": "auto",
    "background_color": "white",
    "color": "black",
    "scroll_behavior": "smooth",
}


def editing_message_input(index: int) -> rx.Component:
    """Input component for editing messages."""
    return rx.box(
        rx.vstack(
            rx.form(
                rx.vstack(
                    rx.text_area(
                        value=State.edit_content,
                        placeholder="Edit your message...",
                        on_change=State.set_edit_content,
                        style=input_style,
                    ),
                    rx.hstack(
                        rx.button(
                            "Cancel", on_click=State.cancel_editing, style=button_style
                        ),
                        rx.button("Update", type="submit", style=button_style),
                        justify="end",
                        width="100%",
                    ),
                ),
                on_submit=State.save_edit,
            ),
            width="100%",
        ),
        style=input_container_style,
    )


def user_message(msg: Message, index: int) -> rx.Component:
    """Render a user message."""
    return rx.context_menu.root(
        rx.context_menu.trigger(
            rx.box(
                rx.text(
                    msg.content,
                    style=message_style,
                    white_space="pre-wrap",
                ),
                width="80%",
                margin_left="20%",
            ),
        ),
        rx.context_menu.content(
            rx.context_menu.item(
                "Edit Message", on_click=lambda: State.start_editing(index, "content")
            ),
            rx.context_menu.separator(),
            rx.context_menu.item(
                "Delete Message",
                color_scheme="red",
                on_click=lambda: State.delete_message(index),
            ),
        ),
    )


def assistant_message(msg: Message, index: int) -> rx.Component:
    """Render an assistant message."""
    return rx.vstack(
        # Reasoning section
        rx.cond(
            msg.reasoning != None,
            rx.context_menu.root(
                rx.context_menu.trigger(
                    rx.blockquote(
                        rx.markdown(msg.reasoning),
                        width="100%",
                        size="1",
                    ),
                ),
                rx.context_menu.content(
                    rx.context_menu.item(
                        "Edit Reasoning",
                        on_click=lambda: State.start_editing(index, "reasoning"),
                    ),
                    rx.context_menu.separator(),
                    rx.context_menu.item(
                        "Delete Message",
                        color_scheme="red",
                        on_click=lambda: State.delete_message(index),
                    ),
                ),
            ),
            rx.box(),
        ),
        # Content section
        rx.cond(
            msg.content != None,
            rx.context_menu.root(
                rx.context_menu.trigger(
                    rx.box(
                        rx.markdown(
                            msg.content,
                            style=answer_style,
                        ),
                        width="100%",
                    ),
                ),
                rx.context_menu.content(
                    rx.context_menu.item(
                        "Edit Content",
                        on_click=lambda: State.start_editing(index, "content"),
                    ),
                    rx.context_menu.separator(),
                    rx.context_menu.item(
                        "Delete Message",
                        color_scheme="red",
                        on_click=lambda: State.delete_message(index),
                    ),
                ),
            ),
            rx.box(),
        ),
        align="start",
        width="100%",
    )


def message(msg: Message, index: int) -> rx.Component:
    """Render a message with proper editing states.

    Uses rx.cond and bitwise operators to handle state comparisons since we're working
    with JavaScript expressions rather than Python boolean values.
    """
    return rx.cond(
        # First check if we're editing this message
        (State.editing_user_message_index == index)
        | (State.editing_assistant_content_index == index)
        | (State.editing_assistant_reasoning_index == index),
        # If editing, show the edit input
        editing_message_input(index),
        # If not editing, show the appropriate message type
        rx.cond(
            msg.role == "user",
            user_message(msg, index),
            assistant_message(msg, index),
        ),
    )


def action_bar() -> rx.Component:
    """Input bar for sending messages."""
    return rx.cond(
        # Check if any editing state is active using bitwise OR
        (State.editing_user_message_index != None)
        | (State.editing_assistant_content_index != None)
        | (State.editing_assistant_reasoning_index != None),
        rx.fragment(),
        rx.box(
            rx.vstack(
                rx.form(
                    rx.vstack(
                        rx.text_area(
                            id="input-textarea--action-bar",
                            value=State.current_message,
                            placeholder="Ask me anything...",
                            on_change=State.set_current_message,
                            style=input_style,
                            on_key_down=State.handle_action_bar_keydown,
                        ),
                        rx.hstack(
                            rx.select(
                                [
                                    "mistralai/codestral-2501",
                                    "aion-labs/aion-1.0",
                                    "google/gemini-2.0-flash-thinking-exp:free",
                                    "deepseek/deepseek-r1",
                                    "openai/gpt-4o-mini",
                                ],
                                placeholder=State.model,
                                disabled=State.processing,
                                on_change=State.set_model,
                                style=select_style,
                            ),
                            rx.spacer(),
                            rx.cond(
                                State.processing,
                                rx.button(
                                    rx.icon("circle-stop", color="crimson"),
                                    on_click=State.stop_process,
                                    style={
                                        "background_color": "transparent",
                                        "border": "0px solid #E9E9E9",
                                        "color": "black",
                                    },
                                ),
                                rx.button(
                                    rx.icon("arrow-right"),
                                    type="submit",
                                    style={
                                        "background_color": "transparent",
                                        "border": "0px solid #E9E9E9",
                                        "color": "black",
                                    },
                                ),
                            ),
                        ),
                    ),
                    on_submit=State.process_message,
                ),
                width="100%",
            ),
            style=input_container_style,
            position="sticky",
            bottom="0",
        ),
    )


def chat_messages() -> rx.Component:
    """Render all chat messages."""
    return rx.vstack(
        rx.foreach(
            State.messages,
            message,
        ),
        align="start",
        width="100%",
        padding_bottom="5em",
    )


def main_chat() -> rx.Component:
    """Main chat component."""
    return rx.box(
        rx.vstack(
            chat_messages(),
            action_bar(),
        ),
        style=chat_style,
    )
