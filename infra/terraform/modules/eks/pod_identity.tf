# Pod Identity associations.
#
# #22 scope is the EBS CSI driver only. The AWS Load Balancer Controller role and the
# backend secret-reader role are added in #23 alongside their workloads.

# The namespace + service account each association binds to. These are a contract with the
# backend Helm chart (infra/k8s/backend): if the association's namespace/SA and the chart's
# values ever diverge, Pod Identity silently grants nothing and the secret mount fails with
# no obvious error. Keep both sides in sync.
locals {
  backend_namespace       = "default"
  backend_service_account = "ai-race-backend"
  lbc_service_account     = "aws-load-balancer-controller" # kube-system; matches the LBC chart default
}

# Trust policy shared by every Pod Identity role: the EKS Pod Identity service assumes
# the role on behalf of a pod and tags the session.
data "aws_iam_policy_document" "pod_identity_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole", "sts:TagSession"]

    principals {
      type        = "Service"
      identifiers = ["pods.eks.amazonaws.com"]
    }
  }
}

# --- EBS CSI driver --------------------------------------------------------
resource "aws_iam_role" "ebs_csi" {
  name               = "${var.project_name}-ebs-csi-role"
  assume_role_policy = data.aws_iam_policy_document.pod_identity_assume.json
}

resource "aws_iam_role_policy_attachment" "ebs_csi" {
  role       = aws_iam_role.ebs_csi.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
}

resource "aws_eks_pod_identity_association" "ebs_csi" {
  cluster_name    = aws_eks_cluster.main.name
  namespace       = "kube-system"
  service_account = "ebs-csi-controller-sa"
  role_arn        = aws_iam_role.ebs_csi.arn
}

# --- AWS Load Balancer Controller ------------------------------------------
# The controller provisions ALBs from Ingress objects. The IAM policy is the upstream LBC
# policy vendored from the EKS Corp Platform reference (lbc-iam-policy.json).
resource "aws_iam_role" "lbc" {
  name               = "${var.project_name}-lbc-role"
  assume_role_policy = data.aws_iam_policy_document.pod_identity_assume.json
}

resource "aws_iam_policy" "lbc" {
  name   = "${var.project_name}-lbc-policy"
  policy = file("${path.module}/lbc-iam-policy.json")
}

resource "aws_iam_role_policy_attachment" "lbc" {
  role       = aws_iam_role.lbc.name
  policy_arn = aws_iam_policy.lbc.arn
}

resource "aws_eks_pod_identity_association" "lbc" {
  cluster_name    = aws_eks_cluster.main.name
  namespace       = "kube-system"
  service_account = local.lbc_service_account
  role_arn        = aws_iam_role.lbc.arn
}

# --- Backend secret-reader -------------------------------------------------
# The backend pod reads the DATABASE_URL secret via the Secrets Store CSI driver. Least
# privilege: read-only, scoped to that one secret ARN.
resource "aws_iam_role" "backend" {
  name               = "${var.project_name}-backend-secret-role"
  assume_role_policy = data.aws_iam_policy_document.pod_identity_assume.json
}

data "aws_iam_policy_document" "backend_secret" {
  statement {
    effect    = "Allow"
    actions   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
    resources = compact([
      var.database_url_secret_arn,
      var.anthropic_api_key_secret_arn,
      var.openai_api_key_secret_arn,
    ])
  }
}

resource "aws_iam_role_policy" "backend_secret" {
  name   = "${var.project_name}-backend-secret"
  role   = aws_iam_role.backend.id
  policy = data.aws_iam_policy_document.backend_secret.json
}

resource "aws_eks_pod_identity_association" "backend" {
  cluster_name    = aws_eks_cluster.main.name
  namespace       = local.backend_namespace
  service_account = local.backend_service_account
  role_arn        = aws_iam_role.backend.arn
}
