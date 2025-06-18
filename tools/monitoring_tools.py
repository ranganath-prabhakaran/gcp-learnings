import subprocess
import json

class MonitoringTools:
    """Tools for monitoring GCP resources."""

    @staticmethod
    def get_cloudsql_metrics(instance_name: str, metric_type: str, duration_hours: int = 1) -> dict:
        """
        Retrieves Cloud SQL instance metrics (e.g., cpu/utilization, disk/utilization, memory/usage).
        Requires Cloud Monitoring API enabled and appropriate IAM permissions.
        """
        end_time = "now"
        start_time = f"now-{duration_hours}h"
        
        # Mapping common metric types to full Cloud Monitoring metric paths
        metrics_map = {
            "cpu_utilization": "cloudsql.googleapis.com/database/cpu/utilization",
            "memory_usage": "cloudsql.googleapis.com/database/memory/usage",
            "disk_utilization": "cloudsql.googleapis.com/database/disk/utilization",
            "network_egress": "cloudsql.googleapis.com/database/network/sent_bytes_count"
        }
        
        if metric_type not in metrics_map:
            raise ValueError(f"Unsupported metric type: {metric_type}. Choose from {list(metrics_map.keys())}")
        
        metric_path = metrics_map[metric_type]
        
        command = (
            f"gcloud monitoring time-series list "
            f"--project={os.environ.get('GCP_PROJECT_ID')} " # Assume project ID is in env var
            f"--metric={metric_path} "
            f"--resource-type=cloudsql_database "
            f"--filter='resource.label.database_id=\"{instance_name}\"' "
            f"--end-time={end_time} "
            f"--start-time={start_time} "
            f"--interval=60s " # Sample every 60 seconds
            f"--format=json"
        )
        
        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error executing gcloud monitoring command: {e.stderr}")
            raise
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from gcloud monitoring: {e}")
            print(f"Raw stdout: {result.stdout}")
            raise

    @staticmethod
    def analyze_metrics_for_anomaly(metrics_data: dict, threshold: float = 0.9) -> dict:
        """
        Analyzes metric data for simple threshold-based anomalies.
        For memory, recommends staying below 90%.[5, 6]
        """
        anomalies =
        if not metrics_data:
            return {"status": "no_data", "anomalies": anomalies}

        # Assuming metrics_data is a list of time series, each with points
        for series in metrics_data:
            metric_name = series.get('metric', {}).get('type', 'unknown_metric')
            for point in series.get('points',):
                value = point.get('value', {}).get('doubleValue') # Assuming double value
                if value is None:
                    continue
                
                # Convert utilization/usage to percentage if applicable (values are 0-1)
                if 'utilization' in metric_name or 'usage' in metric_name:
                    value_percent = value * 100
                    if value_percent > threshold * 100:
                        anomalies.append({
                            "metric": metric_name,
                            "time": point.get('interval', {}).get('endTime'),
                            "value": value_percent,
                            "threshold": threshold * 100,
                            "message": f"High usage detected: {value_percent:.2f}% exceeds {threshold * 100:.0f}%"
                        })
                elif 'sent_bytes_count' in metric_name:
                    # For network egress, a simple spike detection or comparison to historical average
                    # For this example, just flag if it's unusually high (needs context)
                    # A more advanced agent would compare against a rolling average or historical baseline
                    if value > 100000000: # Example: if > 100MB in an interval
                        anomalies.append({
                            "metric": metric_name,
                            "time": point.get('interval', {}).get('endTime'),
                            "value_bytes": value,
                            "message": f"High network egress detected: {value} bytes"
                        })

        return {"status": "success", "anomalies_found": len(anomalies), "anomalies": anomalies}