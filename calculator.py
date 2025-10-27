"""Friendly calculator with a graphical interface for elementary students."""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass


@dataclass
class Problem:
    """Representation of a calculation problem."""

    first: int
    second: int
    operator: str

    def solve(self) -> str:
        """Return the solution as a user-friendly string."""

        operations = {
            "+": (self.first + self.second, "addition"),
            "-": (self.first - self.second, "subtraction"),
            "×": (self.first * self.second, "multiplication"),
            "÷": (self.first / self.second if self.second != 0 else None, "division"),
        }

        value, name = operations[self.operator]
        if value is None:
            raise ZeroDivisionError

        if float(value).is_integer():
            value_text = str(int(value))
        else:
            value_text = f"{value:.2f}"

        return f"The {name} of {self.first} and {self.second} is {value_text}."


class FriendlyCalculatorApp(tk.Tk):
    """Main application window for the friendly calculator."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Friendly Calculator")
        self.resizable(False, False)

        self.configure(background="#f6f8ff")

        self._build_widgets()

    def _build_widgets(self) -> None:
        """Create and arrange the widgets on the window."""

        header = tk.Label(
            self,
            text="Let's Explore Numbers!",
            font=("Arial Rounded MT Bold", 22),
            bg="#f6f8ff",
            fg="#1a237e",
            pady=10,
        )
        header.grid(row=0, column=0, columnspan=4)

        instructions = (
            "Type two whole numbers and press one of the colorful buttons\n"
            "to see the answer. Have fun practicing math!"
        )
        instruction_label = tk.Label(
            self,
            text=instructions,
            font=("Comic Sans MS", 12),
            bg="#f6f8ff",
            fg="#263238",
            justify="center",
            pady=5,
        )
        instruction_label.grid(row=1, column=0, columnspan=4)

        entry_frame = tk.Frame(self, bg="#f6f8ff")
        entry_frame.grid(row=2, column=0, columnspan=4, pady=(10, 5))

        self.first_number = tk.Entry(entry_frame, width=8, font=("Arial", 16), justify="center")
        self.second_number = tk.Entry(entry_frame, width=8, font=("Arial", 16), justify="center")

        tk.Label(
            entry_frame,
            text="First Number",
            font=("Arial", 12),
            bg="#f6f8ff",
            fg="#0d47a1",
        ).grid(row=0, column=0, padx=15, pady=(0, 5))
        tk.Label(
            entry_frame,
            text="Second Number",
            font=("Arial", 12),
            bg="#f6f8ff",
            fg="#0d47a1",
        ).grid(row=0, column=1, padx=15, pady=(0, 5))

        self.first_number.grid(row=1, column=0, padx=15)
        self.second_number.grid(row=1, column=1, padx=15)

        button_info = [
            ("+", "Add", "#ff8a80"),
            ("-", "Subtract", "#ffcc80"),
            ("×", "Multiply", "#80deea"),
            ("÷", "Divide", "#b39ddb"),
        ]

        for column, (symbol, label, color) in enumerate(button_info):
            button = tk.Button(
                self,
                text=f"{symbol}\n{label}",
                font=("Arial", 16, "bold"),
                width=6,
                bg=color,
                activebackground=color,
                relief=tk.RAISED,
                command=lambda s=symbol: self._calculate(s),
            )
            button.grid(row=3, column=column, padx=5, pady=10)

        self.message_label = tk.Label(
            self,
            text="",
            font=("Arial", 14),
            bg="#f6f8ff",
            fg="#1b5e20",
            pady=10,
            wraplength=340,
            justify="center",
        )
        self.message_label.grid(row=4, column=0, columnspan=4)

        self._set_message("Ready to make math magic? Enter numbers to begin!")

    def _set_message(self, message: str, *, error: bool = False) -> None:
        """Update the message label with a friendly message."""

        color = "#b71c1c" if error else "#1b5e20"
        self.message_label.configure(text=message, fg=color)

    def _calculate(self, operator: str) -> None:
        """Validate input, perform the operation, and show the result."""

        try:
            first = self._parse_integer(self.first_number.get(), "first")
            second = self._parse_integer(self.second_number.get(), "second")
            problem = Problem(first, second, operator)
            result = problem.solve()
        except ValueError as exc:
            self._set_message(str(exc), error=True)
        except ZeroDivisionError:
            self._set_message("Oops! We cannot divide by zero. Try another number.", error=True)
        else:
            self._set_message(result)

    @staticmethod
    def _parse_integer(text: str, label: str) -> int:
        """Convert user text input to an integer, raising a friendly error on failure."""

        stripped = text.strip()
        if not stripped:
            raise ValueError(f"Please type the {label} number.")

        if stripped.startswith("-"):
            digits = stripped[1:]
        else:
            digits = stripped

        if not digits.isdigit():
            raise ValueError("Numbers should be whole like 0, 5, or 12.")

        return int(stripped)


def main() -> None:
    """Launch the calculator application."""

    app = FriendlyCalculatorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
