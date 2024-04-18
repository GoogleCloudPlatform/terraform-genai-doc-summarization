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

output "neos_walkthrough_url" {
  value       = "https://console.cloud.google.com/?walkthrough_id=solutions-in-console--generative-ai--document-summarization--tour"
  description = "The URL to launch the in-console tutorial for the Generative AI Document Summarization solution"
}

output "unique_id" {
  value       = random_id.unique_id.hex
  description = "The unique ID for this deployment"
}

output "bucket_main_name" {
  value       = google_storage_bucket.main.name
  description = "The name of the main bucket created"
}

output "bucket_docs_name" {
  value       = google_storage_bucket.docs.name
  description = "The name of the docs bucket created"
}

output "documentai_processor_id" {
  value       = google_document_ai_processor.ocr.id
  description = "The full Document AI processor path ID"
}

output "bigquery_dataset_id" {
  value       = google_bigquery_dataset.main.dataset_id
  description = "The name of the BigQuery dataset created"
}
