variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment (e.g. dev, staging, prod)"
  type        = string
  default     = "production"
}

variable "app_name" {
  description = "Application name prefix"
  type        = string
  default     = "ecommerce-api"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.11.0/24"]
}

variable "container_image" {
  description = "Docker image repository and tag (e.g. ghcr.io/<org>/ecommerce-api:latest)"
  type        = string
  default     = "ghcr.io/your-org/ecommerce-api:latest"
}

variable "container_port" {
  description = "Port exposed by the Docker container"
  type        = number
  default     = 8000
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "ecomdb"
}

variable "db_username" {
  description = "PostgreSQL admin username"
  type        = string
  default     = "ecom"
}

variable "db_password" {
  description = "PostgreSQL admin password (keep secret)"
  type        = string
  sensitive   = true
  default     = "change-me-strong-rds-password"
}

variable "api_key_admin" {
  description = "Admin API key for protected routes"
  type        = string
  sensitive   = true
  default     = "change-me-admin-key"
}
