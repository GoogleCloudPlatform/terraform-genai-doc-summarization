data "google_project" "project" {
  project_id     = var.project_id
}

terraform {
  backend "gcs" {
    bucket  = null
    prefix  = null
  }
}

resource "google_project_service" "serviceusage" {
  service = "serviceusage.googleapis.com"
  project            = var.project_id
  disable_on_destroy = false
  disable_dependent_services = true
}

resource "google_project_service" "vision" {
  service = "vision.googleapis.com"
  project            = var.project_id
  disable_on_destroy = false
  disable_dependent_services = true
  depends_on = [
    google_project_service.serviceusage
  ]
}

resource "google_project_service" "cloudfunctions" {
  service = "cloudfunctions.googleapis.com"
  project            = var.project_id
  disable_on_destroy = false
  disable_dependent_services = true
  depends_on = [
    google_project_service.serviceusage
  ]
}

resource "google_project_service" "artifactregistry" {
  service = "artifactregistry.googleapis.com"
  project            = var.project_id
  disable_on_destroy = false
  disable_dependent_services = true
  depends_on = [
    google_project_service.serviceusage
  ]
}

resource "google_project_service" "eventarc" {
  service            = "eventarc.googleapis.com"
  project            = var.project_id
  disable_on_destroy = false
  depends_on = [
    google_project_service.serviceusage
  ]
}

resource "google_project_service" "bigquery" {
  service            = "bigquery.googleapis.com"
  project            = var.project_id
  disable_on_destroy = false
  depends_on = [
    google_project_service.serviceusage
  ]
}

resource "google_project_service" "aiplatform" {
  service            = "aiplatform.googleapis.com"
  project            = var.project_id
  disable_on_destroy = false
  depends_on = [
    google_project_service.serviceusage
  ]
}

resource "google_project_service" "storage" {
  service            = "storage.googleapis.com"
  project            = var.project_id
  disable_on_destroy = false
  depends_on = [
    google_project_service.serviceusage
  ]
}

resource "google_project_service" "cloudbuild" {
  service = "cloudbuild.googleapis.com"
  project            = var.project_id
  disable_on_destroy = false
  disable_dependent_services = true
  depends_on = [
    google_project_service.serviceusage
  ]
}

resource "google_project_service" "run" {
  service = "run.googleapis.com"
  project            = var.project_id
  disable_on_destroy = false
  disable_dependent_services = true
  depends_on = [
    google_project_service.serviceusage
  ]
}

resource "google_project_service" "iam" {
  service = "iam.googleapis.com"
  project            = var.project_id
  disable_on_destroy = false
  disable_dependent_services = true
  depends_on = [
    google_project_service.serviceusage
  ]
}

data "archive_file" "webhook" {
  type        = "zip"
  source_dir  = "webhook"
  output_path = abspath("./.tmp/${var.webhook_name}.zip")
}

resource "google_storage_bucket_object" "webhook" {
  name   = "${var.webhook_name}.${data.archive_file.webhook.output_base64sha256}.zip"
  bucket = var.bucket
  source = data.archive_file.webhook.output_path
}

resource "google_service_account" "webhook" {
  project = var.project_id
  account_id   = "webhook-service-account"
  display_name = "Serverless Webhooks Service Account"
  depends_on = [
    google_project_service.iam,
  ]
}

resource "google_project_iam_member" "aiplatform_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member = "serviceAccount:${google_service_account.webhook.email}"
  depends_on = [
    google_project_service.iam
  ]
}

resource "google_project_iam_member" "storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member = "serviceAccount:${google_service_account.webhook.email}"
  depends_on = [
    google_project_service.iam
  ]
}

resource "google_project_iam_member" "log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member = "serviceAccount:${google_service_account.webhook.email}"
  depends_on = [
    google_project_service.iam
  ]
}

resource "google_project_iam_member" "data_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member = "serviceAccount:${google_service_account.webhook.email}"
  depends_on = [
    google_project_service.iam
  ]
}

resource "google_project_iam_member" "artifactregistry_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member = "serviceAccount:${google_service_account.webhook.email}"
  depends_on = [
    google_project_service.iam
  ]
}

