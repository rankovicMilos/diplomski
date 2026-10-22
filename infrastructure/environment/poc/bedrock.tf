module "bedrock" {
  source = "../../modules/bedrock"

  # Bedrock Agent Configuration
  bedrock_agent_name                        = "${local.prefix}-bedrock-agent"
  bedrock_agent_idle_session_ttl_in_seconds = 300
  bedrock_kb_execution_role_arn             = module.bedrock_kb_execution_role.role_arn

  # Guardrail Configuration
  bedrock_guardrail_name = "${local.prefix}-bedrock-guardrail"
}