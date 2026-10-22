variable "bedrock_agent_name" {
    description = "The name of the Bedrock agent."
    type        = string
}

variable "bedrock_agent_idle_session_ttl_in_seconds" {
    description = "The idle session TTL in seconds for the Bedrock agent."
    type        = number
}

variable "bedrock_kb_execution_role_arn" {
    description = "The ARN of the IAM role for the Bedrock knowledge base."
    type        = string
}

variable "bedrock_guardrail_name" {
    description = "The name of the Bedrock guardrail."
    type        = string
}

