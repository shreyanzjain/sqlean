from typing import Dict, Any, Tuple
from src.database_manager import DatabaseManager

class ExerciseValidator:
    """
    Validates a user's query based on the lesson's validation rules.
    """
    def __init__(self, db_manager: DatabaseManager):
        """
        Initializes the Validator.
        
        Args:
            db_manager: An instance of DatabaseManager.
        """
        self.db_manager = db_manager

    def validate(self, dataset_name: str, user_query: str, lesson_data: Dict[str, Any]) -> Tuple[bool, str, Any]:
        """
        Main validation router.
        
        Args:
            dataset_name: The dataset to use for validation.
            user_query: The user's SQL query.
            lesson_data: The dictionary for the current lesson.
            
        Returns:
            A tuple (success, message, query_results).
            query_results is for the CLI to display if the query was a non-erroring SELECT.
        """
        validation_type = lesson_data.get('validation_type')
        
        # First, check for basic syntax errors on the user's query
        conn = self.db_manager.get_clean_connection(dataset_name)
        if not conn:
            return (False, "Error: Could not load dataset for validation.", None)
        
        success, results, cols, error = self.db_manager.run_query(conn, user_query)
        conn.close()
        
        if not success:
            return (False, f"Your query has an error:\n{error}", None)
        
        user_query_results = (results, cols)

        # Route to the specific validation method
        if validation_type == 'results_match':
            success, msg = self._validate_results_match(dataset_name, user_query, lesson_data)
        elif validation_type == 'state_check':
            success, msg = self._validate_state_check(dataset_name, user_query, lesson_data)
        elif validation_type == 'keyword_check':
            success, msg = self._validate_keyword_check(dataset_name, user_query, lesson_data)
        else:
            return (False, "Error: Unknown validation type in lesson file.", None)
            
        return (success, msg, user_query_results)

    def _validate_results_match(self, dataset_name: str, user_query: str, lesson_data: Dict[str, Any]) -> Tuple[bool, str]:
        solution_query = lesson_data['solution_query']

        # 1. Get user results
        conn_user = self.db_manager.get_clean_connection(dataset_name)
        success_user, results_user, _, err_user = self.db_manager.run_query(conn_user, user_query)
        conn_user.close()
        if not success_user:
            return (False, f"Your query has an error: {err_user}")
            
        # 2. Get solution results
        conn_sol = self.db_manager.get_clean_connection(dataset_name)
        success_sol, results_sol, _, err_sol = self.db_manager.run_query(conn_sol, solution_query)
        conn_sol.close()
        if not success_sol:
            return (False, f"Lesson Error: The solution query failed: {err_sol}")
            
        # 3. Compare. Use set of tuples to ignore ordering.
        try:
            # Convert to list of lists for comparison in case of unhashable types
            user_results_list = [list(row) for row in results_user]
            solution_results_list = [list(row) for row in results_sol]

            # Convert to set of tuples for order-independent comparison
            user_results_set = set(tuple(row) for row in results_user)
            solution_results_set = set(tuple(row) for row in results_sol)
        except TypeError:
             # Fallback for unhashable types (e.g., if results contained lists)
             user_results_set = user_results_list
             solution_results_set = solution_results_list

        if user_results_set == solution_results_set:
            return (True, "Correct!")
        else:
            return (False, "Incorrect. Your query ran, but the results did not match the expected output.")

    def _validate_state_check(self, dataset_name: str, user_query: str, lesson_data: Dict[str, Any]) -> Tuple[bool, str]:
        validation_query = lesson_data['validation_query']
        expected_results = lesson_data['expected_results']
        
        # 1. Get one connection for this entire transaction
        conn = self.db_manager.get_clean_connection(dataset_name)
        
        # 2. Run user's query (e.g., UPDATE)
        success_user, _, _, err_user = self.db_manager.run_query(conn, user_query)
        if not success_user:
            conn.close()
            return (False, f"Your query has an error: {err_user}")
            
        # 3. On the *same connection*, run the validation query
        success_val, results_val, _, err_val = self.db_manager.run_query(conn, validation_query)
        conn.close()
        if not success_val:
            return (False, f"Lesson Error: The validation query failed: {err_val}")
            
        # 4. Compare validation results
        # --- FIX IS HERE ---
        # Convert results_val (list of tuples) to a list of lists for
        # a fair comparison with the YAML-loaded list of lists.
        results_as_lists = [list(row) for row in results_val]

        if results_as_lists == expected_results:
            return (True, "Correct! The database state was updated successfully.")
        else:
            # Add some debug info for ourselves
            print(f"DEBUG: Validation failed. DB_Results: {results_as_lists} | Expected: {expected_results}")
            return (False, "Incorrect. Your query ran, but the resulting database state was not correct.")

    def _validate_keyword_check(self, dataset_name: str, user_query: str, lesson_data: Dict[str, Any]) -> Tuple[bool, str]:
        required_keywords = lesson_data['required_keywords']
        user_query_lower = user_query.lower()
        
        # 1. Check for all required keywords
        for keyword in required_keywords:
            if keyword.lower() not in user_query_lower:
                return (False, f"Hint: You must use the `{keyword.upper()}` keyword for this exercise.")
                
        # 2. If keywords are present, also check if the results match
        # This ensures they used the keyword *and* got the right answer.
        return self._validate_results_match(dataset_name, user_query, lesson_data)