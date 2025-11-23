import json
import os
from typing import Dict, Any, Tuple


class UserProgressManager:
    """
    Reads and writes the user's progress to a local JSON file.
    """

    def __init__(self, progress_file_path: str):
        """
        Initializes the UserProgressManager.

        Args:
            progress_file_path: The file path (e.g., "user/progress.json").
        """
        self.progress_file = progress_file_path

        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.progress_file), exist_ok=True)

    def _get_default_progress(self) -> Dict[str, Any]:
        """Returns the default starting progress."""
        return {
            "last_module_id": "01_select",
            "last_lesson_id": 1,
            "completed_lessons": {}
        }

    def load_progress(self) -> Dict[str, Any]:
        """
        Loads user progress from the JSON file.
        If the file doesn't exist, returns default progress.
        """
        try:
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return self._get_default_progress()
        except json.JSONDecodeError:
            print("Warning: progress.json is corrupted. Starting from scratch.")
            return self._get_default_progress()

    def get_current_lesson(self) -> Tuple[str, int]:
        """
        Loads progress and returns the last (current) lesson.

        Returns:
            A tuple (module_id, lesson_id).
        """
        progress = self.load_progress()
        return (progress['last_module_id'], progress['last_lesson_id'])

    def save_progress(self, module_id: str, lesson_id: int, completed: bool):
        """
        Saves the new progress state to the JSON file.

        Args:
            module_id: The last module ID.
            lesson_id: The last lesson ID.
            completed: If True, marks the lesson as completed.
        """
        progress = self.load_progress()

        progress['last_module_id'] = module_id
        progress['last_lesson_id'] = lesson_id

        if completed:
            if module_id not in progress['completed_lessons']:
                progress['completed_lessons'][module_id] = []

            if lesson_id not in progress['completed_lessons'][module_id]:
                progress['completed_lessons'][module_id].append(lesson_id)

        try:
            with open(self.progress_file, 'w') as f:
                json.dump(progress, f, indent=2)
        except IOError as e:
            print(f"Error saving progress: {e}")
