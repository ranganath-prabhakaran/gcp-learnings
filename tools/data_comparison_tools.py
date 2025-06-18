import pandas as pd
from tools.mysql_tools import MySQLTools

class DataComparisonTools:
    """Tools for comparing data between source and target databases."""

    @staticmethod
    def compare_row_counts(source_db_conn: MySQLTools, target_db_conn: MySQLTools, database_name: str) -> dict:
        """Compares row counts for all tables between source and target."""
        comparison_results = {}
        source_tables = source_db_conn.execute_query(f"SHOW TABLES FROM {database_name}", fetch_all=True)

        for table_dict in source_tables:
            table_name = list(table_dict.values())
            source_count = source_db_conn.execute_query(f"SELECT COUNT(*) FROM {database_name}.`{table_name}`")
            target_count = target_db_conn.execute_query(f"SELECT COUNT(*) FROM {database_name}.`{table_name}`")
            
            status = "MATCH" if source_count == target_count else "MISMATCH"
            comparison_results[table_name] = {
                "source_rows": source_count,
                "target_rows": target_count,
                "status": status
            }
        return comparison_results

    @staticmethod
    def compare_table_checksums(source_db_conn: MySQLTools, target_db_conn: MySQLTools, database_name: str, table_name: str) -> dict:
        """Compares checksums for a specific table."""
        try:
            source_checksum_result = source_db_conn.execute_query(f"CHECKSUM TABLE {database_name}.`{table_name}`")
            target_checksum_result = target_db_conn.execute_query(f"CHECKSUM TABLE {database_name}.`{table_name}`")

            source_checksum = source_checksum_result['Checksum'] if source_checksum_result else None
            target_checksum = target_checksum_result['Checksum'] if target_checksum_result else None

            status = "MATCH" if source_checksum == target_checksum else "MISMATCH"
            return {
                "table": table_name,
                "source_checksum": source_checksum,
                "target_checksum": target_checksum,
                "status": status
            }
        except Exception as e:
            return {"table": table_name, "status": "ERROR", "message": str(e)}

    @staticmethod
    def detect_data_anomalies(db_conn: MySQLTools, database_name: str, table_name: str, column_name: str, anomaly_threshold: float = 3.0) -> dict:
        """
        Detects simple anomalies in numerical data (e.g., using Z-score).
        This is a simplified example; real anomaly detection would use more sophisticated methods.
        """
        try:
            data = db_conn.execute_query(f"SELECT {column_name} FROM {database_name}.`{table_name}` WHERE {column_name} IS NOT NULL", fetch_all=True)
            if not data:
                return {"table": table_name, "column": column_name, "status": "NO_DATA", "anomalies":}

            df = pd.DataFrame(data)
            series = pd.to_numeric(df[column_name], errors='coerce').dropna()

            if series.empty:
                return {"table": table_name, "column": column_name, "status": "NO_NUMERIC_DATA", "anomalies":}

            mean = series.mean()
            std_dev = series.std()

            if std_dev == 0:
                return {"table": table_name, "column": column_name, "status": "NO_VARIATION", "anomalies":}

            anomalies =
            for index, value in series.items():
                z_score = (value - mean) / std_dev
                if abs(z_score) > anomaly_threshold:
                    anomalies.append({"value": value, "z_score": z_score, "row_index": index})
            
            return {"table": table_name, "column": column_name, "status": "SUCCESS", "anomalies_found": len(anomalies), "anomalies": anomalies}
        except Exception as e:
            return {"table": table_name, "column": column_name, "status": "ERROR", "message": str(e)}