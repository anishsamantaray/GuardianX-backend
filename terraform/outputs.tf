output "api_endpoint" {
  value = "https://${aws_api_gateway_rest_api.guardianx_api.id}.execute-api.${var.aws_region}.amazonaws.com/${aws_api_gateway_stage.prod.stage_name}/"
}

output "profile_pics_bucket" {
  value = aws_s3_bucket.profile_pics.bucket
}