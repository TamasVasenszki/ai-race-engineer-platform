# GitHub Actions OIDC provider + CD role (no long-lived keys).
#
# The role authenticates to ECR (push the backend image) and to EKS (deploy via `helm upgrade`):
# an EKS access entry + AmazonEKSClusterAdminPolicy association give it the Kubernetes RBAC the
# chart needs (incl. the SecretProviderClass CRD, which no narrower AWS-managed policy covers).
# The security boundary is the OIDC trust below — assumable only from refs/heads/main. The role
# is a no-op until the AWS_DEPLOY_ROLE_ARN repo variable is set from the github_actions_role_arn
# output.

data "tls_certificate" "github" {
  url = "https://token.actions.githubusercontent.com/.well-known/openid-configuration"
}

resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.github.certificates[0].sha1_fingerprint]
}

data "aws_iam_policy_document" "github_assume" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_repo}:ref:refs/heads/main"]
    }
  }
}

resource "aws_iam_role" "github_actions_cd" {
  name               = "${var.project_name}-github-cd"
  assume_role_policy = data.aws_iam_policy_document.github_assume.json
}

data "aws_iam_policy_document" "github_cd" {
  # ECR auth token is account-wide (no resource scoping possible).
  statement {
    sid       = "EcrAuth"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  # Push/pull on the backend repository only.
  statement {
    sid = "EcrPush"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:CompleteLayerUpload",
      "ecr:InitiateLayerUpload",
      "ecr:PutImage",
      "ecr:UploadLayerPart",
      "ecr:BatchGetImage",
      "ecr:GetDownloadUrlForLayer",
    ]
    resources = [module.ecr.repository_arn]
  }

  # Required by `aws eks update-kubeconfig`; the Kubernetes-level permissions come from the
  # access entry below, not from IAM.
  statement {
    sid       = "EksDescribe"
    actions   = ["eks:DescribeCluster"]
    resources = [module.eks.cluster_arn]
  }
}

resource "aws_iam_role_policy" "github_cd" {
  name   = "${var.project_name}-github-cd"
  role   = aws_iam_role.github_actions_cd.id
  policy = data.aws_iam_policy_document.github_cd.json
}

# EKS access entry: maps the CD IAM role to cluster-admin Kubernetes RBAC so `helm upgrade` can
# manage the full chart (Deployment/Service/Ingress/ServiceAccount + the SecretProviderClass CRD).
resource "aws_eks_access_entry" "github_cd" {
  cluster_name  = module.eks.cluster_name
  principal_arn = aws_iam_role.github_actions_cd.arn
  type          = "STANDARD"
}

resource "aws_eks_access_policy_association" "github_cd" {
  cluster_name  = module.eks.cluster_name
  principal_arn = aws_iam_role.github_actions_cd.arn
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"

  access_scope {
    type = "cluster"
  }

  depends_on = [aws_eks_access_entry.github_cd]
}
