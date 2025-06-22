variable "aws_region" {
  description = "AWS region"
  default     = "ap-south-1"
}

variable "image_uri" {
  description = "ECR image URI (with tag)"
  type        = string
}
