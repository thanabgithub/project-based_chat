import asyncio
import reflex as rx
from app.state import State, Message

# -----------------------------------------------------------------------------
# Styles (these can be moved to a separate file if desired)
# -----------------------------------------------------------------------------

shadow = "rgba(0, 0, 0, 0.15) 0px 2px 8px"
message_style = {
    "padding_inline": "1em",
    "margin_block": "0.25em",
    "border_radius": "1rem",
    "display": "inline-block",
    "color": "black",
}
question_style = {
    **message_style,
    **{"width": "100%", "border": "1px solid #E9E9E9", "box_shadow": "none"},
}
answer_style = {
    **message_style,
    **{
        "background_color": "#F9F9F9",
        "border": "1px solid #E9E9E9",
        "box_shadow": "none",
        "width": "100%",
    },
}

input_container_style = {
    "border": "1px solid #E9E9E9",
    "border_radius": "15px",
    "padding": "1em",
    "width": "100%",
    "background_color": "white",
    "box_shadow": shadow,
}
form_style = {
    "width": "100%",
    "border": "none",
    "outline": "none",
    "box_shadow": "none",
    "_focus": {"border": "none", "outline": "none", "box_shadow": "none"},
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
controls_style = {"padding_top": "0.5em", "gap": "2", "width": "100%"}
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
context_menu_style = {
    "background_color": "white",
    "border": "1px solid #E9E9E9",
    "border_radius": "8px",
    "padding": "0.5em",
    "box_shadow": shadow,
    "color": "black",
}
copy_button_style = {
    "position": "absolute",
    "bottom": "0.5em",
    "right": "0.5em",
    "background_color": "white",
    "border": "1px solid #E9E9E9",
    "border_radius": "4px",
    "padding": "0.3em",
    "cursor": "pointer",
    "opacity": "0",
    "transition": "opacity 0.2s",
    "_hover": {"opacity": 1},
}

chat_style = {
    "padding": "2em",
    "height": "100vh",
    "overflow_y": "auto",
    "background_color": "white",
    "color": "black",
    "scroll_behavior": "smooth",
}

# -----------------------------------------------------------------------------
# UI Helper Components
# -----------------------------------------------------------------------------


class CopyState(rx.State):
    """State for managing copy button icons."""

    copied_indices: dict[str, bool] = {}

    @rx.event(background=True)
    async def copy_and_reset(self, text: str, index: str):
        yield rx.set_clipboard(text)
        async with self:
            self.copied_indices[index] = True
            yield
        await asyncio.sleep(1)
        async with self:
            self.copied_indices[index] = False
            yield


def editing_user_input(index: int) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.form(
                rx.vstack(
                    rx.text_area(
                        value=State.question,
                        placeholder="Edit your message...",
                        on_change=State.set_question,
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
                            "Cancel", on_click=State.cancel_editing, style=button_style
                        ),
                        rx.button("Update", type="submit", style=button_style),
                        justify="end",
                        width="100%",
                    ),
                ),
                on_submit=State.update_user_message,
            ),
            width="100%",
        ),
        style=input_container_style,
    )


def editing_assistant_content(index: int) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.form(
                rx.vstack(
                    rx.text_area(
                        value=State.answer,
                        placeholder="Edit the content...",
                        on_change=State.set_answer,
                        style={
                            **input_style,
                            "padding_inline": 0,
                            "background_color": "transparent",
                        },
                    ),
                    rx.hstack(
                        rx.spacer(),
                        rx.button(
                            "Cancel", on_click=State.cancel_editing, style=button_style
                        ),
                        rx.button("Update", type="submit", style=button_style),
                        justify="end",
                        width="100%",
                    ),
                ),
                on_submit=State.update_assistant_content,
            ),
            width="100%",
        ),
        style={
            **input_container_style,
            "background_color": "#F9F9F9",
            "border": "1px solid #E9E9E9",
            "box_shadow": "none",
            "width": "100%",
        },
    )


