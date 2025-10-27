# Kid-Friendly Calculator

This repository contains a colourful Tkinter calculator aimed at elementary
school learners.  The application greets children with encouraging copy and
provides big, easy-to-press buttons for the four basic operations.  Inputs are
validated to keep the experience friendly even when mistakes happen.

## Preview

Launching a graphical window is not always possible in automated environments,
so the repository ships with helpers that can generate a preview on demand.
This keeps the history free of binary assets while still making it easy to
inspect the interface.

To render a fresh PNG next to the source files, run:

```bash
python preview_generator.py
```

The command writes `ui_preview.png` in the project root without relying on
external libraries.

Need to share the screenshot inline in a chat or document without checking a
binary file into source control? Generate a data URI with:

```bash
python preview_data_uri.py --wrap 88
```

The command prints an embeddable string such as
`data:image/png;base64,iVBORw0…` that most rich text editors and markdown
renderers understand.

## Running the Calculator

```bash
python calculator.py
```

The window will open immediately.  Enter two numbers, pick an operation, and
the result card will show a cheerful explanation of the answer.

