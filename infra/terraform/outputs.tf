output "alb_dns_name" {
  description = "Public DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "s3_backup_bucket" {
  description = "Name of the S3 bucket created for database backups"
  value       = aws_s3_bucket.backups.bucket
}

output "s3_backup_bucket_arn" {
  description = "ARN of the S3 backup bucket"
  value       = aws_s3_bucket.backups.arn
}

output "rds_endpoint" {
  description = "Connection endpoint for the RDS PostgreSQL database"
  value       = aws_db_instance.postgres.endpoint
}

output "ecs_cluster_name" {
  description = "Name of the ECS Cluster"
  value       = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  description = "Name of the ECS Service"
  value       = aws_ecs_service.app.name
}