resource "google_cloudfunctions2_function" "webhook" {
  project = var.project_id
  name        = var.webhook_name
  location    = var.region

  build_config {
    runtime     = "python310"
    entry_point = "entrypoint"
    source {
      storage_source {
        bucket = var.bucket
        object = google_storage_bucket_object.webhook.name
      }
    }
  }


  service_config {
    service_account_email = google_service_account.webhook.email
    max_instance_count = 100
    available_memory   = "4G"
    available_cpu = 2
    max_instance_request_concurrency = 16
    timeout_seconds    = var.timeout_seconds
    environment_variables = {
      PROJECT_ID = var.project_id
      PRINCIPAL = var.principal
      LOCATION = var.region
      REVISION = var.revision
      OUTPUT_BUCKET = google_storage_bucket.output.name
      DATASET_ID = google_bigquery_dataset.default.dataset_id
      TABLE_ID = google_bigquery_table.default.table_id
    }
  }
  depends_on = [
    google_project_service.artifactregistry,
    google_project_service.cloudbuild,
    google_project_service.run,
    google_project_service.vision,
  ]
}

resource "google_bigquery_dataset" "default" {
  dataset_id = "summary_dataset"
  project    = var.project_id
}

resource "google_bigquery_table" "default" {
  dataset_id = google_bigquery_dataset.default.dataset_id
  table_id   = "summary_table"
  project    = var.project_id

  schema = <<EOF
[
  {
    "name": "bucket",
    "type": "STRING",
    "description": "Source bucket of artifact"
  },
  {
    "name": "filename",
    "type": "STRING",
    "description": "Filename of the source artifact"
  },
  {
    "name": "extracted_text",
    "type": "STRING",
    "description": "Text extracted from the source artifact"
  },
  {
    "name": "summary_uri",
    "type": "STRING",
    "description": "The Storage URI of the complete document text"
  },
  {
    "name": "complete_text_uri",
    "type": "STRING",
    "description": "The Storage URI of the complete document text"
  },
  {
    "name": "summary",
    "type": "STRING",
    "description": "Text summary generated by the LLM"
  },
  {
    "name": "timestamp",
    "type": "TIMESTAMP",
    "description": "TeTimestamp that the processing occurred on"
  }
]
EOF
}

resource "google_storage_bucket" "uploads" {
  project    = var.project_id
  name          = "${var.project_id}_uploads"
  location      = var.region
  force_destroy = true
  uniform_bucket_level_access = true
}

resource "google_storage_bucket" "output" {
  project    = var.project_id
  name          = "${var.project_id}_output"
  location      = var.region
  force_destroy = true
  uniform_bucket_level_access = true
}

resource "google_service_account" "upload_trigger" {
  project = var.project_id
  account_id   = "upload-trigger-service-account"
  display_name = "Eventarc Service Account"
  depends_on = [
    google_project_service.iam,
  ]
}

resource "google_project_iam_member" "event_receiver" {
  project = var.project_id
  role    = "roles/eventarc.eventReceiver"
  member = "serviceAccount:${google_service_account.upload_trigger.email}"
  depends_on = [
    google_project_service.iam
  ]
}

resource "google_project_iam_member" "run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member = "serviceAccount:${google_service_account.upload_trigger.email}"
  depends_on = [
    google_project_service.iam
  ]
}
resource "google_project_iam_member" "pubsub_publisher" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member = "serviceAccount:service-${data.google_project.project.number}@gs-project-accounts.iam.gserviceaccount.com"
  depends_on = [
    google_project_service.iam
  ]
}
  
resource "google_eventarc_trigger" "summarization" {
  project    = var.project_id
  name = "terraformdev"
  location = var.region
  matching_criteria {
      attribute = "type"
      value = "google.cloud.storage.object.v1.finalized"
  }
  matching_criteria {
    attribute = "bucket"
    value     = google_storage_bucket.uploads.name
  }
  destination {
      cloud_run_service {
          service = google_cloudfunctions2_function.webhook.name
          region = var.region
      }
  }
  service_account = google_service_account.upload_trigger.email
  depends_on = [
    google_project_iam_member.event_receiver,
    google_project_iam_member.run_invoker,
    google_project_iam_member.pubsub_publisher,
  ]
}
