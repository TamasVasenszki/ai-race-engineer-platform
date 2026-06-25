output "alb_dns_name" {
  description = "Public DNS name of the backend ALB."
  value       = aws_lb.main.dns_name
}

output "ecr_repository_url" {
  description = "ECR repository URL for the backend image."
  value       = aws_ecr_repository.backend.repository_url
}

output "ecs_cluster_name" {
  description = "ECS cluster name (set in cd.yml ECS_CLUSTER)."
  value       = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  description = "ECS service name (set in cd.yml ECS_SERVICE)."
  value       = aws_ecs_service.backend.name
}

output "container_name" {
  description = "Container name in the task definition (set in cd.yml CONTAINER_NAME)."
  value       = local.container_name
}

output "task_definition_family" {
  description = "Task definition family (used by cd.yml to fetch the current revision)."
  value       = aws_ecs_task_definition.backend.family
}

output "github_actions_role_arn" {
  description = "Role ARN the CD workflow assumes via OIDC (set as the AWS_DEPLOY_ROLE_ARN repo variable)."
  value       = aws_iam_role.github_actions_cd.arn
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint."
  value       = aws_db_instance.postgres.endpoint
  sensitive   = true
}
