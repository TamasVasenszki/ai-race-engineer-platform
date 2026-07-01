output "cluster_name" {
  description = "EKS cluster name (used by aws eks update-kubeconfig)."
  value       = aws_eks_cluster.main.name
}

output "cluster_arn" {
  description = "EKS cluster ARN (scopes the CD role's eks:DescribeCluster and its access entry)."
  value       = aws_eks_cluster.main.arn
}

output "cluster_endpoint" {
  description = "EKS API server endpoint."
  value       = aws_eks_cluster.main.endpoint
}

output "cluster_ca_certificate" {
  description = "Base64-encoded cluster CA certificate."
  value       = aws_eks_cluster.main.certificate_authority[0].data
}

output "cluster_version" {
  description = "Kubernetes version running on the control plane."
  value       = aws_eks_cluster.main.version
}

output "node_role_arn" {
  description = "IAM role ARN attached to the worker nodes."
  value       = aws_iam_role.nodes.arn
}
