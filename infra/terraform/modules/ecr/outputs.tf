output "repository_url" {
  description = "ECR repository URL for the backend image."
  value       = aws_ecr_repository.backend.repository_url
}

output "repository_arn" {
  description = "ECR repository ARN (scoped target for the CD push policy)."
  value       = aws_ecr_repository.backend.arn
}

output "repository_name" {
  description = "ECR repository name."
  value       = aws_ecr_repository.backend.name
}
