import os
import json
from dotenv import load_dotenv
from agents.environment_setup_agent import EnvironmentSetupAgent
from agents.schema_conversion_agent import SchemaConversionAgent
from agents.data_migration_agent import DataMigrationAgent
from agents.data_validation_agent import DataValidationAgent
from agents.anomaly_detection_agent import AnomalyDetectionAgent
from agents.performance_optimization_agent import PerformanceOptimizationAgent

def load_config():
    """Loads configuration from JSON files and environment variables."""
    load_dotenv() # Load.env file for API keys

    llm_config_path = os.path.join(os.path.dirname(__file__), "config", "oai_config.json")
    with open(llm_config_path, 'r') as f:
        llm_config = json.load(f)

    gcp_config_path = os.path.join(os.path.dirname(__file__), "config", "gcp_config.json")
    with open(gcp_config_path, 'r') as f:
        gcp_config = json.load(f)

    # Ensure sensitive info from env vars if not in JSON
    gcp_config['cloudsql_password'] = os.getenv('GCP_CLOUDSQL_PASSWORD', gcp_config.get('cloudsql_password'))
    gcp_config['project_id'] = os.getenv('GCP_PROJECT_ID', gcp_config.get('project_id'))

    # Source DB config (assuming it's external/legacy MySQL)
    source_db_config = {
        "host": os.getenv('SOURCE_MYSQL_HOST', 'your_legacy_mysql_host'),
        "user": os.getenv('SOURCE_MYSQL_USER', 'your_legacy_mysql_user'),
        "password": os.getenv('SOURCE_MYSQL_PASSWORD', 'your_legacy_mysql_password'),
        "database": os.getenv('SOURCE_MYSQL_DATABASE', 'employees'), # datacharmer/test_db default
        "port": int(os.getenv('SOURCE_MYSQL_PORT', 3306))
    }

    # Target DB config (will be provisioned by EnvironmentSetupAgent)
    # These values will be used by other agents to connect to the *newly provisioned* Cloud SQL instance
    target_db_config = {
        "host": "localhost", # Cloud SQL Proxy will tunnel to this, or direct private IP if VM is in same VPC
        "user": gcp_config['cloudsql_user'],
        "password": gcp_config['cloudsql_password'],
        "database": gcp_config['cloudsql_database_name'],
        "port": 3306 # Default MySQL port for Cloud SQL Proxy
    }

    return llm_config, gcp_config, source_db_config, target_db_config

def main():
    llm_config, gcp_config, source_db_config, target_db_config = load_config()

    print("--- Starting End-to-End MySQL to Cloud SQL Migration ---")

    # 1. Environment Setup
    env_setup_agent = EnvironmentSetupAgent(llm_config=llm_config, gcp_config=gcp_config)
    env_result = env_setup_agent.setup_environment()
    if env_result['status']!= 'completed':
        print("Environment setup failed. Aborting migration.")
        return

    # After environment setup, ensure Cloud SQL Proxy is running on the orchestrator VM
    # This step would typically be part of the VM's startup script or a manual step for initial setup.
    # For automation, the EnvironmentSetupAgent could trigger a script to install and run it.
    # For simplicity in this code, we assume it's handled externally or by a preceding script.
    # Example:./cloud_sql_proxy -instances=PROJECT_ID:REGION:INSTANCE_NAME=tcp:3306 &

    # Update target_db_config with actual Cloud SQL private IP if orchestrator VM is in same VPC
    # This would require fetching the IP from Terraform outputs or gcloud CLI.
    # For now, assuming localhost:3306 via Cloud SQL Proxy.
    # actual_cloudsql_ip = GcpCliTools.get_cloudsql_instance_ip(gcp_config['cloudsql_instance_name'])
    # target_db_config['host'] = actual_cloudsql_ip

    # 2. Schema Conversion
    schema_agent = SchemaConversionAgent(llm_config=llm_config, source_db_config=source_db_config, target_db_config=target_db_config)
    schema_result = schema_agent.convert_schema()
    if schema_result['status']!= 'completed':
        print("Schema conversion failed. Aborting migration.")
        return

    # 3. Data Migration
    data_migration_agent = DataMigrationAgent(llm_config=llm_config, source_db_config=source_db_config, target_db_config=target_db_config, cloud_storage_bucket=gcp_config['cloud_storage_bucket_name'])
    data_migration_result = data_migration_agent.migrate_data()
    if data_migration_result['status']!= 'completed':
        print("Data migration failed. Aborting migration.")
        return

    # 4. Data Validation
    data_validation_agent = DataValidationAgent(llm_config=llm_config, source_db_config=source_db_config, target_db_config=target_db_config)
    validation_result = data_validation_agent.validate_data()
    print(f"Data Validation Report: {validation_result['details']}")

    # 5. Anomaly Detection (Post-migration monitoring)
    anomaly_detection_agent = AnomalyDetectionAgent(llm_config=llm_config, gcp_config=gcp_config)
    anomaly_result = anomaly_detection_agent.detect_anomalies()
    print(f"Anomaly Detection Report: {anomaly_result['details']}")

    # 6. Performance Optimization (Post-migration tuning)
    perf_opt_agent = PerformanceOptimizationAgent(llm_config=llm_config, target_db_config=target_db_config, gcp_config=gcp_config)
    perf_opt_result = perf_opt_agent.optimize_performance()
    print(f"Performance Optimization Recommendations: {perf_opt_result['details']}")

    print("--- End-to-End Migration Process Completed ---")

if __name__ == "__main__":
    main()