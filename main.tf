terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.37"
    }
  }
}

variable "project_id" {
  description = "Google Cloud project ID"
  type        = string
}

variable "bucket_name" {
  description = "Globally unique bucket name for lottery data"
  type        = string
}

variable "location" {
  description = "Google Cloud region for the bucket and BigQuery dataset"
  type        = string
  default     = "us-east1"
}

provider "google" {
  project = var.project_id
  region  = var.location
}

resource "google_storage_bucket" "raw_lottery_data" {
  name     = var.bucket_name
  location = var.location

  # Optional, but recommended settings:
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
}
