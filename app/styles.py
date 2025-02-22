"""Styles for the app."""

# Common styles
base_style = {
    "width": "100%",
    "height": "100vh",
}

# Sidebar styles
sidebar_style = {
    "width": "256px",
    "height": "100%",
    "padding": "1rem",
}

project_sidebar_style = {
    **sidebar_style,
    "background_color": "rgb(17, 24, 39)",  # bg-gray-900
    "color": "white",
}

chat_sidebar_style = {
    **sidebar_style,
    "background_color": "rgb(249, 250, 251)",  # bg-gray-50
}

# Button styles
button_style = {
    "width": "100%",
    "padding": "0.5rem 1rem",
    "border_radius": "0.375rem",
    "text_align": "left",
    "_hover": {"background_color": "rgb(55, 65, 81)"},  # bg-gray-700
}

selected_button_style = {
    **button_style,
    "background_color": "rgb(55, 65, 81)",  # bg-gray-700
}

# Modal styles
modal_style = {
    "padding": "2rem",
    "border_radius": "0.5rem",
    "background_color": "white",
    "max_width": "500px",
    "width": "100%",
}

# Knowledge base styles
knowledge_base_style = {
    "width": "300px",
    "height": "100%",
    "padding": "1rem",
    "background_color": "white",
    "border_left": "1px solid rgb(229, 231, 235)",  # border-gray-200
}
