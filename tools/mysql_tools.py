import mysql.connector
import subprocess
import os

class MySQLTools:
    """Tools for interacting with MySQL databases."""

    def __init__(self, host, user, password, database=None, port=3306):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        self.connection = None

    def _get_connection(self):
        if self.connection is None or not self.connection.is_connected():
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port,
                ssl_mode="VERIFY_IDENTITY" # Enforce SSL [4]
            )
        return self.connection

    def execute_query(self, query: str, fetch_all=False):
        """Executes a SQL query and returns results."""
        conn = self._get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query)
            if query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
                conn.commit()
                return {"status": "success", "rows_affected": cursor.rowcount}
            else:
                return cursor.fetchall() if fetch_all else cursor.fetchone()
        except mysql.connector.Error as err:
            print(f"Error executing query: {err}")
            raise
        finally:
            cursor.close()

    def get_schema_ddl(self, db_name: str) -> str:
        """Extracts DDL for all tables and routines in a database."""
        ddl_script =
        tables = self.execute_query(f"SHOW TABLES FROM {db_name}", fetch_all=True)
        for table in tables:
            table_name = list(table.values())
            create_table_sql = self.execute_query(f"SHOW CREATE TABLE {db_name}.`{table_name}`", fetch_all=False)
            ddl_script.append(create_table_sql + ";\n")

        # Add views, procedures, functions if needed
        # For simplicity, focusing on tables for now.
        return "\n".join(ddl_script)

    def run_mydumper(self, source_host: str, source_user: str, source_password: str, source_db: str, output_dir: str, threads: int = 4):
        """Runs mydumper to export data."""
        # Ensure mydumper is installed and accessible in the environment
        # For production, consider running mydumper in a Docker container for isolation
        print(f"Running mydumper for {source_db} to {output_dir} with {threads} threads...")
        command =
            "--compress",
            "--trx-consistency-only" # Less locking for InnoDB [1]
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            print("Mydumper stdout:\n", result.stdout)
            print("Mydumper stderr:\n", result.stderr)
            print("Mydumper completed successfully.")
            return {"status": "success", "output": result.stdout}
        except subprocess.CalledProcessError as e:
            print(f"Mydumper failed: {e.stderr}")
            raise

    def run_myloader(self, target_host: str, target_user: str, target_password: str, target_db: str, input_dir: str, threads: int = 4):
        """Runs myloader to import data."""
        print(f"Running myloader for {target_db} from {input_dir} with {threads} threads...")
        command = [
            "myloader",
            f"--host={target_host}",
            f"--user={target_user}",
            f"--password={target_password}",
            f"--database={target_db}",
            f"--directory={input_dir}",
            f"--threads={threads}",
            "--verbose=3", # Verbose output [1]
            "--enable-binlog" # Ensure binlog is enabled for replication if needed
        ]
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            print("Myloader stdout:\n", result.stdout)
            print("Myloader stderr:\n", result.stderr)
            print("Myloader completed successfully.")
            return {"status": "success", "output": result.stdout}
        except subprocess.CalledProcessError as e:
            print(f"Myloader failed: {e.stderr}")
            raise

    def close(self):
        """Closes the database connection."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self.connection = None