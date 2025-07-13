resource "aws_s3_bucket" "tf_state" {
  bucket = "guardianx-terraform-state"
  versioning {
    enabled = true
  }
}

resource "aws_dynamodb_table" "tf_locks" {
  name         = "guardianx-terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"
  attribute {
    name = "LockID"
    type = "S"
  }
}