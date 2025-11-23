import os
import sys
from typing import Dict, Any, Optional, List

from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

from src.database_manager import DatabaseManager
from src.lesson_manager import LessonManager
from src.user_progress_manager import UserProgressManager
from src.exercise_validator import ExerciseValidator


class CLIEngine:
    """
    The main application loop that ties all components together.
    Handles all user I/O (input and output).
    """

    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.lesson_manager = LessonManager(os.path.join(base_dir, "content"))
        self.progress_manager = UserProgressManager(
            os.path.join(base_dir, "user/progress.json"))
        self.db_manager = DatabaseManager(os.path.join(base_dir, "datasets"))
        self.validator = ExerciseValidator(self.db_manager)

        self.console = Console()

        # Set up prompt-toolkit history
        history_path = os.path.join(base_dir, "user/.sql_history")
        os.makedirs(os.path.dirname(history_path), exist_ok=True)
        self.prompt_history = FileHistory(history_path)

    def _display_lesson(self, lesson_data: Dict[str, Any]):
        """Prints the lesson content using Rich."""
        self.console.rule(f"[bold cyan]{lesson_data['title']}[/bold cyan]")

        # Lesson Text
        self.console.print(Panel(
            Text(lesson_data['text'], style="white"),
            title="Concept",
            border_style="green",
            expand=True
        ))

        # Exercise
        self.console.print(Panel(
            Text(lesson_data['exercise'], style="bold yellow"),
            title="Exercise",
            border_style="yellow",
            expand=True
        ))

        # Schema Snippet
        if lesson_data.get('schema_snippet'):
            self.console.print(
                f"[dim]Schema hint: {lesson_data['schema_snippet']}[/dim]")

        self.console.print(
            "\nType your SQL query below. Type `!help` for commands.")

    def _print_results(self, results: List[Any], columns: List[str]):
        """Prints SQL results in a formatted table."""
        if not results:
            self.console.print("[italic]Query returned no rows.[/italic]")
            return

        table = Table(title="Query Results", show_header=True,
                      header_style="bold magenta")

        for col in columns:
            table.add_column(col)

        for row in results:
            table.add_row(*[str(item) for item in row])

        self.console.print(table)

    def _handle_meta_command(self, user_input: str, lesson_data: Dict[str, Any], dataset_name: str) -> bool:
        """
        Checks for and handles meta-commands (e.g., !hint).
        Returns True if a command was handled, False otherwise.
        """
        if user_input == "!help":
            self.console.print(
                "[bold]Meta-commands:[/bold]\n"
                "  !hint    - Show a hint for the current exercise.\n"
                "  !schema  - Show the schema for the current database.\n"
                "  !solve   - Show the solution query (does not pass the lesson).\n"
                "  !quit    - Exit the application."
            )
            return True

        elif user_input == "!hint":
            self.console.print(
                Panel(f"[italic green]{lesson_data['hint']}[/italic green]", title="Hint"))
            return True

        elif user_input == "!schema":
            conn = self.db_manager.get_clean_connection(dataset_name)
            if conn:
                schema_info = self.db_manager.get_schema_info(conn)
                conn.close()
                self.console.print(
                    Panel(schema_info, title="Database Schema", border_style="blue"))
            else:
                self.console.print("[red]Error: Could not load schema.[/red]")
            return True

        elif user_input == "!solve":
            self.console.print(
                Panel(f"[yellow]{lesson_data['solution_query']}[/yellow]", title="Solution"))
            return True

        elif user_input == "!quit":
            return False  # Signal to the prompt loop to exit

        return False

    def prompt_loop(self, lesson_data: Dict[str, Any], dataset_name: str) -> str:
        """
        The inner loop for a single exercise.

        Returns:
            - "success" if the lesson was passed
            - "quit" if the user wants to exit
        """
        multiline_buffer = []

        while True:
            try:
                # Use a different prompt for multiline input
                prompt_text = "SQL> " if not multiline_buffer else "...> "

                user_input = prompt(
                    prompt_text,
                    history=self.prompt_history,
                    auto_suggest=AutoSuggestFromHistory()
                ).strip()

                if not user_input:
                    continue

                if user_input.startswith("!"):
                    if self._handle_meta_command(user_input, lesson_data, dataset_name):
                        continue
                    elif user_input == "!quit":
                        return "quit"

                # Handle multiline input
                multiline_buffer.append(user_input)

                # If the query doesn't end with ';', assume it's multiline
                if not user_input.endswith(';'):
                    continue

                # If we're here, the query ends with ';'. Join the buffer.
                full_query = " ".join(multiline_buffer)
                multiline_buffer = []  # Clear the buffer

                # Validate the full query
                success, message, query_results = self.validator.validate(
                    dataset_name, full_query, lesson_data)

                if success:
                    self.console.print(
                        Panel(f"[bold green]✅ {message}[/bold green]"))
                    return "success"
                else:
                    self.console.print(
                        Panel(f"[bold red]❌ {message}[/bold red]"))
                    # If it was a non-erroring SELECT, show the user's (wrong) results
                    if query_results and query_results[0] is not None:
                        self.console.print(
                            "[italic]This is what your query returned:[/italic]")
                        self._print_results(query_results[0], query_results[1])

            except KeyboardInterrupt:
                if multiline_buffer:
                    multiline_buffer = []
                    self.console.print(
                        "\n[red]Multiline input cancelled.[/red]")
                else:
                    return "quit"
            except EOFError:
                return "quit"

    def run(self):
        """The main outer loop for the entire course."""
        self.console.clear()
        self.console.print(
            Panel("[bold green]Welcome to SQLean! 🚀[/bold green]", title="SQLean"))

        if not self.lesson_manager.load_course():
            self.console.print(
                "[red]Error: Could not load course. Exiting.[/red]")
            sys.exit(1)

        try:
            module_id, lesson_id = self.progress_manager.get_current_lesson()

            while module_id and lesson_id:
                lesson_data = self.lesson_manager.get_lesson(
                    module_id, lesson_id)
                module_info = self.lesson_manager.get_module_info(module_id)

                if not lesson_data or not module_info:
                    self.console.print(
                        f"[red]Error: Could not load lesson {module_id}:{lesson_id}. Exiting.[/red]")
                    break

                dataset_name = module_info['dataset']

                self._display_lesson(lesson_data)

                result = self.prompt_loop(lesson_data, dataset_name)

                if result == "success":
                    self.console.print(
                        "[green]Moving to the next lesson...[/green]\n")

                    # Mark this lesson as completed *before* finding the next one
                    self.progress_manager.save_progress(
                        module_id, lesson_id, completed=True)

                    # Get next lesson
                    next_module_id, next_lesson_id = self.lesson_manager.get_next_lesson_id(
                        module_id, lesson_id)

                    if next_module_id and next_lesson_id:
                        # Save progress at the *start* of the new lesson
                        self.progress_manager.save_progress(
                            next_module_id, next_lesson_id, completed=False)
                        module_id, lesson_id = next_module_id, next_lesson_id
                    else:
                        # End of course
                        break

                elif result == "quit":
                    break

            if not module_id or not lesson_id:
                self.console.print(Panel(
                    "[bold magenta]🎉 Congratulations! You have completed the entire course! 🎉[/bold magenta]"))

        except Exception as e:
            self.console.print(
                f"\n[bold red]An unexpected error occurred:[/bold] {e}")
            self.console.print("Exiting.")
        finally:
            self.console.print("\n[green]Goodbye![/green]")
