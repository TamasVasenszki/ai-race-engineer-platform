variable "project_name" {
  description = "Prefix used to name and tag all resources."
  type        = string
}

variable "vpc_id" {
  description = "VPC ID the RDS security group lives in."
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR allowed to reach PostgreSQL."
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for the DB subnet group."
  type        = list(string)
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
