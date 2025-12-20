/**
 * Main Terraform configuration for AI-Chat Orchestrator
 * Deploys services to Google Cloud Platform
 */

terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Configure the Google Cloud Provider
provider "google" {
  project      = var.project_id
  region       = var.region
  zone         = var.zone
  access_token = var.access_token
}

# Enable required GCP APIs
resource "google_project_service" "compute" {
  service            = "compute.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cloud_run" {
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cloud_build" {
  service            = "cloudbuild.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "artifact_registry" {
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "monitoring" {
  service            = "monitoring.googleapis.com"
  disable_on_destroy = false
}

# Create Artifact Registry for Docker images
resource "google_artifact_registry_repository" "ai_chat_repo" {
  location      = var.region
  repository_id = "ai-chat-orchestrator"
  description   = "Docker repository for AI-Chat integration services"
  format        = "DOCKER"

  depends_on = [google_project_service.artifact_registry]
}

# Reference existing secrets (managed outside Terraform)
data "google_secret_manager_secret" "gemini_api_key" {
  secret_id = "gemini-api-key"
}

data "google_secret_manager_secret" "discord_bot_token" {
  secret_id = "discord-bot-token"
}

data "google_secret_manager_secret" "slack_bot_token" {
  secret_id = "slack-bot-token"
}

# Optional Google Tasks secrets
data "google_secret_manager_secret" "tasks_client_id" {
  secret_id = "tasks-client-id"
}

data "google_secret_manager_secret" "tasks_client_secret" {
  secret_id = "tasks-client-secret"
}

data "google_secret_manager_secret" "tasks_refresh_token" {
  secret_id = "tasks-refresh-token"
}

# Read .env file for non-secret environment variables
locals {
  # Read .env file
  env_file = file("../.env")

  # Parse .env into a map (key=value format)
  env_lines = [for line in split("\n", local.env_file) : line if length(trimspace(line)) > 0 && !startswith(trimspace(line), "#")]

  env_vars = { for line in local.env_lines :
    split("=", line)[0] => trimspace(join("=", slice(split("=", line), 1, length(split("=", line)))))
    if length(split("=", line)) >= 2
  }

  # Define which env vars are secrets (exclude from env vars)
  secret_keys = [
    "GEMINI_API_KEY",
    "DISCORD_BOT_TOKEN",
    "SLACK_BOT_TOKEN",
    "TASKS_CLIENT_ID",
    "TASKS_CLIENT_SECRET",
    "TASKS_REFRESH_TOKEN",
  ]

  # Non-secret env vars only
  non_secret_env_vars = { for k, v in local.env_vars : k => v
    if !contains(local.secret_keys, k) && length(v) > 0
  }
}

# Service Account for Cloud Run
resource "google_service_account" "orchestrator_sa" {
  account_id   = "ai-chat-orchestrator"
  display_name = "AI-Chat Orchestrator Service Account"
  description  = "Service account for AI-Chat orchestrator services"
}

# Grant Secret Manager access to service account
resource "google_secret_manager_secret_iam_member" "gemini_access" {
  secret_id = data.google_secret_manager_secret.gemini_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.orchestrator_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "discord_access" {
  secret_id = data.google_secret_manager_secret.discord_bot_token.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.orchestrator_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "slack_access" {
  secret_id = data.google_secret_manager_secret.slack_bot_token.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.orchestrator_sa.email}"
}

# Grant access to optional Google Tasks secrets
resource "google_secret_manager_secret_iam_member" "tasks_client_id_access" {
  secret_id = data.google_secret_manager_secret.tasks_client_id.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.orchestrator_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "tasks_client_secret_access" {
  secret_id = data.google_secret_manager_secret.tasks_client_secret.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.orchestrator_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "tasks_refresh_token_access" {
  secret_id = data.google_secret_manager_secret.tasks_refresh_token.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.orchestrator_sa.email}"
}

# Grant Monitoring Metric Writer permission for metrics export
resource "google_project_iam_member" "monitoring_metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.orchestrator_sa.email}"
}

# Cloud Monitoring - Latency Metric Descriptor
resource "google_monitoring_metric_descriptor" "request_latency" {
  description  = "Request latency in milliseconds"
  display_name = "AI-Chat Request Latency"
  type         = "custom.googleapis.com/ai_chat/request_latency"
  metric_kind  = "GAUGE"
  value_type   = "DOUBLE"

  labels {
    key         = "service"
    value_type  = "STRING"
    description = "Service name (orchestrator, gemini, discord, slack)"
  }

  labels {
    key         = "operation"
    value_type  = "STRING"
    description = "Operation type (handle_message, process_direct, ai_generate, chat_send)"
  }

  depends_on = [google_project_service.monitoring]
}

# Cloud Monitoring - Success Rate Metric
resource "google_monitoring_metric_descriptor" "success_rate" {
  description  = "Success rate percentage"
  display_name = "AI-Chat Success Rate"
  type         = "custom.googleapis.com/ai_chat/success_rate"
  metric_kind  = "GAUGE"
  value_type   = "DOUBLE"

  labels {
    key         = "service"
    value_type  = "STRING"
    description = "Service name"
  }

  depends_on = [google_project_service.monitoring]
}

# Cloud Monitoring - Failure Rate Metric
resource "google_monitoring_metric_descriptor" "failure_rate" {
  description  = "Failure rate percentage"
  display_name = "AI-Chat Failure Rate"
  type         = "custom.googleapis.com/ai_chat/failure_rate"
  metric_kind  = "GAUGE"
  value_type   = "DOUBLE"

  labels {
    key         = "service"
    value_type  = "STRING"
    description = "Service name"
  }

  depends_on = [google_project_service.monitoring]
}

# Cloud Run service for AI-Chat Orchestrator Service
resource "google_cloud_run_service" "orchestrator_service" {
  name     = "ai-chat-orchestrator"
  location = var.region

  template {
    spec {
      service_account_name = google_service_account.orchestrator_sa.email

      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.ai_chat_repo.repository_id}/orchestrator-service:v3.15"

        # Secret environment variables
        env {
          name = "GEMINI_API_KEY"
          value_from {
            secret_key_ref {
              name = data.google_secret_manager_secret.gemini_api_key.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name = "DISCORD_BOT_TOKEN"
          value_from {
            secret_key_ref {
              name = data.google_secret_manager_secret.discord_bot_token.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name = "SLACK_BOT_TOKEN"
          value_from {
            secret_key_ref {
              name = data.google_secret_manager_secret.slack_bot_token.secret_id
              key  = "latest"
            }
          }
        }

        # Optional Google Tasks secrets
        env {
          name = "TASKS_CLIENT_ID"
          value_from {
            secret_key_ref {
              name = data.google_secret_manager_secret.tasks_client_id.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name = "TASKS_CLIENT_SECRET"
          value_from {
            secret_key_ref {
              name = data.google_secret_manager_secret.tasks_client_secret.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name = "TASKS_REFRESH_TOKEN"
          value_from {
            secret_key_ref {
              name = data.google_secret_manager_secret.tasks_refresh_token.secret_id
              key  = "latest"
            }
          }
        }

        # GCP_PROJECT for metrics export
        env {
          name  = "GCP_PROJECT"
          value = var.project_id
        }

        # Non-secret env vars from .env
        dynamic "env" {
          for_each = local.non_secret_env_vars
          content {
            name  = env.key
            value = env.value
          }
        }

        ports {
          container_port = 8000
        }

        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }
      }
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = "10"
        "autoscaling.knative.dev/minScale" = "0"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [
    google_project_service.cloud_run,
    google_artifact_registry_repository.ai_chat_repo
  ]
}

# Allow unauthenticated access to orchestrator service (or configure as needed)
resource "google_cloud_run_service_iam_member" "orchestrator_public" {
  service  = google_cloud_run_service.orchestrator_service.name
  location = google_cloud_run_service.orchestrator_service.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Monitoring Dashboard
resource "google_monitoring_dashboard" "ai_chat_dashboard" {
  dashboard_json = jsonencode({
    displayName = "AI-Chat Orchestrator Dashboard"
    mosaicLayout = {
      columns = 12
      tiles = [
        {
          xPos   = 0
          yPos   = 0
          width  = 6
          height = 4
          widget = {
            title = "Request Latency"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"custom.googleapis.com/ai_chat/request_latency\""
                  }
                }
                plotType = "LINE"
              }]
              yAxis = {
                label = "Latency (ms)"
                scale = "LINEAR"
              }
            }
          }
        },
        {
          xPos   = 6
          yPos   = 0
          width  = 6
          height = 4
          widget = {
            title = "Success vs Failure Rate"
            xyChart = {
              dataSets = [
                {
                  timeSeriesQuery = {
                    timeSeriesFilter = {
                      filter = "metric.type=\"custom.googleapis.com/ai_chat/success_rate\""
                    }
                  }
                  plotType = "LINE"
                },
                {
                  timeSeriesQuery = {
                    timeSeriesFilter = {
                      filter = "metric.type=\"custom.googleapis.com/ai_chat/failure_rate\""
                    }
                  }
                  plotType = "LINE"
                }
              ]
              yAxis = {
                label = "Rate (%)"
                scale = "LINEAR"
              }
            }
          }
        }
      ]
    }
  })

  depends_on = [
    google_monitoring_metric_descriptor.request_latency,
    google_monitoring_metric_descriptor.success_rate,
    google_monitoring_metric_descriptor.failure_rate
  ]
}
