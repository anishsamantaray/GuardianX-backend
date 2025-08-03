variable "aws_region" {
  description = "AWS region"
  default     = "ap-south-1"
}

variable "image_uri" {
  description = "ECR image URI (with tag)"
  type        = string
}

variable "lambda_env_vars" {
  description = "Environment variables for the Lambda container"
  type        = map(string)
}

variable "incident_table_name" {
  type        = string
  description = "DynamoDB table name for incidents"
}

variable "project_name" {
  description = "The name of the project used for resource naming"
  type        = string
}