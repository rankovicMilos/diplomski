data "aws_bedrock_foundation_model" "claude_sonnet_4" {
    model_id = "anthropic.claude-sonnet-4-20250514-v1:0"
}

data "aws_bedrock_foundation_model" "titan_embeddings" {
    model_id = "amazon.titan-embed-text-v2:0"
}

data "aws_bedrock_inference_profile" "claude_sonnet_4_inference_profile" {
    inference_profile_id = "eu.anthropic.claude-sonnet-4-20250514-v1:0"
}

resource "aws_bedrockagent_agent" "bedrock_agent" {
    agent_name = var.bedrock_agent_name
    foundation_model = data.aws_bedrock_foundation_model.claude_sonnet_4.model_arn
    idle_session_ttl_in_seconds = var.bedrock_agent_idle_session_ttl_in_seconds
    agent_resource_role_arn = var.bedrock_kb_execution_role_arn
    instruction = "You are a helpful AI assistant for credit risk analysts. Answer questions clearly and concisely."

    guardrail_configuration {
        guardrail_identifier = aws_bedrock_guardrail.bedrock_guardrail.guardrail_id
        guardrail_version = aws_bedrock_guardrail.bedrock_guardrail.version
    }

    tags = {
        Name = var.bedrock_agent_name
        Environment = "poc"
        ManagedBy = "terraform"
    }
}

# Unfortunately, S3 Vectors Knowledge Base integration is not yet supported in Terraform AWS Provider.

# The following resources are placeholders for when support is added.

# resource "aws_bedrockagent_knowledge_base" "bedrock__knowledge_base" {
# }

# resource "aws_bedrockagent_agent_knowledge_base_association" "bedrock_agent_kb_association" {
# }

# resource "aws_bedrockagent_data_source" "s3_benchmark_dataset_source" {
# }

# resource "aws_bedrockagent_data_source" "s3_cleaned_data_source" {
# }

resource "aws_bedrock_guardrail" "bedrock_guardrail" {
    name = var.bedrock_guardrail_name
    blocked_input_messaging = "Message blocked due to policy violation."
    blocked_outputs_messaging = "Output blocked due to policy violation."

    content_policy_config {
        filters_config {
            input_strength  = "HIGH"
            output_strength = "HIGH"
            type            = "HATE"
        }
        filters_config {
            input_strength  = "HIGH"
            output_strength = "HIGH"
            type            = "VIOLENCE"
        }
        filters_config {
            input_strength  = "HIGH"
            output_strength = "HIGH"
            type            = "SEXUAL"
        }
        tier_config {
            tier_name = "CLASSIC"
        }
    }
    

    tags = {
        Name = var.bedrock_guardrail_name
        Environment = "poc"
        ManagedBy = "terraform"
    }
}