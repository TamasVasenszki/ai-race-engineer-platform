# Phase 4 EKS platform — modular wiring.
#
#   vpc_network → ecr → eks → rds
#
# Per-concern modules live in ./modules. Provider, versions, outputs, and the GitHub
# OIDC CD role are in their own root files (providers.tf, versions.tf, outputs.tf, cd_iam.tf).

module "vpc" {
  source = "./modules/vpc_network"

  project_name = var.project_name
  vpc_cidr     = var.vpc_cidr
}

module "ecr" {
  source = "./modules/ecr"

  project_name = var.project_name
}

module "eks" {
  source = "./modules/eks"

  project_name            = var.project_name
  private_subnet_ids      = module.vpc.private_subnet_ids
  cluster_version         = var.cluster_version
  node_instance_types     = var.node_instance_types
  node_desired_size       = var.node_desired_size
  node_min_size           = var.node_min_size
  node_max_size           = var.node_max_size
  database_url_secret_arn = module.rds.database_url_secret_arn
}

module "rds" {
  source = "./modules/rds"

  project_name       = var.project_name
  vpc_id             = module.vpc.vpc_id
  vpc_cidr           = module.vpc.vpc_cidr
  private_subnet_ids = module.vpc.private_subnet_ids
  db_name            = var.db_name
  db_username        = var.db_username
  db_instance_class  = var.db_instance_class
}
