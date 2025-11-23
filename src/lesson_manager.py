import yaml
import os
from typing import Optional, Dict, Any, List, Tuple


class LessonManager:
    """
    Loads and serves learning content from the 'content/' directory.
    Reads the manifest and individual module YAML files.
    """

    def __init__(self, content_path: str):
        """
        Initializes the LessonManager.

        Args:
            content_path: The file path to the 'content' directory.
        """
        self.content_path = content_path
        self.course_manifest: Dict[str, Any] = {}
        self.loaded_modules: Dict[str, Dict[str, Any]] = {}

    def load_course(self, manifest_file: str = "manifest.yml") -> bool:
        """
        Loads the main course manifest file.

        Args:
            manifest_file: The name of the manifest file.

        Returns:
            True if loading was successful, False otherwise.
        """
        manifest_path = os.path.join(self.content_path, manifest_file)
        try:
            with open(manifest_path, 'r') as f:
                self.course_manifest = yaml.safe_load(f)
            return True
        except FileNotFoundError:
            print(f"Error: Manifest file not found at {manifest_path}")
            return False
        except yaml.YAMLError as e:
            print(f"Error parsing manifest file: {e}")
            return False

    def get_module_info(self, module_id: str) -> Optional[Dict[str, Any]]:
        """
        Gets the metadata for a module (e.g., title, dataset) from the manifest.

        Args:
            module_id: The ID of the module (e.g., "01_select").

        Returns:
            A dictionary of the module's info or None if not found.
        """
        if not self.course_manifest:
            self.load_course()

        for module in self.course_manifest.get('modules', []):
            if module.get('id') == module_id:
                return module
        return None

    def _load_module_file(self, module_file: str) -> Optional[Dict[str, Any]]:
        """
        Private helper to load a module's YAML file and cache it.
        """
        if module_file in self.loaded_modules:
            return self.loaded_modules[module_file]

        module_path = os.path.join(self.content_path, module_file)
        try:
            with open(module_path, 'r') as f:
                module_data = yaml.safe_load(f)
                self.loaded_modules[module_file] = module_data
                return module_data
        except FileNotFoundError:
            print(f"Error: Lesson file not found at {module_path}")
            return None
        except yaml.YAMLError as e:
            print(f"Error parsing lesson file {module_file}: {e}")
            return None

    def get_lesson(self, module_id: str, lesson_id: int) -> Optional[Dict[str, Any]]:
        """

        Gets the complete data for a single lesson.

        Args:
            module_id: The ID of the module.
            lesson_id: The ID of the lesson.

        Returns:
            A dictionary of the lesson's data or None if not found.
        """
        module_info = self.get_module_info(module_id)
        if not module_info:
            return None

        module_file = module_info.get('file')
        if not module_file:
            print(
                f"Error: No 'file' key found for module '{module_id}' in manifest.")
            return None

        module_data = self._load_module_file(module_file)
        if not module_data:
            return None

        for lesson in module_data.get('lessons', []):
            if lesson.get('id') == lesson_id:
                return lesson

        print(f"Error: Lesson ID {lesson_id} not found in module {module_id}.")
        return None

    def get_next_lesson_id(self, module_id: str, current_lesson_id: int) -> Tuple[Optional[str], Optional[int]]:
        """
        Finds the next lesson, handling module transitions.

        Args:
            module_id: The current module ID.
            current_lesson_id: The current lesson ID.

        Returns:
            A tuple (next_module_id, next_lesson_id).
            If at the end of the course, returns (None, None).
        """
        module_info = self.get_module_info(module_id)
        module_data = self._load_module_file(module_info['file'])

        lessons = module_data.get('lessons', [])

        # Try to find the next lesson in the current module
        for lesson in lessons:
            if lesson.get('id') > current_lesson_id:
                # Found next lesson in this module
                return (module_id, lesson.get('id'))

        # If not found, try to find the next module
        modules_list = self.course_manifest.get('modules', [])
        try:
            current_module_index = next(i for i, mod in enumerate(
                modules_list) if mod['id'] == module_id)

            if current_module_index + 1 < len(modules_list):
                # Move to the next module
                next_module_id = modules_list[current_module_index + 1]['id']
                next_module_info = self.get_module_info(next_module_id)
                next_module_data = self._load_module_file(
                    next_module_info['file'])

                # Get the first lesson of the next module
                next_lesson_id = next_module_data.get('lessons', [])[
                    0].get('id')
                return (next_module_id, next_lesson_id)
            else:
                # End of the course
                return (None, None)

        except (StopIteration, IndexError):
            # This should not happen if data is valid
            return (None, None)
