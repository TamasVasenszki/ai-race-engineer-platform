variable "region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "eu-central-1"
}

variable "project_name" {
  description = "Prefix used to name and tag all resources."
  type        = string
  default     = "ai-race-engineer"
}

variable "container_port" {
  description = "Port the backend container listens on."
  type        = number
  default     = 8000
}

variable "image_tag" {
  description = "ECR image tag the ECS task definition starts from. CD updates this per deploy."
  type        = string
  default     = "latest"
}

variable "db_name" {
  description = "PostgreSQL database name."
  type        = string
  default     = "race_engineer"
}

variable "db_username" {
  description = "PostgreSQL master username."
  type        = string
  default     = "race"
}

variable "db_instance_class" {
  description = "RDS instance class."
  type        = string
  default     = "db.t4g.micro"
}

variable "db_allocated_storage" {
  description = "RDS allocated storage in GB."
  type        = number
  default     = 20
}

variable "task_cpu" {
  description = "Fargate task CPU units (256 = 0.25 vCPU)."
  type        = number
  default     = 256
}

variable "task_memory" {
  description = "Fargate task memory in MiB."
  type        = number
  default     = 512
}

variable "desired_count" {
  description = "Number of backend tasks to run."
  type        = number
  default     = 1
}

variable "github_repo" {
  description = "GitHub <owner>/<repo> allowed to assume the CD role via OIDC."
  type        = string
  default     = "TamasVasenszki/ai-race-engineer-platform"
}
