variable "project_id" {
  type        = string
}

variable "principal" {
  type        = string
}

variable "bucket" {
  type        = string
}

variable "region" {
  type        = string
  default = "us-central1"
}

variable "access_token" {
  type        = string
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

variable "revision" {
  type        = string
}