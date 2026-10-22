module "api" {
  source = "../../modules/api_gateway"

  # API Gateway configuration
  rest_api_name  = "${local.prefix}-rest-api"
  api_stage_name = "poc"

  # Monitoring
  log_group_arn              = module.api_gw_log_group.log_group_arn
  api_gw_cloudwatch_role_arn = module.api_gw_cloudwatch_role.role_arn

  # Lambda function names needed for invoke permissions
  trigger_upload_lambda_name           = module.trigger_upload.function_name
  orchestrator_lambda_name             = module.orchestrator.function_name
  get_analyses_lambda_name             = module.get_analyses.function_name
  get_analyses_by_category_lambda_name = module.get_analyses_by_category.function_name
  get_client_analyses_lambda_name      = module.get_client_analyses.function_name
}