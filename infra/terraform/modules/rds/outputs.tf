output "db_endpoint" {
  description = "RDS PostgreSQL endpoint (host:port)."
  value       = aws_db_instance.main.endpoint
}

output "database_url_secret_arn" {
  description = "Secrets Manager ARN of the DATABASE_URL secret (read by the #23 CSI driver)."
  value       = aws_secretsmanager_secret.database_url.arn
}

output "database_url_secret_name" {
  description = "Secrets Manager name of the DATABASE_URL secret."
  value       = aws_secretsmanager_secret.database_url.name
}
