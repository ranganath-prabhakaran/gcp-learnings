import subprocess
import json
import os

class GcpCliTools:
    """Tools for interacting with Google Cloud CLI."""

    @staticmethod
    def run_gcloud_command(command: str) -> dict:
        """Executes a gcloud CLI command and returns JSON output."""
        full_command = f"gcloud {command} --format=json"
        try:
            result = subprocess.run(full_command, shell=True, check=True, capture_output=True, text=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error executing gcloud command: {e.stderr}")
            raise

    @staticmethod
    def run_terraform_command(command: str, working_dir: str) -> str:
        """Executes a Terraform command."""
        full_command = f"terraform {command}"
        try:
            result = subprocess.run(full_command, shell=True, check=True, cwd=working_dir, capture_output=True, text=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Error executing terraform command: {e.stderr}")
            raise

    @staticmethod
    def get_cloudsql_instance_ip(instance_name: str) -> str:
        """Retrieves the private IP address of a Cloud SQL instance."""
        try:
            instance_details = GcpCliTools.run_gcloud_command(f"sql instances describe {instance_name}")
            for ip_address in instance_details.get('ipAddresses',):
                if ip_address.get('type') == 'PRIVATE':
                    return ip_address['ipAddress']
            raise ValueError(f"Private IP not found for Cloud SQL instance {instance_name}")
        except Exception as e:
            print(f"Could not get Cloud SQL instance IP: {e}")
            raise

    @staticmethod
    def enable_service_api(service_name: str, project_id: str):
        """Enables a Google Cloud API service."""
        try:
            print(f"Enabling {service_name} API for project {project_id}...")
            GcpCliTools.run_gcloud_command(f"services enable {service_name} --project={project_id}")
            print(f"{service_name} API enabled.")
            return {"status": "success", "message": f"{service_name} API enabled."}
        except Exception as e:
            print(f"Failed to enable {service_name} API: {e}")
            raise

    @staticmethod
    def create_vpc_peering_connection(network_name: str, project_id: str, range_name: str):
        """Creates a VPC peering connection for private services access."""
        try:
            print(f"Creating VPC peering connection for network {network_name} in project {project_id}...")
            GcpCliTools.run_gcloud_command(
                f"services vpc-peerings connect --service=servicenetworking.googleapis.com "
                f"--ranges={range_name} --network={network_name} --project={project_id}"
            )
            print("VPC peering connection initiated.")
            return {"status": "success", "message": "VPC peering connection initiated."}
        except Exception as e:
            print(f"Failed to create VPC peering connection: {e}")
            raise

    @staticmethod
    def get_project_number(project_id: str) -> str:
        """Retrieves the project number for a given project ID."""
        try:
            project_info = GcpCliTools.run_gcloud_command(f"projects describe {project_id}")
            return project_info['projectNumber']
        except Exception as e:
            print(f"Failed to get project number for {project_id}: {e}")
            raise

    @staticmethod
    def add_iam_policy_binding(project_id: str, member: str, role: str):
        """Adds an IAM policy binding to a project."""
        try:
            print(f"Adding IAM policy binding: member={member}, role={role} to project {project_id}...")
            GcpCliTools.run_gcloud_command(
                f"projects add-iam-policy-binding {project_id} --member='{member}' --role='{role}'"
            )
            print("IAM policy binding added.")
            return {"status": "success", "message": "IAM policy binding added."}
        except Exception as e:
            print(f"Failed to add IAM policy binding: {e}")
            raise