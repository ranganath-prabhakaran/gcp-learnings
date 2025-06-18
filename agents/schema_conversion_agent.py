from autogen import AssistantAgent, UserProxyAgent, register_function
from tools.mysql_tools import MySQLTools
import os

class SchemaConversionAgent:
    def __init__(self, llm_config: dict, source_db_config: dict, target_db_config: dict):
        self.source_db_config = source_db_config
        self.target_db_config = target_db_config
        self.assistant = AssistantAgent(
            name="SchemaConversionAssistant",
            system_message="You are an expert in MySQL schema analysis and conversion for Cloud SQL. "
                            "Your task is to extract the schema from the legacy MySQL, identify incompatibilities, "
                            "generate compatible DDL, and apply it to Cloud SQL. "
                            "Return 'TERMINATE' when the schema is successfully converted and applied.",
            llm_config=llm_config,
        )
        self.user_proxy = UserProxyAgent(
            name="SchemaExecutor",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
            code_execution_config={"executor": MySQLTools(
                host=target_db_config['host'],
                user=target_db_config['user'],
                password=target_db_config['password'],
                database=target_db_config['database'],
                port=target_db_config['port']
            )},
        )

        # Register tools
        register_function(
            MySQLTools(
                host=source_db_config['host'],
                user=source_db_config['user'],
                password=source_db_config['password'],
                database=source_db_config['database'],
                port=source_db_config['port']
            ).get_schema_ddl,
            caller=self.assistant,
            executor=self.user_proxy,
            name="get_source_schema_ddl",
            description="Extracts DDL for all tables from the source database."
        )
        register_function(
            MySQLTools(
                host=target_db_config['host'],
                user=target_db_config['user'],
                password=target_db_config['password'],
                database=target_db_config['database'],
                port=target_db_config['port']
            ).execute_query,
            caller=self.assistant,
            executor=self.user_proxy,
            name="execute_sql_on_target",
            description="Executes a SQL query or DDL script on the target Cloud SQL instance."
        )

    def convert_schema(self) -> dict:
        """Initiates the schema conversion process."""
        print("Starting Schema Conversion...")
        
        initial_prompt = f"""
        1. Connect to the legacy MySQL database at host '{self.source_db_config['host']}' with user '{self.source_db_config['user']}' and extract the DDL for all tables in database '{self.source_db_config['database']}'.
        2. Analyze the extracted DDL for any potential incompatibilities with Cloud SQL for MySQL 8.0 (e.g., specific storage engines like MyISAM, unsupported functions, character sets).
        3. Generate a compatible DDL script. Ensure character sets are `utf8mb4` and collation is `utf8mb4_unicode_ci` where appropriate.
        4. Connect to the Cloud SQL for MySQL instance at host '{self.target_db_config['host']}' with user '{self.target_db_config['user']}' and apply the generated DDL script to create the schema in database '{self.target_db_config['database']}'.
        5. Confirm schema creation by listing tables in the target database.
        """
        
        chat_result = self.user_proxy.initiate_chat(
            self.assistant,
            message=initial_prompt
        )
        
        final_message = chat_result.chat_history[-1]['content']
        print(f"Schema Conversion Complete. Final message: {final_message}")
        return {"status": "completed", "details": final_message}