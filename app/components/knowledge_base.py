import reflex as rx
from app.state import State
from app.styles import knowledge_base_style


def knowledge_base() -> rx.Component:
    """The knowledge base component."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.heading("Knowledge Base", size="md"),
                rx.upload(
                    rx.button("Upload"),
                    multiple=True,
                    accept={
                        "application/pdf": [".pdf"],
                        "text/plain": [".txt"],
                        "text/markdown": [".md"],
                    },
                    on_upload=State.upload_document,
                ),
                justify="space-between",
                width="100%",
            ),
            rx.foreach(
                State.current_project.knowledge if State.current_project else [],
                lambda doc: rx.hstack(
                    rx.icon("document"),
                    rx.text(doc.name),
                    rx.spacer(),
                    rx.button(
                        rx.icon("delete"),
                        on_click=lambda: None,  # TODO: Implement delete
                        variant="ghost",
                    ),
                    width="100%",
                ),
            ),
            width="100%",
            spacing="1rem",
            display=rx.cond(State.show_knowledge_base, "flex", "none"),
        ),
        style=knowledge_base_style,
    )