def editing_assistant_reasoning(index: int) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.form(
                rx.vstack(
                    rx.text_area(
                        value=State.reasoning,
                        placeholder="Edit the reasoning...",
                        on_change=State.set_reasoning,
                        style={**input_style, "background_color": "transparent"},
                    ),
                    rx.hstack(
                        rx.spacer(),
                        rx.button(
                            "Cancel", on_click=State.cancel_editing, style=button_style
                        ),
                        rx.button("Update", type="submit", style=button_style),
                        justify="end",
                        width="100%",
                    ),
                ),
                on_submit=State.update_assistant_reasoning,
            ),
            width="100%",
        ),
        style={
            **input_container_style,
            "border": "0px solid #E9E9E9",
            "box_shadow": "none",
            "width": "100%",
        },
    )


def copy_button(code: str) -> rx.Component:
    return rx.button(
        rx.icon("copy", size=20),
        on_click=rx.set_clipboard(code),
        position="absolute",
        top="0.5em",
        right="0",
        background_color="transparent",
        _hover={"background_color": "rgba(0,0,0,0.1)"},
    )


def code_block_with_copy(code: str, **props) -> rx.Component:
    return rx.box(
        rx.code_block(code, theme=rx.code_block.themes.dark, margin_y="1em", **props),
        copy_button(code),
        position="relative",
    )


reasoning_component_map = {"p": lambda text: rx.text.em(text)}
content_component_map = {"codeblock": code_block_with_copy}


def user_message(msg: Message, index: int) -> rx.Component:
    return rx.context_menu.root(
        rx.context_menu.trigger(
            rx.box(
                rx.box(
                    rx.text(
                        msg.content,
                        style={**question_style, "padding": "1em"},
                        white_space="pre-wrap",
                    ),
                    width="100%",
                ),
                width="80%",
                margin_left="20%",
            ),
        ),
        rx.context_menu.content(
            rx.context_menu.item(
                "Edit Message", on_click=lambda: State.start_editing_user_message(index)
            ),
            rx.context_menu.separator(),
            rx.context_menu.item(
                "Delete Message",
                color_scheme="red",
                on_click=lambda: State.delete_message(index),
            ),
            style=context_menu_style,
        ),
    )


def assistant_message(msg: Message, index: int) -> rx.Component:
    return rx.vstack(
        rx.cond(
            msg.reasoning != None,
            rx.context_menu.root(
                rx.context_menu.trigger(
                    rx.blockquote(
                        rx.box(
                            rx.markdown(
                                msg.reasoning, component_map=reasoning_component_map
                            ),
                            rx.box(
                                rx.cond(
                                    CopyState.copied_indices[f"{index}_reasoning"],
                                    rx.icon("check", stroke_width=1, size=15),
                                    rx.icon("copy", stroke_width=1, size=15),
                                ),
                                on_click=lambda: CopyState.copy_and_reset(
                                    msg.reasoning, f"{index}_reasoning"
                                ),
                                style=copy_button_style,
                                _hover={"opacity": 1},
                            ),
                            position="relative",
                        ),
                        width="100%",
                        size="1",
                    ),
                ),
                rx.context_menu.content(
                    rx.context_menu.item(
                        "Edit Reasoning",
                        on_click=lambda: State.start_editing_assistant_reasoning(index),
                    ),
                    rx.context_menu.separator(),
                    rx.context_menu.item(
                        "Delete Message",
                        color_scheme="red",
                        on_click=lambda: State.delete_message(index),
                    ),
                    style=context_menu_style,
                ),
            ),
            rx.box(),
        ),
        rx.cond(
            msg.content != None,
            rx.context_menu.root(
                rx.context_menu.trigger(
                    rx.box(
                        rx.box(
                            rx.markdown(
                                msg.content,
                                component_map=content_component_map,
                                style=answer_style,
                            ),
                            rx.box(
                                rx.cond(
                                    CopyState.copied_indices[f"{index}_content"],
                                    rx.icon("check", stroke_width=1, size=15),
                                    rx.icon("copy", stroke_width=1, size=15),
                                ),
                                on_click=lambda: CopyState.copy_and_reset(
                                    msg.content, f"{index}_content"
                                ),
                                style=copy_button_style,
                                _hover={"opacity": 1},
                            ),
                            position="relative",
                        ),
                        width="100%",
                    ),
                ),
                rx.context_menu.content(
                    rx.context_menu.item(
                        "Edit Content",
                        on_click=lambda: State.start_editing_assistant_content(index),
                    ),
                    rx.context_menu.separator(),
                    rx.context_menu.item(
                        "Delete Message",
                        color_scheme="red",
                        on_click=lambda: State.delete_message(index),
                    ),
                    style=context_menu_style,
                ),
            ),
            rx.box(),
        ),
        align="start",
        width="100%",
    )


