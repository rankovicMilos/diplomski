data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
    # Lambda integration ARNs are filled in from the function names and the account
    openapi_spec = templatefile("${path.module}/specs/openapi.yaml", {
        region                               = data.aws_region.current.region
        account_id                           = data.aws_caller_identity.current.account_id
        trigger_upload_lambda_name           = var.trigger_upload_lambda_name
        orchestrator_lambda_name             = var.orchestrator_lambda_name
        get_analyses_lambda_name             = var.get_analyses_lambda_name
        get_analyses_by_category_lambda_name = var.get_analyses_by_category_lambda_name
        get_client_analyses_lambda_name      = var.get_client_analyses_lambda_name
    })
}

resource "aws_api_gateway_rest_api" "rest_api" {
    name = var.rest_api_name

    body = local.openapi_spec

    endpoint_configuration {
      types = ["REGIONAL"]
    }

    tags = {
      Name = var.rest_api_name
      Environment = "poc"
      ManagedBy = "terraform"
    }

    lifecycle {
      ignore_changes = [ 
        body
      ]
    }
}

resource "aws_api_gateway_deployment" "api_deployment" {
    rest_api_id = aws_api_gateway_rest_api.rest_api.id

    depends_on = [
      aws_api_gateway_rest_api.rest_api
    ]
}

resource "aws_api_gateway_stage" "api_stage" {
    stage_name    = var.api_stage_name
    rest_api_id   = aws_api_gateway_rest_api.rest_api.id
    deployment_id = aws_api_gateway_deployment.api_deployment.id

    access_log_settings {
      destination_arn = var.log_group_arn
      format          = "{\"requestId\":\"$context.requestId\",\"ip\":\"$context.identity.sourceIp\",\"caller\":\"$context.identity.caller\",\"user\":\"$context.identity.user\",\"requestTime\":\"$context.requestTime\",\"httpMethod\":\"$context.httpMethod\",\"resourcePath\":\"$context.resourcePath\",\"status\":\"$context.status\",\"protocol\":\"$context.protocol\",\"responseLength\":\"$context.responseLength\"}"
    }

    xray_tracing_enabled = true

    lifecycle {
      ignore_changes = [ 
        deployment_id
      ]
    }

    tags = {
      Name = "${var.rest_api_name}-stage"
      Environment = "poc"
      ManagedBy = "terraform"
    }
}

resource "aws_api_gateway_account" "api_gateway_account" {
    cloudwatch_role_arn = var.api_gw_cloudwatch_role_arn
}

resource "aws_lambda_permission" "trigger_upload_lambda_invoke_permission" {
    statement_id  = "AllowAPIGatewayInvoke"
    action        = "lambda:InvokeFunction"
    function_name = var.trigger_upload_lambda_name
    principal     = "apigateway.amazonaws.com"

    source_arn = "${aws_api_gateway_rest_api.rest_api.execution_arn}/*/*"

    depends_on = [
      aws_api_gateway_rest_api.rest_api
    ] 
}

resource "aws_lambda_permission" "orchestrator_lambda_invoke_permission" {
    statement_id  = "AllowAPIGatewayInvokeOrchestrator"
    action        = "lambda:InvokeFunction"
    function_name = var.orchestrator_lambda_name
    principal     = "apigateway.amazonaws.com"

    source_arn = "${aws_api_gateway_rest_api.rest_api.execution_arn}/*/*"

    depends_on = [
      aws_api_gateway_rest_api.rest_api
    ]
}

resource "aws_lambda_permission" "get_analyses_lambda_invoke_permission" {
    statement_id  = "AllowAPIGatewayInvokeGetAnalyses"
    action        = "lambda:InvokeFunction"
    function_name = var.get_analyses_lambda_name
    principal     = "apigateway.amazonaws.com"

    source_arn = "${aws_api_gateway_rest_api.rest_api.execution_arn}/*/*"

    depends_on = [
      aws_api_gateway_rest_api.rest_api
    ]
}

resource "aws_lambda_permission" "get_analyses_by_category_lambda_invoke_permission" {
    statement_id  = "AllowAPIGatewayInvokeGetAnalysesByCategory"
    action        = "lambda:InvokeFunction"
    function_name = var.get_analyses_by_category_lambda_name
    principal     = "apigateway.amazonaws.com"

    source_arn = "${aws_api_gateway_rest_api.rest_api.execution_arn}/*/*"

    depends_on = [
      aws_api_gateway_rest_api.rest_api
    ]
}

resource "aws_lambda_permission" "get-client-analyses-lambda-invoke-permission" {
    statement_id  = "AllowAPIGatewayInvokeGetClientAnalyses"
    action        = "lambda:InvokeFunction"
    function_name = var.get_client_analyses_lambda_name
    principal     = "apigateway.amazonaws.com"

    source_arn = "${aws_api_gateway_rest_api.rest_api.execution_arn}/*/*"

    depends_on = [
      aws_api_gateway_rest_api.rest_api
    ]
}