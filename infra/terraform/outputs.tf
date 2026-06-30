output "region" {
  description = "AWS region (used by aws eks update-kubeconfig)."
  value       = var.region
}

output "cluster_name" {
  description = "EKS cluster name: aws eks update-kubeconfig --region <region> --name <this>."
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "EKS API server endpoint."
  value       = module.eks.cluster_endpoint
}

output "cluster_version" {
  description = "Kubernetes version running on the control plane."
  value       = module.eks.cluster_version
}

output "ecr_repository_url" {
  description = "ECR repository URL for the backend image."
  value       = module.ecr.repository_url
}

output "database_url_secret_arn" {
  description = "Secrets Manager ARN of the DATABASE_URL secret (read by the #23 CSI driver)."
  value       = module.rds.database_url_secret_arn
}

output "github_actions_role_arn" {
  description = "Role ARN the CD workflow assumes via OIDC (set as the AWS_DEPLOY_ROLE_ARN repo variable)."
  value       = aws_iam_role.github_actions_cd.arn
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint."
  value       = module.rds.db_endpoint
  sensitive   = true
}
