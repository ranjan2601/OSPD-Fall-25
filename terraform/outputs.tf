/**
 * Terraform outputs for AI-Chat Orchestrator
 */

output "orchestrator_service_url" {
  description = "URL of the deployed AI-Chat Orchestrator service"
  value       = google_cloud_run_service.orchestrator_service.status[0].url
}

output "artifact_registry_url" {
  description = "URL of the Artifact Registry repository"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.ai_chat_repo.repository_id}"
}

output "service_account_email" {
  description = "Email of the service account used by Cloud Run"
  value       = google_service_account.orchestrator_sa.email
}

output "dashboard_url" {
  description = "URL to view the monitoring dashboard"
  value       = "https://console.cloud.google.com/monitoring/dashboards/custom/${google_monitoring_dashboard.ai_chat_dashboard.id}?project=${var.project_id}"
}

output "secrets" {
  description = "Secret Manager secret names (values not exposed)"
  value = {
    gemini_api_key    = data.google_secret_manager_secret.gemini_api_key.secret_id
    discord_bot_token = data.google_secret_manager_secret.discord_bot_token.secret_id
    slack_bot_token   = data.google_secret_manager_secret.slack_bot_token.secret_id
  }
}
