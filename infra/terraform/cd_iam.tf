# GitHub Actions OIDC provider + CD role (no long-lived keys).
#
# Phase 4 scope: the role can authenticate to ECR and push the backend image. EKS deploy
# permissions (and a matching EKS access entry) are added in #24 when CD is rewritten to
# deploy via `helm upgrade`. The role is a no-op until the AWS_DEPLOY_ROLE_ARN repo
# variable is set from the github_actions_role_arn output.

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
}

resource "aws_iam_role_policy" "github_cd" {
  name   = "${var.project_name}-github-cd"
  role   = aws_iam_role.github_actions_cd.id
  policy = data.aws_iam_policy_document.github_cd.json
}