def message(msg: Message, index: int) -> rx.Component:
    return rx.cond(
        State.editing_user_message_index == index,
        editing_user_input(index),
        rx.cond(
            State.editing_assistant_content_index == index,
            editing_assistant_content(index),
            rx.cond(
                State.editing_assistant_reasoning_index == index,
                editing_assistant_reasoning(index),
                rx.cond(
                    msg.role == "user",
                    user_message(msg, index),
                    assistant_message(msg, index),
                ),
            ),
        ),
    )


# -----------------------------------------------------------------------------
# Render Function with Type Annotation for Foreach
# -----------------------------------------------------------------------------
def render_message(msg: Message, index: int) -> rx.Component:
    """
    Render a message component with a proper type annotation.
    """
    return message(msg, index)


def chat() -> rx.Component:
    """Chat messages area using current_chat.messages from the ORM."""
    return rx.vstack(
        rx.foreach(
            State.chat_messages,
            render_message,
        ),
        align="start",
        width="100%",
        padding_bottom="5em",
    )


# -----------------------------------------------------------------------------
# Action Bar for User Input
# -----------------------------------------------------------------------------


class ActionBarState(rx.State):
    @rx.event
    def auto_resize_textarea(self):
        return rx.call_script(
            """
            function autoResizeTextArea(element) {
                if (!element) return;
                const computed = window.getComputedStyle(element);
                const hiddenDiv = document.createElement('div');
                hiddenDiv.style.cssText = `
                    width: ${computed.width};
                    padding: ${computed.padding};
                    border: ${computed.border};
                    font: ${computed.font};
                    letter-spacing: ${computed.letterSpacing};
                    position: absolute;
                    top: -9999px;
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                    white-space: pre-wrap;
                `;
                document.body.appendChild(hiddenDiv);
                hiddenDiv.textContent = element.value;
                const maxHeight = window.innerHeight * 0.6;
                const targetHeight = Math.min(hiddenDiv.offsetHeight, maxHeight);
                document.body.removeChild(hiddenDiv);
                const currentHeight = element.getBoundingClientRect().height;
                if (Math.abs(currentHeight - targetHeight) > 1) {
                    element.style.height = targetHeight + 'px';
                }
            }
            autoResizeTextArea(document.getElementById('input-textarea--action-bar'));
            """
        )


def action_bar() -> rx.Component:
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
                            value=State.question,
                            placeholder="何でも質問してください...",
                            on_change=[State.set_question],
                            style=input_style,
                            on_key_down=[
                                State.handle_action_bar_keydown,
                                ActionBarState.auto_resize_textarea,
                            ],
                        ),
                        rx.hstack(
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
                                    height="100%",
                                ),
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
                            style=controls_style,
                        ),
                    ),
                    on_submit=State.process_message,
                    style=form_style,
                ),
                width="100%",
            ),
            style=input_container_style,
            position="sticky",
            bottom="0",
        ),
    )


# -----------------------------------------------------------------------------
# Main Chat Component
# -----------------------------------------------------------------------------


def main_chat() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.heading(
                    rx.cond(
                        State.current_project,
                        State.current_project.name,
                        "Select a Project",
                    )
                    + " / "
                    + rx.cond(
                        State.current_chat,
                        State.current_chat.name,
                        "Select a Chat",
                    ),
                    size="3",
                ),
                width="100%",
                padding="1rem",
                border_bottom="1px solid rgb(229, 231, 235)",
            ),
            chat(),
            action_bar(),
        ),
        style=chat_style,
    )
