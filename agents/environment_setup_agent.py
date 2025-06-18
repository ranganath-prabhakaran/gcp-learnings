from autogen import AssistantAgent, UserProxyAgent, register_function
from tools.gcp_cli_tools import GcpCliTools
import json
import os

class EnvironmentSetupAgent:
    def __init__(self, llm_config: dict, gcp_config: dict):
        self.gcp_config = gcp_config
        self.assistant = AssistantAgent(
            name="EnvironmentSetupAssistant",
            system_message="You are an expert in GCP infrastructure provisioning using Terraform and gcloud CLI. "
                            "Your task is to set up Cloud SQL for MySQL, VPC network, and Cloud Storage. "
                            "You will generate Terraform commands and gcloud CLI commands. "
                            "Ensure all resources follow GCP best practices for security and cost optimization. "
                            "Return 'TERMINATE' when all infrastructure is successfully provisioned and configured.",
            llm_config=llm_config,
        )
        self.user_proxy = UserProxyAgent(
            name="GCPExecutor",
            human_input_mode="NEVER", # Automated execution
            max_consecutive_auto_reply=10,
            is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
            code_execution_config={"executor": GcpCliTools()}, # Use GcpCliTools for execution
        )

        # Register tools for the agents
        register_function(
            GcpCliTools.run_terraform_command,
            caller=self.assistant,
            executor=self.user_proxy,
            name="run_terraform_command",
            description="Executes a Terraform command in a specified directory (e.g., 'init', 'apply -auto-approve', 'output -json')."
        )
        register_function(
            GcpCliTools.run_gcloud_command,
            caller=self.assistant,
            executor=self.user_proxy,
            name="run_gcloud_command",
            description="Executes a gcloud CLI command and returns JSON output."
        )
        register_function(
            GcpCliTools.enable_service_api,
            caller=self.assistant,
            executor=self.user_proxy,
            name="enable_service_api",
            description="Enables a Google Cloud API service (e.g., 'servicenetworking.googleapis.com')."
        )
        register_function(
            GcpCliTools.create_vpc_peering_connection,
            caller=self.assistant,
            executor=self.user_proxy,
            name="create_vpc_peering_connection",
            description="Creates a VPC peering connection for private services access."
        )
        register_function(
            GcpCliTools.get_project_number,
            caller=self.assistant,
            executor=self.user_proxy,
            name="get_project_number",
            description="Retrieves the project number for a given project ID."
        )
        register_function(
            GcpCliTools.add_iam_policy_binding,
            caller=self.assistant,
            executor=self.user_proxy,
            name="add_iam_policy_binding",
            description="Adds an IAM policy binding to a project."
        )


    def setup_environment(self) -> dict:
        """Initiates the environment setup process."""
        print("Starting Environment Setup...")
        
        initial_prompt = f"""
        Provision the following GCP infrastructure using Terraform and gcloud CLI:
        1. Enable necessary APIs: `compute.googleapis.com`, `sqladmin.googleapis.com`, `servicenetworking.googleapis.com`, `storage.googleapis.com`.
        2. Initialize Terraform in the `terraform/` directory.
        3. Apply the Terraform configuration to create:
           - A VPC network named '{self.gcp_config['cloudsql_vpc_network']}'.
           - An allocated IP range for private services access named '{self.gcp_config['cloudsql_private_ip_range_name']}'.
           - A private service connection to `servicenetworking.googleapis.com`.
           - A Cloud SQL for MySQL instance named '{self.gcp_config['cloudsql_instance_name']}' in region '{self.gcp_config['region']}', 
             with machine type '{self.gcp_config['cloudsql_machine_type']}', disk size {self.gcp_config['cloudsql_disk_size_gb']}GB SSD, 
             HA enabled: {self.gcp_config['cloudsql_ha_enabled']}, and Private IP enabled using VPC network '{self.gcp_config['cloudsql_vpc_network']}'.
             Ensure `require_secure_transport` flag is ON and a strong password policy is set.
           - A database named '{self.gcp_config['cloudsql_database_name']}' and a user '{self.gcp_config['cloudsql_user']}' for this instance.
           - A Cloud Storage bucket named '{self.gcp_config['cloud_storage_bucket_name']}' with uniform bucket-level access enabled and a 7-day lifecycle rule for object deletion.
        4. Grant the `roles/servicenetworking.serviceAgent` role to the service networking service account for your project.
        
        Use the following variables for Terraform:
        project_id = "{self.gcp_config['project_id']}"
        region = "{self.gcp_config['region']}"
        cloudsql_instance_name = "{self.gcp_config['cloudsql_instance_name']}"
        cloudsql_database_name = "{self.gcp_config['cloudsql_database_name']}"
        cloudsql_user = "{self.gcp_config['cloudsql_user']}"
        cloudsql_password = "{self.gcp_config['cloudsql_password']}"
        cloudsql_machine_type = "{self.gcp_config['cloudsql_machine_type']}"
        cloudsql_disk_size_gb = {self.gcp_config['cloudsql_disk_size_gb']}
        cloudsql_ha_enabled = {self.gcp_config['cloudsql_ha_enabled']}
        cloudsql_private_ip_range_name = "{self.gcp_config['cloudsql_private_ip_range_name']}"
        cloudsql_vpc_network = "{self.gcp_config['cloudsql_vpc_network']}"
        cloud_storage_bucket_name = "{self.gcp_config['cloud_storage_bucket_name']}"

        Report the Cloud SQL instance connection name and private IP address upon successful provisioning.
        """
        
        chat_result = self.user_proxy.initiate_chat(
            self.assistant,
            message=initial_prompt,
            config_list=[self.gcp_config] # Pass config for agent to use
        )
        
        # Extract relevant information from the chat history
        final_message = chat_result.chat_history[-1]['content']
        print(f"Environment Setup Complete. Final message: {final_message}")
        return {"status": "completed", "details": final_message}
