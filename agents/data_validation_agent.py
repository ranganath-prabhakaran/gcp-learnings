from autogen import AssistantAgent, UserProxyAgent, register_function
from tools.mysql_tools import MySQLTools
from tools.data_comparison_tools import DataComparisonTools
import json

class DataValidationAgent:
    def __init__(self, llm_config: dict, source_db_config: dict, target_db_config: dict):
        self.source_db_config = source_db_config
        self.target_db_config = target_db_config
        self.assistant = AssistantAgent(
            name="DataValidationAssistant",
            system_message="You are an expert in database data validation. "
                            "Your task is to compare the migrated data in Cloud SQL against the source database "
                            "using row counts and checksums. "
                            "Generate a detailed validation report. "
                            "Return 'TERMINATE' when validation is complete and results are reported.",
            llm_config=llm_config,
        )
        self.user_proxy = UserProxyAgent(
            name="ValidationExecutor",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
            code_execution_config={"executor": MySQLTools(
                host=target_db_config['host'],
                user=target_db_config['user'],
                password=target_db_config['password'],
                database=target_db_config['database'],
                port=target_db_config['port']
            )}, # Executor for target DB operations
        )

        # Register tools
        self.source_mysql_tools = MySQLTools(
            host=source_db_config['host'],
            user=source_db_config['user'],
            password=source_db_config['password'],
            database=source_db_config['database'],
            port=source_db_config['port']
        )
        self.target_mysql_tools = MySQLTools(
            host=target_db_config['host'],
            user=target_db_config['user'],
            password=target_db_config['password'],
            database=target_db_config['database'],
            port=target_db_config['port']
        )

        register_function(
            DataComparisonTools.compare_row_counts,
            caller=self.assistant,
            executor=self.user_proxy,
            name="compare_row_counts",
            description="Compares row counts for all tables between source and target databases. "
                        "Requires source_db_conn and target_db_conn objects, and database_name."
        )
        register_function(
            DataComparisonTools.compare_table_checksums,
            caller=self.assistant,
            executor=self.user_proxy,
            name="compare_table_checksums",
            description="Compares checksums for a specific table between source and target databases. "
                        "Requires source_db_conn, target_db_conn objects, database_name, and table_name."
        )
        # To make the tools callable, we need to pass the connection objects or have the agent create them
        # For simplicity in AutoGen context, the agent will be instructed to pass connection parameters
        # and the tool will instantiate its own connections or use a shared context if available.
        # For this example, the tools are designed to take connection objects directly.
        # The agent will be prompted to call these with the instantiated MySQLTools objects.

    def validate_data(self) -> dict:
        """Initiates the data validation process."""
        print("Starting Data Validation...")
        
        # Pass the connection objects to the agent's context or instruct it to create them
        # This is a conceptual representation of how agents would use these tools.
        # In a real AutoGen setup, tools are registered and the LLM decides how to call them.
        # The prompt guides the LLM to use the tools with the correct parameters.
        
        initial_prompt = f"""
        1. Compare row counts for all tables in database '{self.source_db_config['database']}' between the source MySQL at '{self.source_db_config['host']}' and the target Cloud SQL at '{self.target_db_config['host']}'.
           Use the `compare_row_counts` tool, passing the source and target database connection objects.
        2. For a few critical tables (e.g., 'employees', 'salaries' from datacharmer/test_db), compare their checksums between source and target.
           Use the `compare_table_checksums` tool.
        3. Summarize the validation results, highlighting any discrepancies in row counts or checksums.
        """
        
        chat_result = self.user_proxy.initiate_chat(
            self.assistant,
            message=initial_prompt,
            # Pass connection objects as part of the context if the tools are designed to receive them
            # For this example, the tools are instantiated with configs, and the agent is expected to know how to use them.
            # A more robust solution might use a shared state or a tool that creates connections on demand.
            source_db_conn=self.source_mysql_tools,
            target_db_conn=self.target_mysql_tools
        )
        
        final_message = chat_result.chat_history[-1]['content']
        print(f"Data Validation Complete. Final message: {final_message}")
        return {"status": "completed", "details": final_message}