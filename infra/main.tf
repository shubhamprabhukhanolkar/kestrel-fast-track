terraform {
  required_version = ">= 1.6"
  required_providers {
    google = { source = "hashicorp/google", version = "~> 6.0" }
  }
}
provider "google" {
  project = var.project_id
  region = "asia-south1"
}
variable "project_id" {
  type = string
  default = "slabspro-slabsuser37"
}
variable "documents_bucket" { type = string }

# Provision deliberately, after reviewing terraform plan and lab permissions/costs.
resource "google_project_service" "api" {
  for_each = toset(["sqladmin.googleapis.com", "storage.googleapis.com", "cloudtasks.googleapis.com", "secretmanager.googleapis.com", "run.googleapis.com"])
  service = each.value
  disable_on_destroy = false
}
resource "google_service_account" "runtime" {
  account_id = "kestrel-runtime"
  display_name = "Kestrel live workbench runtime"
}
resource "google_service_account" "tasks" {
  account_id = "kestrel-tasks"
  display_name = "Kestrel authenticated pipeline dispatch"
}
resource "google_storage_bucket" "documents" {
  name = var.documents_bucket
  location = "ASIA-SOUTH1"
  uniform_bucket_level_access = true
  public_access_prevention = "enforced"
  force_destroy = false
  versioning { enabled = true }
  depends_on = [google_project_service.api]
}
resource "google_storage_bucket_iam_member" "runtime" {
  for_each = toset(["roles/storage.objectCreator", "roles/storage.objectViewer"])
  bucket = google_storage_bucket.documents.name
  role = each.value
  member = "serviceAccount:${google_service_account.runtime.email}"
}
resource "google_sql_database_instance" "database" {
  name = "kestrel-live"
  region = "asia-south1"
  database_version = "POSTGRES_16"
  deletion_protection = true
  settings {
    tier = "db-custom-2-7680"
    availability_type = "REGIONAL"
    disk_autoresize = true
    backup_configuration {
      enabled = true
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
    }
    ip_configuration {
      ipv4_enabled = true
      ssl_mode = "ENCRYPTED_ONLY"
      # No authorized public networks. The Cloud Run Cloud SQL socket uses IAM-authorized connectivity.
    }
  }
  depends_on = [google_project_service.api]
}
resource "google_sql_database" "kestrel" {
  name = "kestrel"
  instance = google_sql_database_instance.database.name
}
resource "google_cloud_tasks_queue" "pipeline" {
  name = "kestrel-pipeline"
  location = "asia-south1"
  rate_limits {
    max_concurrent_dispatches = 2
    max_dispatches_per_second = 2
  }
  retry_config {
    max_attempts = 10
    min_backoff = "15s"
    max_backoff = "120s"
    max_retry_duration = "3600s"
  }
  depends_on = [google_project_service.api]
}
resource "google_project_iam_member" "runtime_roles" {
  for_each = toset(["roles/cloudsql.client", "roles/cloudtasks.enqueuer"])
  project = var.project_id
  role = each.value
  member = "serviceAccount:${google_service_account.runtime.email}"
}
resource "google_service_account_iam_member" "dispatch_identity" {
  service_account_id = google_service_account.tasks.name
  role = "roles/iam.serviceAccountUser"
  member = "serviceAccount:${google_service_account.runtime.email}"
}
# Create these secret versions through Secret Manager; plaintext values never enter Terraform state.
resource "google_secret_manager_secret" "runtime" {
  for_each = toset(["kestrel-database-url", "kestrel-groq-api-key", "kestrel-gemini-api-key"])
  secret_id = each.value
  replication {
    user_managed {
      replicas {
        location = "asia-south1"
      }
    }
  }
  depends_on = [google_project_service.api]
}
resource "google_secret_manager_secret_iam_member" "runtime" {
  for_each = google_secret_manager_secret.runtime
  secret_id = each.value.id
  role = "roles/secretmanager.secretAccessor"
  member = "serviceAccount:${google_service_account.runtime.email}"
}
output "runtime_service_account" { value = google_service_account.runtime.email }
output "task_service_account" { value = google_service_account.tasks.email }
output "cloud_sql_connection" { value = google_sql_database_instance.database.connection_name }
output "documents_bucket" { value = google_storage_bucket.documents.name }
