# One-time bootstrap for the S3 + DynamoDB remote state backend.
#
# Run this BEFORE switching the main config's backend from local to S3:
#   cd infra/terraform/bootstrap
#   terraform init && terraform apply
#
# This config uses local state on purpose — the bucket that stores state
# cannot itself be managed by the config that uses it as a backend.

terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

variable "region" {
  description = "AWS region (must match the main config)."
  type        = string
  default     = "eu-central-1"
}

variable "project_name" {
  description = "Prefix for the bucket and table names."
  type        = string
  default     = "ai-race-engineer"
}

# --- S3 bucket for state ---------------------------------------------------
resource "aws_s3_bucket" "tfstate" {
  bucket = "${var.project_name}-tf-state"

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "tfstate" {
  bucket                  = aws_s3_bucket.tfstate.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# --- DynamoDB table for state locking --------------------------------------
resource "aws_dynamodb_table" "tflock" {
  name         = "${var.project_name}-tf-lock"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }
}

# --- Outputs ---------------------------------------------------------------
output "bucket" {
  description = "S3 bucket name — use as the backend.s3.bucket value."
  value       = aws_s3_bucket.tfstate.id
}

output "dynamodb_table" {
  description = "DynamoDB table name — use as the backend.s3.dynamodb_table value."
  value       = aws_dynamodb_table.tflock.name
}
