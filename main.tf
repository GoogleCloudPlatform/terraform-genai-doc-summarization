/**
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

module "project_services" {
  source                      = "terraform-google-modules/project-factory/google//modules/project_services"
  version                     = "~> 18.0"
  disable_services_on_destroy = var.disable_services_on_destroy

  project_id = var.project_id

  activate_apis = [
    "aiplatform.googleapis.com",
    "artifactregistry.googleapis.com",
    "bigquery.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudfunctions.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "compute.googleapis.com",
    "config.googleapis.com",
    "documentai.googleapis.com",
    "eventarc.googleapis.com",
    "iam.googleapis.com",
    "run.googleapis.com",
    "serviceusage.googleapis.com",
    "storage-api.googleapis.com",
    "storage.googleapis.com",
  ]
}

resource "random_id" "unique_id" {
  byte_length = 3
}

locals {
  bucket_main_name   = var.unique_names ? "summary-main-${var.project_id}-${random_id.unique_id.hex}" : "summary-main-${var.project_id}"
  bucket_docs_name   = var.unique_names ? "summary-docs-${var.project_id}-${random_id.unique_id.hex}" : "summary-docs-${var.project_id}"
  webhook_name       = var.unique_names ? "summary-webhook-${random_id.unique_id.hex}" : "summary-webhook"
  webhook_sa_name    = var.unique_names ? "summary-webhook-sa-${random_id.unique_id.hex}" : "summary-webhook-sa"
  artifact_repo_name = var.unique_names ? "summary-artifact-repo-${random_id.unique_id.hex}" : "summary-artifact-repo"
  trigger_name       = var.unique_names ? "summary-trigger-${random_id.unique_id.hex}" : "summary-trigger"
  trigger_sa_name    = var.unique_names ? "summary-trigger-sa-${random_id.unique_id.hex}" : "summary-trigger-sa"
  ocr_processor_name = var.unique_names ? "summary-ocr-processor-${random_id.unique_id.hex}" : "summary-ocr-processor"
  bq_dataset_name    = var.unique_names ? "summary_dataset_${random_id.unique_id.hex}" : "summary_dataset"
}

#-- Cloud Storage buckets --#
resource "google_storage_bucket" "main" {
  project                     = module.project_services.project_id
  name                        = local.bucket_main_name
  location                    = var.region
  force_destroy               = true
  uniform_bucket_level_access = true
  labels                      = var.labels
}

resource "google_storage_bucket" "docs" {
  project                     = module.project_services.project_id
  name                        = local.bucket_docs_name
  location                    = var.region
  force_destroy               = true
  uniform_bucket_level_access = true
  labels                      = var.labels
}

#-- Cloud Function webhook --#
resource "google_cloudfunctions2_function" "webhook" {
  project  = module.project_services.project_id
  name     = local.webhook_name
  location = var.region
  labels   = var.labels

  build_config {
    runtime           = "python312"
    entry_point       = "on_cloud_event"
    docker_repository = google_artifact_registry_repository.webhook_images.id
    source {
      storage_source {
        bucket = google_storage_bucket.main.name
        object = google_storage_bucket_object.webhook_staging.name
      }
    }
  }

  service_config {
    available_memory      = "1G"
    service_account_email = google_service_account.webhook.email
    environment_variables = {
      PROJECT_ID       = module.project_services.project_id
      LOCATION         = var.region
      OUTPUT_BUCKET    = google_storage_bucket.main.name
      DOCAI_PROCESSOR  = google_document_ai_processor.ocr.id
      DOCAI_LOCATION   = google_document_ai_processor.ocr.location
      BQ_DATASET       = google_bigquery_dataset.main.dataset_id
      BQ_TABLE         = google_bigquery_table.main.table_id
      LOG_EXECUTION_ID = true
    }
  }
}

resource "google_project_iam_member" "webhook" {
  project = module.project_services.project_id
  member  = google_service_account.webhook.member
  for_each = toset([
    "roles/aiplatform.serviceAgent", # https://cloud.google.com/iam/docs/service-agents
    "roles/bigquery.dataEditor",     # https://cloud.google.com/bigquery/docs/access-control
    "roles/documentai.apiUser",      # https://cloud.google.com/document-ai/docs/access-control/iam-roles
  ])
  role = each.key
}

resource "google_service_account" "webhook" {
  project      = module.project_services.project_id
  account_id   = local.webhook_sa_name
  display_name = "Doc summary webhook"
}

resource "google_artifact_registry_repository" "webhook_images" {
  project       = module.project_services.project_id
  location      = var.region
  repository_id = local.artifact_repo_name
  format        = "DOCKER"
  labels        = var.labels
}

data "archive_file" "webhook_staging" {
  type        = "zip"
  source_dir  = abspath("${path.module}/webhook")
  output_path = abspath("${path.module}/.tmp/webhook.zip")
  excludes = [
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "env",
  ]
}

resource "google_storage_bucket_object" "webhook_staging" {
  name   = "webhook-staging/${data.archive_file.webhook_staging.output_base64sha256}.zip"
  bucket = google_storage_bucket.main.name
  source = data.archive_file.webhook_staging.output_path
}

#-- Eventarc trigger --#
resource "google_eventarc_trigger" "trigger" {
  project         = module.project_services.project_id
  location        = var.region
  name            = local.trigger_name
  service_account = google_service_account.trigger.email
  labels          = var.labels

  matching_criteria {
    attribute = "type"
    value     = "google.cloud.storage.object.v1.finalized"
  }
  matching_criteria {
    attribute = "bucket"
    value     = google_storage_bucket.docs.name
  }

  destination {
    cloud_run_service {
      service = google_cloudfunctions2_function.webhook.name
      region  = var.region
    }
  }
}

#-- Eventarc trigger for deletion events --#
resource "google_eventarc_trigger" "delete_trigger" {
  project         = module.project_services.project_id
  location        = var.region
  name            = "${local.trigger_name}-delete"
  service_account = google_service_account.trigger.email
  labels          = var.labels

  matching_criteria {
    attribute = "type"
    value     = "google.cloud.storage.object.v1.deleted"
  }
  matching_criteria {
    attribute = "bucket"
    value     = google_storage_bucket.docs.name
  }

  destination {
    cloud_run_service {
      service = google_cloudfunctions2_function.webhook.name
      region  = var.region
    }
  }
}

resource "google_project_iam_member" "trigger" {
  project = module.project_services.project_id
  member  = google_service_account.trigger.member
  for_each = toset([
    "roles/eventarc.eventReceiver", # https://cloud.google.com/eventarc/docs/access-control
    "roles/run.invoker",            # https://cloud.google.com/run/docs/reference/iam/roles
  ])
  role = each.key
}

resource "google_service_account" "trigger" {
  project      = module.project_services.project_id
  account_id   = local.trigger_sa_name
  display_name = "Doc summary Eventarc trigger"
}

#-- Cloud Storage Eventarc agent --#
resource "google_project_iam_member" "gcs_account" {
  project = module.project_services.project_id
  member  = "serviceAccount:${data.google_storage_project_service_account.gcs_account.email_address}"
  role    = "roles/pubsub.publisher" # https://cloud.google.com/pubsub/docs/access-control
}

data "google_storage_project_service_account" "gcs_account" {
  project = module.project_services.project_id
}

resource "google_project_iam_member" "eventarc_agent" {
  project = module.project_services.project_id
  member  = "serviceAccount:${google_project_service_identity.eventarc_agent.email}"
  role    = "roles/eventarc.serviceAgent" # https://cloud.google.com/iam/docs/service-agents
}

resource "google_project_service_identity" "eventarc_agent" {
  provider = google-beta
  project  = module.project_services.project_id
  service  = "eventarc.googleapis.com"
}

#-- Document AI --#
resource "google_document_ai_processor" "ocr" {
  project      = module.project_services.project_id
  location     = var.documentai_location
  display_name = local.ocr_processor_name
  type         = "OCR_PROCESSOR"
}

#-- BigQuery --#
resource "google_bigquery_dataset" "main" {
  project                    = module.project_services.project_id
  dataset_id                 = local.bq_dataset_name
  delete_contents_on_destroy = true
}

resource "google_bigquery_table" "main" {
  project             = module.project_services.project_id
  dataset_id          = google_bigquery_dataset.main.dataset_id
  table_id            = "summaries"
  schema              = file("${path.module}/schema.json")
  deletion_protection = false
}
