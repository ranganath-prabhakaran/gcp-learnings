# main.tf
provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_compute_network" "vpc_network" {
  name = var.cloudsql_vpc_network
  auto_create_subnetworks = true
}

resource "google_compute_global_address" "private_ip_alloc" {
  name          = var.cloudsql_private_ip_range_name
  purpose       = "VPC_PEERING"
  prefix_length = 16
  network       = google_compute_network.vpc_network.id
  address_type  = "INTERNAL"
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc_network.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_alloc.name]
}

resource "google_sql_database_instance" "mysql_instance" {
  database_version = "MYSQL_8_0" # Or desired version
  name             = var.cloudsql_instance_name
  region           = var.region
  settings {
    tier = var.cloudsql_machine_type
    disk_size = var.cloudsql_disk_size_gb
    disk_type = "SSD"
    backup_configuration {
      enabled            = true
      binary_log_enabled = true
      start_time         = "03:00" # UTC time
    }
    ip_configuration {
      ipv4_enabled = false
      private_network = google_compute_network.vpc_network.id
      # authorized_networks { value = "10.0.0.0/8" } # Example if specific internal ranges need authorization
    }
    location_preference {
      zone = "${var.region}-a" # Or specific zone for HA
    }
    availability_type = var.cloudsql_ha_enabled? "REGIONAL" : "ZONAL"
    database_flags {
      name  = "require_secure_transport"
      value = "ON"
    }
    password_validation_policy {
      enabled = true
      min_length = 12
      require_uppercase = true
      require_lowercase = true
      require_number = true
      require_symbol = true
    }
  }
  depends_on = [google_service_networking_connection.private_vpc_connection]
}

resource "google_sql_database" "database" {
  name     = var.cloudsql_database_name
  instance = google_sql_database_instance.mysql_instance.name
  charset  = "utf8mb4"
  collation = "utf8mb4_unicode_ci"
}

resource "google_sql_user" "db_user" {
  name     = var.cloudsql_user
  instance = google_sql_database_instance.mysql_instance.name
  host     = "%" # Allow connections from any host within the private network
  password = var.cloudsql_password
}

resource "google_storage_bucket" "migration_bucket" {
  name          = var.cloud_storage_bucket_name
  location      = "US-CENTRAL1" # Or desired region
  force_destroy = false # Set to true for easy cleanup in dev, but be careful
  uniform_bucket_level_access = true # Security best practice [9]
  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 7 # Delete objects older than 7 days (adjust as needed)
    }
  }
}