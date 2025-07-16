terraform {
  backend "s3" {
    bucket         = "guardianx-terraform-state"
    key            = "lambda/terraform.tfstate"
    region         = "ap-south-1"
    dynamodb_table = "guardianx-terraform-locks"
    encrypt        = true
  }
}
