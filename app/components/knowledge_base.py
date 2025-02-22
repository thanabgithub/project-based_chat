import reflex as rx
from app.state import State
from app.styles import knowledge_base_style


def knowledge_base() -> rx.Component:
    """The knowledge base component."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.heading("Knowledge Base", size="4"),
                rx.upload(
                    # on_upload=State.upload_document,
                    id="knowledge_base_upload",
                ),
                rx.button(
                    "Upload",
                    on_click=rx.set_value("knowledge_base_upload", ""),
                ),
                justify="between",
                width="100%",
            ),
            rx.foreach(
                State.current_project.knowledge,
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
            width="100%",
            spacing="4",
            display=rx.cond(State.show_knowledge_base, "flex", "none"),
        ),
        style=knowledge_base_style,
    )
