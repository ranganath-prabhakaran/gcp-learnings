from autogen import AssistantAgent, UserProxyAgent, register_function
from tools.monitoring_tools import MonitoringTools
import json

class AnomalyDetectionAgent:
    def __init__(self, llm_config: dict, gcp_config: dict):
        self.gcp_config = gcp_config
        self.assistant = AssistantAgent(
            name="AnomalyDetectionAssistant",
            system_message="You are an expert in detecting anomalies in GCP Cloud SQL metrics. "
                            "Your task is to monitor CPU, memory, disk, and network egress for the Cloud SQL instance, "
                            "identify unusual patterns, and report them. "
                            "Return 'TERMINATE' when anomaly detection for the initial period is complete.",
            llm_config=llm_config,
        )
        self.user_proxy = UserProxyAgent(
            name="MonitoringExecutor",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
            code_execution_config={"executor": MonitoringTools()},
        )

        # Register tools
        register_function(
            MonitoringTools.get_cloudsql_metrics,
            caller=self.assistant,
            executor=self.user_proxy,
            name="get_cloudsql_metrics",
            description="Retrieves Cloud SQL instance metrics (e.g., 'cpu_utilization', 'memory_usage', 'disk_utilization', 'network_egress')."
        )
        register_function(
            MonitoringTools.analyze_metrics_for_anomaly,
            caller=self.assistant,
            executor=self.user_proxy,
            name="analyze_metrics_for_anomaly",
            description="Analyzes metric data for simple threshold-based anomalies. "
                        "For memory, recommends staying below 90% utilization."
        )

    def detect_anomalies(self) -> dict:
        """Initiates the anomaly detection process."""
        print("Starting Anomaly Detection...")
        
        instance_name = self.gcp_config['cloudsql_instance_name']
        project_id = self.gcp_config['project_id']
        os.environ = project_id # Set env var for tool

        initial_prompt = f"""
        1. Retrieve the last 6 hours of 'cpu_utilization' metrics for Cloud SQL instance '{instance_name}'.
        2. Analyze the CPU utilization data for any anomalies.
        3. Retrieve the last 6 hours of 'memory_usage' metrics for Cloud SQL instance '{instance_name}'.
        4. Analyze the memory usage data for any anomalies, noting that memory usage should ideally remain below 90%.
        5. Retrieve the last 6 hours of 'disk_utilization' metrics for Cloud SQL instance '{instance_name}'.
        6. Analyze the disk utilization data for any anomalies, noting that at least 20% free space should be maintained.
        7. Retrieve the last 6 hours of 'network_egress' metrics for Cloud SQL instance '{instance_name}'.
        8. Analyze the network egress data for any unusual spikes.
        9. Summarize all detected anomalies and provide recommendations.
        """
        
        chat_result = self.user_proxy.initiate_chat(
            self.assistant,
            message=initial_prompt
        )
        
        final_message = chat_result.chat_history[-1]['content']
        print(f"Anomaly Detection Complete. Final message: {final_message}")
        return {"status": "completed", "details": final_message}