data "google_project" "project" {
  project_id     = var.project_id
}

terraform {
  backend "gcs" {
    bucket  = null
    prefix  = null
  }
}