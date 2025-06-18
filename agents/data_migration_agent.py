from autogen import AssistantAgent, UserProxyAgent, register_function
from tools.mysql_tools import MySQLTools
import os

class DataMigrationAgent:
    def __init__(self, llm_config: dict, source_db_config: dict, target_db_config: dict, cloud_storage_bucket: str):
        self.source_db_config = source_db_config
        self.target_db_config = target_db_config
        self.cloud_storage_bucket = cloud_storage_bucket
        self.assistant = AssistantAgent(
            name="DataMigrationAssistant",
            system_message="You are an expert in high-performance MySQL data migration using mydumper and myloader. "
                            "Your task is to export data from the source, upload to Cloud Storage, "
                            "and import into Cloud SQL. "
                            "Return 'TERMINATE' when data migration is successfully completed.",
            llm_config=llm_config,
        )
        self.user_proxy = UserProxyAgent(
            name="MigrationExecutor",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=15, # Increased for potentially longer migration
            is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
            code_execution_config={"executor": MySQLTools(
                host="localhost", # Tools will be run on the orchestrator VM
                user="dummy", # Dummy values for executor init, actual credentials passed to run_mydumper/myloader
                password="dummy"
            )},
        )

        # Register tools
        register_function(
            MySQLTools(
                host="localhost", # Dummy host, actual host passed as arg
                user="dummy",
                password="dummy"
            ).run_mydumper,
            caller=self.assistant,
            executor=self.user_proxy,
            name="run_mydumper",
            description="Executes mydumper to export data from a source MySQL database to a local directory."
        )
        register_function(
            MySQLTools(
                host="localhost", # Dummy host, actual host passed as arg
                user="dummy",
                password="dummy"
            ).run_myloader,
            caller=self.assistant,
            executor=self.user_proxy,
            name="run_myloader",
            description="Executes myloader to import data into a target MySQL database from a local directory."
        )
        # Add a tool for gsutil to move files to/from Cloud Storage
        register_function(
            self._gsutil_command,
            caller=self.assistant,
            executor=self.user_proxy,
            name="gsutil_command",
            description="Executes a gsutil command (e.g., 'cp -r local_dir gs://bucket_name', 'cp -r gs://bucket_name local_dir')."
        )

    def _gsutil_command(self, command: str) -> str:
        """Helper to run gsutil commands."""
        full_command = f"gsutil {command}"
        try:
            result = subprocess.run(full_command, shell=True, check=True, capture_output=True, text=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Error executing gsutil command: {e.stderr}")
            raise

    def migrate_data(self) -> dict:
        """Initiates the data migration process."""
        print("Starting Data Migration...")
        
        local_dump_dir = "/tmp/mysql_dump" # Temporary local directory on orchestrator VM
        cloud_storage_path = f"gs://{self.cloud_storage_bucket}/mysql_dumps"

        initial_prompt = f"""
        1. Create a local directory '{local_dump_dir}' on this machine.
        2. Execute `mydumper` to export data from the legacy MySQL database.
           Source details: host='{self.source_db_config['host']}', user='{self.source_db_config['user']}', password='{self.source_db_config['password']}', database='{self.source_db_config['database']}'.
           Output the dump files to the local directory '{local_dump_dir}'. Use a suitable number of threads (e.g., 4 or based on CPU cores).
        3. Once `mydumper` completes, upload the entire contents of '{local_dump_dir}' to the Cloud Storage bucket '{self.cloud_storage_bucket}' at path '{cloud_storage_path}'. Use `gsutil cp -r`.
        4. After successful upload, execute `myloader` to import the data from the Cloud Storage path '{cloud_storage_path}' into the Cloud SQL for MySQL instance.
           Target details: host='{self.target_db_config['host']}', user='{self.target_db_config['user']}', password='{self.target_db_config['password']}', database='{self.target_db_config['database']}'.
           First, download the dump files from '{cloud_storage_path}' to a temporary local directory (e.g., '/tmp/myloader_input') on this machine using `gsutil cp -r`.
           Then, run `myloader` from this temporary local directory. Use a suitable number of threads.
        5. Clean up the local temporary dump directories ('{local_dump_dir}' and '/tmp/myloader_input').
        """
        
        chat_result = self.user_proxy.initiate_chat(
            self.assistant,
            message=initial_prompt
        )
        
        final_message = chat_result.chat_history[-1]['content']
        print(f"Data Migration Complete. Final message: {final_message}")
        return {"status": "completed", "details": final_message}