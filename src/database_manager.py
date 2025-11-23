import sqlite3
import os
from typing import Optional, List, Any, Tuple

class DatabaseManager:
    """
    Manages the creation and population of sandboxed, in-memory SQLite databases
    based on specifications in the 'datasets/' directory.
    """
    def __init__(self, datasets_path: str):
        """
        Initializes the DatabaseManager with the path to the datasets.
        
        Args:
            datasets_path: The file path to the 'datasets' directory.
        """
        self.datasets_path = datasets_path

    def get_clean_connection(self, dataset_name: str) -> Optional[sqlite3.Connection]:
        """
        Creates a new, clean, in-memory SQLite database populated with data
        from the specified dataset.
        
        Args:
            dataset_name: The name of the dataset (e.g., "employees_db").
            
        Returns:
            A populated sqlite3.Connection object or None if dataset files are not found.
        """
        dataset_dir = os.path.join(self.datasets_path, dataset_name)
        schema_path = os.path.join(dataset_dir, "schema.sql")
        data_path = os.path.join(dataset_dir, "data.sql")

        if not (os.path.exists(schema_path) and os.path.exists(data_path)):
            print(f"Error: Dataset files not found for '{dataset_name}'")
            return None

        # Create a new in-memory database
        connection = sqlite3.connect(":memory:")
        
        try:
            # Read and execute schema.sql
            with open(schema_path, 'r') as f:
                connection.executescript(f.read())
                
            # Read and execute data.sql
            with open(data_path, 'r') as f:
                connection.executescript(f.read())
        
        except sqlite3.Error as e:
            print(f"Error populating database for '{dataset_name}': {e}")
            connection.close()
            return None
        
        return connection

    def run_query(self, connection: sqlite3.Connection, query: str) -> Tuple[bool, Optional[List[Any]], Optional[List[str]], Optional[str]]:
        """
        Executes a user's query against the provided connection.
        
        Args:
            connection: The sqlite3.Connection to use.
            query: The SQL query string to execute.
            
        Returns:
            A tuple: (success, results, columns, error_message)
            - success (bool): True if the query ran, False if an error occurred.
            - results (list | None): A list of result rows (for SELECT).
            - columns (list | None): A list of column names (for SELECT).
            - error_message (str | None): A formatted error string if success is False.
        """
        try:
            cursor = connection.cursor()
            cursor.execute(query)
            
            # For non-SELECT queries (INSERT, UPDATE, DELETE), cursor.description is None
            if cursor.description:
                # This was a SELECT query
                columns = [desc[0] for desc in cursor.description]
                results = cursor.fetchall()
                return (True, results, columns, None)
            else:
                # This was a DML query (UPDATE, INSERT, DELETE)
                connection.commit()
                return (True, None, None, None)
        
        except sqlite3.Error as e:
            return (False, None, None, str(e))

    def get_schema_info(self, connection: sqlite3.Connection) -> str:
        """
        Queries sqlite_master to retrieve all table CREATE statements.
        
        Args:
            connection: The sqlite3.Connection to inspect.
            
        Returns:
            A formatted string of all table schemas.
        """
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = cursor.fetchall()
            
            if not tables:
                return "No tables found in this database."
                
            schema_info = "--- DATABASE SCHEMA ---\n\n"
            schema_info += "\n\n".join([f"-- {name} --\n{sql};" for name, sql in tables])
            return schema_info
            
        except sqlite3.Error as e:
            return f"Error retrieving schema: {e}"