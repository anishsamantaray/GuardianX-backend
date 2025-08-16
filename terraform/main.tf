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

resource "aws_iam_policy" "lambda_s3_policy" {
  name   = "guardianx-lambda-s3-access"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement: [
      {
        Effect = "Allow",
        Action = [
          "s3:PutObject",
          "s3:GetObject"
        ],
        Resource = "${aws_s3_bucket.profile_pics.arn}/*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_s3_attach" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_s3_policy.arn
}


resource "aws_lambda_function" "guardianx" {
  function_name = "guardianx-fastapi"
  package_type  = "Image"
  image_uri     = var.image_uri
  role          = aws_iam_role.lambda_exec.arn
  timeout       = 30

  source_code_hash = filebase64sha256("${path.module}/../.build_id")

   environment {
    variables = merge(
      var.lambda_env_vars,
      {
        ALLY_EMAIL_QUEUE_URL = aws_sqs_queue.ally_email_queue.url
      }
    )
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
  api_key_required = false
}

resource "aws_api_gateway_integration" "lambda_integration" {
  rest_api_id             = aws_api_gateway_rest_api.guardianx_api.id
  resource_id             = aws_api_gateway_resource.proxy.id
  http_method             = aws_api_gateway_method.proxy_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.guardianx.invoke_arn
}

resource "aws_api_gateway_deployment" "deployment" {
  depends_on = [
    aws_api_gateway_integration.lambda_integration
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
  enabled = false
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



resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.guardianx.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.guardianx_api.execution_arn}/*/*"
}

resource "aws_dynamodb_table" "incident" {
  name         = var.incident_table_name
  hash_key     = "incident_id"
  billing_mode = "PAY_PER_REQUEST"

  # existing attribute for your PK
  attribute {
    name = "incident_id"
    type = "S"
  }

  # add this attribute for your GSI
  attribute {
    name = "email"
    type = "S"
  }

  # now define the GSI
  global_secondary_index {
    name               = "email-index"
    hash_key           = "email"
    projection_type    = "ALL"
    # if you switch to PROVISIONED, uncomment these:
    # read_capacity   = 5
    # write_capacity  = 5
  }
}

resource "aws_s3_bucket" "profile_pics" {
  bucket = "${var.project_name}-profile-pics"
  tags   = { Name = "Profile Pictures" }
}

resource "aws_s3_bucket_cors_configuration" "cors" {
  bucket = aws_s3_bucket.profile_pics.id

  cors_rule {
    allowed_methods = ["GET", "PUT"]
    allowed_origins = ["*"]
    allowed_headers = ["*"]
    expose_headers = ["ETag"]
    max_age_seconds = 3000
  }
}

resource "aws_sqs_queue" "ally_email_dlq" {
  name                      = "${var.project_name}-ally-email-dlq"
  message_retention_seconds = 1209600
}

resource "aws_sqs_queue" "ally_email_queue" {
  name                       = "${var.project_name}-ally-email-queue"
  visibility_timeout_seconds = 60
  redrive_policy             = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.ally_email_dlq.arn
    maxReceiveCount     = 5
  })
}

resource "aws_iam_policy" "api_can_send_sqs" {
  name   = "${var.project_name}-api-can-send-sqs"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect   = "Allow",
      Action   = ["sqs:SendMessage"],
      Resource = aws_sqs_queue.ally_email_queue.arn
    }]
  })
}

resource "aws_iam_role_policy_attachment" "attach_api_can_send_sqs" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.api_can_send_sqs.arn
}

data "aws_iam_policy_document" "worker_assume" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ally_worker_role" {
  name               = "${var.project_name}-ally-worker-role"
  assume_role_policy = data.aws_iam_policy_document.worker_assume.json
}

resource "aws_iam_role_policy_attachment" "worker_logs" {
  role       = aws_iam_role.ally_worker_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_policy" "worker_sqs_consume" {
  name   = "${var.project_name}-worker-sqs-consume"
  policy = jsonencode({
    Version   = "2012-10-17",
    Statement = [{
      Effect   = "Allow",
      Action   = [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes",
        "sqs:ChangeMessageVisibility"
      ],
      Resource = aws_sqs_queue.ally_email_queue.arn
    }]
  })
}

resource "aws_iam_role_policy_attachment" "attach_worker_sqs_consume" {
  role       = aws_iam_role.ally_worker_role.name
  policy_arn = aws_iam_policy.worker_sqs_consume.arn
}

resource "aws_lambda_function" "ally_email_worker" {
  function_name = "${var.project_name}-ally-email-worker"
  package_type  = "Image"
  image_uri     = var.image_uri                 # same image you already build/push
  role          = aws_iam_role.ally_worker_role.arn
  timeout       = 30
  memory_size   = 256

  # Use worker handler inside the same image
  image_config {
    command = ["lambda_handlers.ally_email_worker.handler"]
  }
   environment {
    variables = merge(
      var.lambda_env_vars,
      {
        ALLY_EMAIL_QUEUE_URL = aws_sqs_queue.ally_email_queue.url
      }
    )
  }
}

resource "aws_lambda_event_source_mapping" "ally_sqs_trigger" {
  event_source_arn                    = aws_sqs_queue.ally_email_queue.arn
  function_name                       = aws_lambda_function.ally_email_worker.arn
  batch_size                          = 10
  maximum_batching_window_in_seconds  = 2
  enabled                             = true
}