# Generative AI Document Summarization

## Description
### Tagline
Create summaries of a large corpus of documents using Generative AI.

### Detailed
This solution showcases how to summarize a large corpus of documents using Generative AI. It provides an end-to-end demonstration of document summarization going all the way from raw documents, detecting text in the documents and summarizing the documents on-demand using Vertex AI LLM APIs, Document AI Optical Character Recognition (OCR), and BigQuery.

### PreDeploy
To deploy this blueprint you must have an active billing account and billing permissions.

## Architecture
![Document Summarization using Generative AI](https://www.gstatic.com/pantheon/images/solutions/gen_ai_document_summarization_architecture_v1.svg)

- User uploads a new document triggering the webhook Cloud Function.
- Document AI extracts the text from the document file.
- A Vertex AI Large Language Model summarizes the document text.
- The document summaries are stored in BigQuery.

## Documentation
- [Generative AI Document Summary](https://cloud.google.com/architecture/ai-ml/generative-ai-document-summarization)

## Deployment Duration
Configuration: 1 mins
Deployment: 5 mins

## Cost
[Cost Details](https://cloud.google.com/products/calculator/#id=4ce59084-5e4b-42c3-bad6-983f8618361c)

<!-- BEGINNING OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| disable\_services\_on\_destroy | Whether project services will be disabled when the resources are destroyed. | `bool` | `false` | no |
| documentai\_location | Document AI location, see https://cloud.google.com/document-ai/docs/regions | `string` | `"us"` | no |
| labels | A set of key/value label pairs to assign to the resources deployed by this blueprint. | `map(string)` | `{}` | no |
| project\_id | The Google Cloud project ID to deploy to | `string` | n/a | yes |
| region | The Google Cloud region to deploy to | `string` | `"us-central1"` | no |
| unique\_names | Whether to use unique names for resources | `bool` | `false` | no |

## Outputs

| Name | Description |
|------|-------------|
| bigquery\_dataset\_id | The name of the BigQuery dataset created |
| bucket\_docs\_name | The name of the docs bucket created |
| bucket\_main\_name | The name of the main bucket created |
| documentai\_processor\_id | The full Document AI processor path ID |
| neos\_walkthrough\_url | The URL to launch the in-console tutorial for the Generative AI Document Summarization solution |
| unique\_id | The unique ID for this deployment |

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
