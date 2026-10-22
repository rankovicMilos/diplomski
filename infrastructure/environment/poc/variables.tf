variable "aws_region" {
  description = "The AWS region to deploy resources in."
  type        = string
  default     = "eu-central-1"
}
variable "project_prefix" {
  description = "Prefix of every resource name."
  type        = string
  default     = "sra-thesis"
}

variable "knowledge_base_id" {
  description = "ID of the Bedrock Knowledge Base (created in the console; see README)."
  type        = string
  default     = ""
}

variable "frontend_origin" {
  description = "Origin of the website, allowed by the S3 bucket CORS rules (e.g. the CloudFront URL)."
  type        = string
  default     = "http://localhost:3000"
}

variable "anthropic_api_key" {
  description = "Anthropic API key for the orchestrator Lambda (pass via TF_VAR_anthropic_api_key; stored in state)."
  type        = string
  sensitive   = true
  default     = ""
}

variable "claude_model" {
  description = "Claude model used for report generation."
  type        = string
  default     = "claude-sonnet-5-5"
}
