/**
 * Terraform outputs for AI-Chat Orchestrator
 */

output "gemini_service_url" {
  description = "URL of the deployed Gemini AI service"
  value       = google_cloud_run_service.gemini_service.status[0].url
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
    gemini_api_key       = google_secret_manager_secret.gemini_api_key.secret_id
    discord_client_id    = google_secret_manager_secret.discord_client_id.secret_id
    discord_client_secret = google_secret_manager_secret.discord_client_secret.secret_id
    slack_token          = google_secret_manager_secret.slack_token.secret_id
  }
}
