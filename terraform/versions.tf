terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.70" }
  }
  # Uncomment after creating an S3 bucket + DynamoDB table for remote state:
  # backend "s3" {
  #   bucket         = "YOUR-tfstate-bucket"
  #   key            = "urlshort/terraform.tfstate"
  #   region         = "ap-south-1"
  #   dynamodb_table = "tfstate-lock"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.region
  default_tags { tags = { Project = "urlshort-platform", ManagedBy = "terraform" } }
}
