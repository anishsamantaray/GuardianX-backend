provider "aws" {
  region = var.aws_region
}

resource "aws_iam_role" "lambda_exec" {
  name = "guardianx-lambda-exec"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement: [{
      Effect = "Allow",
      Principal = {
        Service = "lambda.amazonaws.com"
      },
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic_exec" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_dynamodb_access" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
}

resource "aws_lambda_function" "guardianx" {
  function_name = "guardianx-fastapi"
  package_type  = "Image"
  image_uri     = var.image_uri
  role          = aws_iam_role.lambda_exec.arn
  timeout       = 30

  source_code_hash = filebase64sha256("${path.module}/../.build_id")

  environment {
    variables = var.lambda_env_vars
  }
}

resource "aws_api_gateway_rest_api" "guardianx_api" {
  name = "guardianx-rest-api"
}

# Catch-all proxy route
resource "aws_api_gateway_resource" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.guardianx_api.id
  parent_id   = aws_api_gateway_rest_api.guardianx_api.root_resource_id
  path_part   = "{proxy+}"
}

resource "aws_api_gateway_method" "proxy_method" {
  rest_api_id   = aws_api_gateway_rest_api.guardianx_api.id
  resource_id   = aws_api_gateway_resource.proxy.id
  http_method   = "ANY"
  authorization = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_integration" "lambda_integration" {
  rest_api_id             = aws_api_gateway_rest_api.guardianx_api.id
  resource_id             = aws_api_gateway_resource.proxy.id
  http_method             = aws_api_gateway_method.proxy_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.guardianx.invoke_arn
}

# Public docs
resource "aws_api_gateway_resource" "docs" {
  rest_api_id = aws_api_gateway_rest_api.guardianx_api.id
  parent_id   = aws_api_gateway_rest_api.guardianx_api.root_resource_id
  path_part   = "docs"
}

resource "aws_api_gateway_method" "docs_method" {
  rest_api_id   = aws_api_gateway_rest_api.guardianx_api.id
  resource_id   = aws_api_gateway_resource.docs.id
  http_method   = "GET"
  authorization = "NONE"
  api_key_required = false
}

resource "aws_api_gateway_integration" "docs_integration" {
  rest_api_id             = aws_api_gateway_rest_api.guardianx_api.id
  resource_id             = aws_api_gateway_resource.docs.id
  http_method             = aws_api_gateway_method.docs_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.guardianx.invoke_arn
}

# openapi.json public route
resource "aws_api_gateway_resource" "openapi_json" {
  rest_api_id = aws_api_gateway_rest_api.guardianx_api.id
  parent_id   = aws_api_gateway_rest_api.guardianx_api.root_resource_id
  path_part   = "openapi.json"
}

resource "aws_api_gateway_method" "openapi_json_method" {
  rest_api_id   = aws_api_gateway_rest_api.guardianx_api.id
  resource_id   = aws_api_gateway_resource.openapi_json.id
  http_method   = "GET"
  authorization = "NONE"
  api_key_required = false
}

resource "aws_api_gateway_integration" "openapi_json_integration" {
  rest_api_id             = aws_api_gateway_rest_api.guardianx_api.id
  resource_id             = aws_api_gateway_resource.openapi_json.id
  http_method             = aws_api_gateway_method.openapi_json_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.guardianx.invoke_arn
}

resource "aws_api_gateway_deployment" "deployment" {
  depends_on = [
    aws_api_gateway_integration.lambda_integration,
    aws_api_gateway_integration.docs_integration,
    aws_api_gateway_integration.openapi_json_integration
  ]
  rest_api_id = aws_api_gateway_rest_api.guardianx_api.id
}

resource "aws_api_gateway_stage" "prod" {
  rest_api_id   = aws_api_gateway_rest_api.guardianx_api.id
  deployment_id = aws_api_gateway_deployment.deployment.id
  stage_name    = "prod"
}

resource "aws_api_gateway_api_key" "guardianx_key" {
  name    = "guardianx-client-key"
  enabled = true
}

resource "aws_api_gateway_usage_plan" "guardianx_plan" {
  name = "guardianx-usage-plan"

  api_stages {
    api_id = aws_api_gateway_rest_api.guardianx_api.id
    stage  = aws_api_gateway_stage.prod.stage_name


  }
  throttle_settings {
      burst_limit = 100
      rate_limit  = 50
    }
}

resource "aws_api_gateway_usage_plan_key" "guardianx_usage_key" {
  key_id        = aws_api_gateway_api_key.guardianx_key.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.guardianx_plan.id
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.guardianx.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.guardianx_api.execution_arn}/*/*"
}
