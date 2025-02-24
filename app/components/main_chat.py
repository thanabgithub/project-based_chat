"""Chat interface components and styles."""

import reflex as rx
from app.state import State, Message

# Style Definitions
# Common styles with dict syntax
shadow = "rgba(0, 0, 0, 0.15) 0px 2px 8px"
message_style = dict(
    padding_inline="1em",
    margin_block="0.25em",
    border_radius="1rem",
    display="inline-block",
    color="black",
)

question_style = message_style | dict(
    width="100%",
    border="1px solid #E9E9E9",
    padding="1em",
    box_shadow="none",
)

answer_style = message_style | dict(
    background_color="#F9F9F9",
    border="1px solid #E9E9E9",
    box_shadow="none",
    width="100%",
)

# Container styles
input_container_style = dict(
    border="1px solid #E9E9E9",
    border_radius="15px",
    padding="1em",
    width="100%",
    background_color="white",
    box_shadow=shadow,
)

input_style = dict(
    border="none",
    padding="0.5em",
    width="100%",
    color="black",
    background_color="transparent",
    outline="none",
    box_shadow="none",
    font_size="1em",
    min_height="6em",
    height="100%",
    max_height="80vh",
    overflow_y="auto",
    resize="vertical",
    _focus={"border": "none", "outline": "none", "box_shadow": "none"},
    _placeholder={"color": "#A3A3A3"},
)

select_style = dict(
    border="1px solid #E9E9E9",
    padding="0.5em",
    border_radius="1em",
    background_color="#F5F5F5",
    color="black",
    width="auto",
    min_width="150px",
)

button_style = dict(
    background_color="#FFFFFF",
    border="1px solid #E9E9E9",
    border_radius="8px",
    padding="0.5em",
    color="black",
)

chat_style = dict(
    padding="2em",
    height="100vh",
    overflow_y="auto",
    background_color="white",
    color="black",
    scroll_behavior="smooth",
)


def copy_button(code: str) -> rx.Component:
    """Create a copy button for code blocks."""
    return rx.button(
        rx.icon("copy", size=20, color="black"),
        on_click=rx.set_clipboard(code),
        position="absolute",
        top="0.5em",
        right="0",
        background_color="transparent",
    )


def code_block_with_copy(code: str, **props) -> rx.Component:
    """Create a code block with a copy button."""
    return rx.box(
        rx.code_block(
            code,
            margin_y="1em",
            **props,
        ),
        copy_button(code),
        position="relative",
    )


content_component_map = {
    "codeblock": code_block_with_copy,
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
                        rx.select(
                            [
                                "mistralai/codestral-2501",
                                "aion-labs/aion-1.0",
                                "deepseek/deepseek-r1",
                                "openai/gpt-4o-mini",
                                "google/gemini-2.0-flash-thinking-exp:free",
                            ],
                            placeholder=State.model,
                            disabled=State.processing,
                            on_change=State.set_model,
                            style=select_style,
                        ),
                        rx.spacer(),
                        rx.button(
                            "Cancel",
                            on_click=State.cancel_editing,
                            style=button_style,
                        ),
                        rx.button(
                            "Update",
                            type="submit",
                            style=button_style,
                        ),
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
                    style=question_style,
                    white_space="pre-wrap",
                ),
                width="80%",
                margin_left="20%",
            ),
        ),
        rx.context_menu.content(
            rx.context_menu.item(
                "Edit Message",
                on_click=lambda: State.start_editing(index, "content"),
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
                            component_map=content_component_map,
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


def assistant_reasoning_section(msg: Message, index: int) -> rx.Component:
    return rx.cond(
        State.editing_assistant_reasoning_index == index,
        editing_message_input(index),
        rx.cond(
            msg.reasoning != None,
            rx.context_menu.root(
                rx.context_menu.trigger(
                    rx.blockquote(
                        rx.markdown(msg.reasoning),
                        width="100%",
                        size="1",
                    )
                ),
                rx.context_menu.content(
                    rx.context_menu.item(
                        "Edit Reasoning",
                        on_click=lambda: State.start_editing(index, "reasoning"),
                    )
                ),
            ),
        ),
    )


def assistant_content_section(msg: Message, index: int) -> rx.Component:
    return rx.cond(
        State.editing_assistant_content_index == index,
        editing_message_input(index),
        rx.cond(
            msg.content != None,
            rx.context_menu.root(
                rx.context_menu.trigger(
                    rx.box(
                        rx.markdown(
                            msg.content,
                            component_map=content_component_map,
                            style=answer_style,
                        ),
                        width="100%",
                    )
                ),
                rx.context_menu.content(
                    rx.context_menu.item(
                        "Edit Content",
                        on_click=lambda: State.start_editing(index, "content"),
                    )
                ),
            ),
        ),
    )


def message(msg: Message, index: int) -> rx.Component:
    return rx.cond(
        msg.role == "user",
        rx.cond(
            State.editing_user_message_index == index,
            editing_message_input(index),
            user_message(msg, index),
        ),
        rx.vstack(
            assistant_reasoning_section(msg, index),
            assistant_content_section(msg, index),
            align="start",
            width="100%",
        ),
    )


def action_bar() -> rx.Component:
    """Input bar for sending messages."""
    return rx.cond(
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
                            value=State.current_question,
                            placeholder="Ask me anything...",
                            on_change=State.set_current_question,
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
                            justify="between",
                            width="100%",
                        ),
                    ),
                    on_submit=State.process_question,
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
        rx.cond(
            ~State.messages.length(),
            rx.heading(
                "お手伝いできることはありますか?",
                size="8",
                color="black",
                text_align="center",
                margin_top="20%",
                margin_bottom="5%",
            ),
            rx.box(),
        ),
        rx.foreach(
            State.messages,
            message,
        ),
        align="center",
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
