terraform {
  required_version = ">= 1.0"

  cloud {
    organization = "Nuagique"

    workspaces {
      name = "mgl842"
    }
  }

  required_providers {
    aws = {
      source = "hashicorp/aws"
      version = "5.43.0"
    }
  }
}


provider "aws" {
  region = "us-east-1"
}