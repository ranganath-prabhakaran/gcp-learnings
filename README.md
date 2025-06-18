Overview: Automated legacy MySQL to GCP Cloud SQL migration using AutoGen AI agents.

Features:

Automated GCP resource provisioning (Cloud SQL, VPC, Cloud Storage).

Schema conversion and application.

Multi-threaded data migration using mydumper/myloader.

Post-migration data validation.

Anomaly detection for performance and cost.

Performance optimization recommendations.

Prerequisites:

GCP Project with billing enabled.

gcloud CLI installed and authenticated.

Terraform installed.

Python 3.9+ and pip.

Docker (for mydumper/myloader containerization, optional but recommended).

LLM API Key (e.g., OpenAI API Key) configured.

Setup:

Clone the repository.

Install Python dependencies (pip install -r requirements.txt).

Configure GCP credentials and LLM API keys (see config/oai_config.json and config/gcp_config.json.example).

Initialize Terraform (terraform init in terraform/).

Usage:

Execute python main.py to start the agentic migration process.

Follow prompts for input (if human_input_mode is enabled for UserProxyAgent).

Sample Database: Uses datacharmer/test_db for demonstration. Download employees.sql into the data/ directory.

Cost Optimization: Leverages mydumper/myloader and adheres to GCP best practices for cost efficiency.

Security: Emphasizes Private IP, VPC Peering, SSL, and IAM least privilege.