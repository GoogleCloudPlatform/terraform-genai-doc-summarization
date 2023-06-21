/**
 * Copyright 2021 Google LLC
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

variable "project_id" {
  description = "The project ID to deploy to"
  type        = string
}

variable "bucket_name" {
  description = "The name of the bucket to create"
  type        = string
}

variable "region" {
  type        = string
  default = "us-central1"
}

variable "webhook_name" {
  type        = string
  default = "webhook"
}

variable "timeout_seconds" {
  type        = number
  default     = 900
}

variable "zone" {
  default = "us-central1-a"
  type    = string
}
