module "api_gw_log_group" {
  source = "../../modules/cloudwatch_log_groups"

  log_group_name    = "${local.prefix}/api-gateway/poc"
  retention_in_days = 0

  tags = merge(local.common_tags, { Name = "${local.prefix}/api-gateway/poc" })
}