terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }

  backend "s3" {
    bucket         = "ai-race-engineer-tf-state"
    key            = "infra/terraform.tfstate"
    region         = "eu-central-1"
    dynamodb_table = "ai-race-engineer-tf-lock"
    encrypt        = true
  }
}
