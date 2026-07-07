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

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.0.0.0/16"
}

# --- EKS -------------------------------------------------------------------
variable "cluster_version" {
  description = "Kubernetes version for the EKS control plane. Override if unavailable at apply time."
  type        = string
  default     = "1.36"
}

variable "node_instance_types" {
  description = "Instance types for the managed node group."
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_desired_size" {
  # This root default is the value passed to the eks module (main.tf), so it is the effective one
  # — the module's own default is shadowed by the explicit argument. 3 fits the observability stack
  # (kube-prometheus-stack + Loki + Promtail) alongside the backend + LBC + CSI.
  description = "Desired number of worker nodes."
  type        = number
  default     = 3
}

variable "node_min_size" {
  description = "Minimum number of worker nodes."
  type        = number
  default     = 2
}

variable "node_max_size" {
  description = "Maximum number of worker nodes."
  type        = number
  default     = 4
}

# --- Database --------------------------------------------------------------
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

# --- CD --------------------------------------------------------------------
variable "github_repo" {
  description = "GitHub <owner>/<repo> allowed to assume the CD role via OIDC."
  type        = string
  default     = "TamasVasenszki/ai-race-engineer-platform"
}
