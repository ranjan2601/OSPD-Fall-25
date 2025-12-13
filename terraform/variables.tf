/**
 * Terraform variables for AI-Chat Orchestrator deployment
 */

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP zone for resources"
  type        = string
  default     = "us-central1-a"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "access_token" {
  description = "GCP access token for authentication"
  type        = string
  default     = ""
  sensitive   = true
}
