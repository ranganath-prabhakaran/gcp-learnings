# outputs.tf
output "cloudsql_instance_connection_name" {
  description = "The connection name of the Cloud SQL instance."
  value       = google_sql_database_instance.mysql_instance.connection_name
}

output "cloudsql_private_ip_address" {
  description = "The private IP address of the Cloud SQL instance."
  value       = google_sql_database_instance.mysql_instance.private_ip_address
}

output "storage_bucket_url" {
  description = "The URL of the Cloud Storage bucket."
  value       = google_storage_bucket.migration_bucket.url
}