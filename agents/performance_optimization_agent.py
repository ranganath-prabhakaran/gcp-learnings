from autogen import AssistantAgent, UserProxyAgent, register_function
from tools.mysql_tools import MySQLTools
from tools.gcp_cli_tools import GcpCliTools # For instance scaling
from tools.monitoring_tools import MonitoringTools # For metrics
import json

class PerformanceOptimizationAgent:
    def __init__(self, llm_config: dict, target_db_config: dict, gcp_config: dict):
        self.target_db_config = target_db_config
        self.gcp_config = gcp_config
        self.assistant = AssistantAgent(
            name="PerformanceOptimizationAssistant",
            system_message="You are an expert in Cloud SQL for MySQL performance tuning and cost optimization. "
                            "Your task is to analyze database performance, identify bottlenecks, "
                            "suggest query optimizations, and recommend instance right-sizing. "
                            "Also, provide cost optimization strategies. "
                            "Return 'TERMINATE' when optimization recommendations are provided.",
            llm_config=llm_config,
        )
        self.user_proxy = UserProxyAgent(
            name="OptimizationExecutor",
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
                host=target_db_config['host'],
                user=target_db_config['user'],
                password=target_db_config['password'],
                database=target_db_config['database'],
                port=target_db_config['port']
            ).execute_query,
            caller=self.assistant,
            executor=self.user_proxy,
            name="execute_sql_on_target",
            description="Executes a SQL query on the target Cloud SQL instance (e.g., 'EXPLAIN SELECT...')."
        )
        register_function(
            GcpCliTools.run_gcloud_command,
            caller=self.assistant,
            executor=self.user_proxy,
            name="run_gcloud_command",
            description="Executes a gcloud CLI command, useful for getting instance details or updating configurations."
        )
        register_function(
            MonitoringTools.get_cloudsql_metrics,
            caller=self.assistant,
            executor=self.user_proxy,
            name="get_cloudsql_metrics",
            description="Retrieves Cloud SQL instance metrics (e.g., 'cpu_utilization', 'memory_usage')."
        )

    def optimize_performance(self) -> dict:
        """Initiates the performance optimization process."""
        print("Starting Performance Optimization...")
        
        instance_name = self.gcp_config['cloudsql_instance_name']
        
        initial_prompt = f"""
        1. Retrieve recent CPU and memory utilization metrics for Cloud SQL instance '{instance_name}' using `get_cloudsql_metrics`.
        2. Analyze the metrics to determine if the instance is right-sized. If CPU consistently maxed out or memory usage is above 90%, suggest scaling up. If consistently low, suggest scaling down.
        3. Identify any long-running or inefficient queries in the Cloud SQL instance '{instance_name}'. (Assume access to query insights or logs for this step, or simulate with a problematic query example).
           For example, consider an unindexed query: `SELECT * FROM employees WHERE first_name LIKE 'A%';`
           Use `execute_sql_on_target` with `EXPLAIN` for such queries.
        4. Based on query analysis, suggest specific SQL query optimizations (e.g., adding indexes, rewriting joins, avoiding SELECT *).
        5. Provide a summary of performance recommendations and cost optimization tips, including leveraging Committed Use Discounts for compute, and strategies for managing storage and network egress costs as CUDs do not apply to them.
        """
        
        chat_result = self.user_proxy.initiate_chat(
            self.assistant,
            message=initial_prompt
        )
        
        final_message = chat_result.chat_history[-1]['content']
        print(f"Performance Optimization Complete. Final message: {final_message}")
        return {"status": "completed", "details": final_message}