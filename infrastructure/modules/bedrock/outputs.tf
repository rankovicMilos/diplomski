output "bedrock_embedding_agent_arn" {
    description = "The ARN of the Bedrock agent."
    value       = data.aws_bedrock_foundation_model.titan_embeddings.model_arn
}

output "bedrock_claude_model_arn" {
    description = "The ARN of the Bedrock Claude model."
    value       = data.aws_bedrock_foundation_model.claude_sonnet_4.model_arn
}

output "bedrock_agent_arn" {
    description = "The ARN of the Bedrock Agent."
    value       = aws_bedrockagent_agent.bedrock_agent.agent_arn
}

output "inference_profile_model_arn" {
    description = "The ARN of the Claude Sonnet 4 inference profile."
    value       = data.aws_bedrock_inference_profile.claude_sonnet_4_inference_profile.inference_profile_arn
}