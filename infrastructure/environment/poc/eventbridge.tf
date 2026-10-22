module "scraper_trigger" {
  source = "../../modules/eventbridge"

  rule_name           = "scraper-trigger-rule"
  rule_description    = "Triggers the scraper Lambda function every 15th of the month"
  schedule_expression = "cron(0 9 15 * ? *)"

  enable_target        = true
  target_arn           = module.scraper.function_arn
  lambda_function_name = module.scraper.function_name

  tags = merge(local.common_tags, { Name = "scraper-trigger-rule" })
}

module "kb_sync_trigger" {
  source = "../../modules/eventbridge"

  rule_name           = "kb-sync-trigger-rule"
  rule_description    = "Triggers the knowledge base sync Lambda function every 15th of the month"
  schedule_expression = "cron(0 10 15 * ? *)"

  enable_target        = true
  target_arn           = module.kb_sync_lambda.function_arn
  lambda_function_name = module.kb_sync_lambda.function_name

  tags = merge(local.common_tags, { Name = "kb-sync-trigger-rule" })
}

module "market_analysis_report_trigger" {
  source = "../../modules/eventbridge"

  rule_name           = "market-analysis-report-trigger-rule"
  rule_description    = "Triggers the market analysis report Lambda function every 15th of the month, 5 minutes after the KB sync"
  schedule_expression = "cron(5 10 15 * ? *)"

  enable_target        = true
  target_arn           = module.orchestrator.function_arn
  lambda_function_name = module.orchestrator.function_name

  target_input = jsonencode({
    analysis_type = "market_analysis"
  })

  tags = merge(local.common_tags, { Name = "market-analysis-report-trigger-rule" })
}