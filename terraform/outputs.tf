output "api_endpoint" {
  value = "https://${aws_api_gateway_rest_api.guardianx_api.id}.execute-api.${var.aws_region}.amazonaws.com/${aws_api_gateway_deployment.deployment.stage_name}/"
}
