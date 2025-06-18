# variables.tf
variable "project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "region" {
  description = "The GCP region for resources."
  type        = string
  default     = "us-central1"
}

variable "cloudsql_instance_name" {
  description = "Name for the Cloud SQL instance."
  type        = string
}

variable "cloudsql_database_name" {
  description = "Name for the database within Cloud SQL."
  type        = string
}

variable "cloudsql_user" {
  description = "Username for the Cloud SQL database."
  type        = string
}

variable "cloudsql_password" {
  description = "Password for the Cloud SQL database user."
  type        = string
  sensitive   = true
}

variable "cloudsql_machine_type" {
  description = "Machine type for the Cloud SQL instance (e.g., db-n1-standard-4)."
  type        = string
  default     = "db-n1-standard-4"
}

variable "cloudsql_disk_size_gb" {
  description = "Disk size in GB for the Cloud SQL instance."
  type        = number
  default     = 200
}

variable "cloudsql_ha_enabled" {
  description = "Enable High Availability for Cloud SQL."
  type        = bool
  default     = true
}

variable "cloudsql_private_ip_range_name" {
  description = "Name for the allocated IP range for private services access."
  type        = string
  default     = "google-managed-services-default"
}

variable "cloudsql_vpc_network" {
  description = "Name of the VPC network to use for Cloud SQL private IP."
  type        = string
  default     = "default"
}

variable "cloud_storage_bucket_name" {
  description = "Name for the Cloud Storage bucket for migration dumps."
  type        = string
}