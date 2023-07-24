# Generative AI Document Summarization

## Description
### Tagline
Create summaries of a large corpus of documents using Generative AI.

### Detailed
This solution showcases how to summarize a large corpus of documents using Generative AI. It provides an
end-to-end demonstration of document summarization going all the way from raw documents, detecting text
in the documents and summarizing the documents on-demand using Vertex AI LLM APIs, Cloud Vision Optical
Character Recognition (OCR) and BigQuery.

### PreDeploy
To deploy this blueprint you must have an active billing account and billing permissions.

## Architecture
![Document Summarization using Generative AI](https://www.gstatic.com/pantheon/images/solutions/gen_ai_document_summarization_architecture_v1.svg)
1. The developer follows a tutorial on a Jupyter Notebook, where they upload a PDF — either through Vertex AI Workbench or Colaboratory.
2. The uploaded PDF file is sent to a function running on Cloud Functions. This function handles PDF file processing.
3. The Cloud Functions function uses Cloud Vision to extract all text from the PDF file.
4. The Cloud Functions function stores the extracted text inside a Cloud Storage bucket.
5. The Cloud Functions function uses Vertex AI’s LLM API to summarize the extracted text.
6. The Cloud Functions function stores the text summaries of PDFs in BigQuery tables.
7. As an alternative to uploading PDF files through Jupyter Notebook, the developer can upload a PDF file directly to a Cloud Storage
bucket — for instance, through the Console UI or gcloud. This upload triggers Eventarc to begin the Document Processing phase.
8. As a result of the direct upload to Cloud Storage, Eventarc triggers the Document Processing phase, handled by Cloud Functions.

## Documentation
- [Generative AI Document Summary](https://cloud.google.com/architecture/ai-ml/generative-ai-document-summarization)

## Deployment Duration
Configuration: 1 mins
Deployment: 10 mins

## Cost
[Cost Details](https://cloud.google.com/products/calculator/#id=78888c9b-02ac-4130-9327-fecd7f4cfb11)

<!-- BEGINNING OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| bucket\_name | The name of the bucket to create | `string` | `"genai-webhook"` | no |
| gcf\_timeout\_seconds | GCF execution timeout | `number` | `900` | no |
| project\_id | The Google Cloud project ID to deploy to | `string` | n/a | yes |
| region | Google Cloud region | `string` | `"us-central1"` | no |
| time\_to\_enable\_apis | Wait time to enable APIs in new projects | `string` | `"180s"` | no |
| webhook\_name | Name of the webhook | `string` | `"webhook"` | no |
| webhook\_path | Path to the webhook directory | `string` | `"webhook"` | no |

## Outputs

| Name | Description |
|------|-------------|
| genai\_doc\_summary\_colab\_url | The URL to launch the notebook tutorial for the Generateive AI Document Summarization Solution |
| neos\_walkthrough\_url | The URL to launch the in-console tutorial for the Generative AI Document Summarization solution |

<!-- END OF PRE-COMMIT-TERRAFORM DOCS HOOK -->

## Requirements

These sections describe requirements for using this module.

### Software

The following dependencies must be available:

- [Terraform][terraform] v0.13
- [Terraform Provider for GCP][terraform-provider-gcp] plugin v3.0

### Service Account

A service account with the following roles must be used to provision
the resources of this module:

- Storage Admin: `roles/storage.admin`

### APIs

A project with the following APIs enabled must be used to host the
resources of this module:

- Google Cloud Storage JSON API: `storage-api.googleapis.com`

## Contributing

Refer to the [contribution guidelines](./docs/CONTRIBUTING.md) for
information on contributing to this module.

[iam-module]: https://registry.terraform.io/modules/terraform-google-modules/iam/google
[project-factory-module]: https://registry.terraform.io/modules/terraform-google-modules/project-factory/google
[terraform-provider-gcp]: https://www.terraform.io/docs/providers/google/index.html
[terraform]: https://www.terraform.io/downloads.html

## Security Disclosures

Please see our [security disclosure process](./SECURITY.md).
