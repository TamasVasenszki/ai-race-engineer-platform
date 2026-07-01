# EKS backend deploy — runbook (#23)

Deploys the backend to EKS via the custom Helm chart in [`backend/`](./backend), fronted by an
ALB from the AWS Load Balancer Controller, with the `DATABASE_URL` secret delivered by the
Secrets Store CSI driver (AWS provider).

Terraform owns only the AWS resources (cluster, IAM roles, Pod Identity associations). The
community charts and the backend chart are installed with the `helm`/`kubectl` CLIs, ordered
below. #24 (CD) and #25 (Makefile) later automate these steps — this runbook is the manual
reference they codify.

> **Automated lifecycle:** the root `Makefile` codifies this runbook — `make apply` brings the
> whole stack up and `make destroy` tears it down in the correct order (helm uninstall → wait for
> this cluster's ALB to deprovision → `terraform destroy`). The steps below remain the reference.

Chart versions below are pinned; verify/bump them at apply time (`helm search repo <chart> --versions`).

## Prerequisites

- `terraform apply` completed (cluster + IAM roles + Pod Identity associations exist)
- `aws`, `kubectl`, `helm`, `docker` available and AWS creds configured

```sh
cd infra/terraform
export AWS_REGION=$(terraform output -raw region)
export CLUSTER_NAME=$(terraform output -raw cluster_name)
export VPC_ID=$(terraform output -raw vpc_id)
export ECR_URL=$(terraform output -raw ecr_repository_url)
export DB_SECRET_NAME=$(terraform output -raw database_url_secret_name)
aws eks update-kubeconfig --region "$AWS_REGION" --name "$CLUSTER_NAME"
```

## Install order

### 1. Build + push the backend image to ECR

```sh
aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "${ECR_URL%/*}"
docker buildx build --platform linux/amd64 -t "$ECR_URL:latest" ./backend --push
```

### 2. AWS Load Balancer Controller (Helm)

The controller's IAM role is provisioned by Terraform via Pod Identity, so the chart's
ServiceAccount must be named `aws-load-balancer-controller` and NOT create its own IAM binding.

```sh
helm repo add eks https://aws.github.io/eks-charts
helm repo update
# Pin the chart to the 1.13.x line (controller v2.13.x): the vendored lbc-iam-policy.json
# matches that controller version. Newer lines (v2.14+/v3.x) may need IAM actions the policy
# lacks. Bump the policy and this pin together.
helm upgrade --install aws-load-balancer-controller eks/aws-load-balancer-controller \
  --version 1.13.4 \
  --namespace kube-system \
  --set clusterName="$CLUSTER_NAME" \
  --set region="$AWS_REGION" \
  --set vpcId="$VPC_ID" \
  --set serviceAccount.create=true \
  --set serviceAccount.name=aws-load-balancer-controller
kubectl -n kube-system rollout status deployment/aws-load-balancer-controller
```

### 3. Secrets Store CSI driver + AWS provider

Two settings are load-bearing for EKS Pod Identity:
- `syncSecret.enabled=true` — lets the SecretProviderClass sync the mounted value into a native
  k8s Secret (which the backend consumes via `secretKeyRef`).
- `tokenRequests` with audiences `sts.amazonaws.com` + `pods.eks.amazonaws.com` — without these
  the CSIDriver hands the provider no ServiceAccount token and the mount fails with
  `CSI token error: serviceAccount.tokens not provided`. The chart's SecretProviderClass sets
  `usePodIdentity: "true"` to match (values.yaml `aws.usePodIdentity`).

The `tokenRequests[N]` keys must be single-quoted in zsh (the brackets are a glob otherwise).

```sh
helm repo add secrets-store-csi-driver \
  https://kubernetes-sigs.github.io/secrets-store-csi-driver/charts
helm repo update
helm upgrade --install csi-secrets-store \
  secrets-store-csi-driver/secrets-store-csi-driver \
  --version 1.6.0 \
  --namespace kube-system \
  --set syncSecret.enabled=true \
  --set 'tokenRequests[0].audience=sts.amazonaws.com' \
  --set 'tokenRequests[1].audience=pods.eks.amazonaws.com'

# AWS provider (installs the aws-secrets-manager provider daemonset in kube-system)
# NOTE: pulled from main (unpinned) — pin to a release tag as a follow-up.
kubectl apply -f \
  https://raw.githubusercontent.com/aws/secrets-store-csi-driver-provider-aws/main/deployment/aws-provider-installer.yaml
kubectl -n kube-system rollout status daemonset/csi-secrets-store-provider-aws
```

### 4. Backend chart

```sh
helm upgrade --install ai-race-backend infra/k8s/backend \
  --namespace default \
  --set image.repository="$ECR_URL" \
  --set image.tag=latest \
  --set aws.region="$AWS_REGION" \
  --set aws.databaseUrlSecretName="$DB_SECRET_NAME"
```

## Verification (Gate 2)

```sh
kubectl -n default rollout status deployment/ai-race-backend   # 1. Running + Ready
kubectl -n default get secret backend-db                       # 2. CSI sync happened
kubectl -n default describe pod -l app=ai-race-backend         # 3. no "failed to mount secrets store"

ALB=$(kubectl -n default get ingress ai-race-backend \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
curl "http://$ALB/health"                                      # 4. {"status":"ok","ai_provider":"mock"}

# 5. Full CSI -> synced-secret -> RDS round-trip (proves the whole chain, not just DB-free /health).
# laps.session_id is an FK to racing_sessions, and there is no /sessions/ endpoint yet (#28),
# so first seed a session row via the app's own engine inside a pod, then POST a lap with its id.
SESSION_ID=$(kubectl -n default exec -i deploy/ai-race-backend -- python - <<'PY'
import asyncio
from database import AsyncSessionLocal
from models import RacingSession
async def main():
    async with AsyncSessionLocal() as s:
        rs = RacingSession(track="Monza", car="Ferrari 488 Challenge Evo")
        s.add(rs); await s.commit(); await s.refresh(rs)
        print(rs.id)
asyncio.run(main())
PY
)

LAP=$(curl -s -X POST "http://$ALB/laps/" -H 'Content-Type: application/json' \
  -d "{\"session_id\":\"$SESSION_ID\",\"lap_number\":1,\"lap_time_ms\":92345,\"sector1_ms\":30000,\"sector2_ms\":31000,\"sector3_ms\":31345,\"max_speed_kmh\":248.5}")
echo "$LAP"                                                    # expect HTTP 201 body with an id + ai_summary
LAP_ID=$(echo "$LAP" | sed -E 's/.*"id":"([^"]+)".*/\1/')
curl -s "http://$ALB/laps/$LAP_ID"                             # expect 200, same body read back from RDS
```

## Teardown — ORDER MATTERS

The ALB is provisioned by the LBC from the Ingress and is **not** in Terraform state. Running
`terraform destroy` first would orphan it, and the VPC/subnet/ENI destroy would then fail with
`DependencyViolation`. Delete the Ingress (which makes the LBC deprovision the ALB) and wait for
the ALB to actually disappear before `terraform destroy`.

```sh
# 1. Remove the backend -> deletes the Ingress -> LBC deprovisions ALB + target groups + managed SG
helm uninstall ai-race-backend -n default

# 2. Wait until the ALB is really gone
kubectl -n default get ingress                                 # expect: no resources
aws elbv2 describe-load-balancers --region "$AWS_REGION" \
  --query 'LoadBalancers[].LoadBalancerName'                   # expect: []

# 3. Remove the cluster add-ons
kubectl delete -f \
  https://raw.githubusercontent.com/aws/secrets-store-csi-driver-provider-aws/main/deployment/aws-provider-installer.yaml
helm uninstall csi-secrets-store -n kube-system
helm uninstall aws-load-balancer-controller -n kube-system

# 4. Only now destroy the infra
cd infra/terraform && terraform destroy

# 5. Confirm clean
aws eks list-clusters --region "$AWS_REGION"                   # expect: []
aws elbv2 describe-load-balancers --region "$AWS_REGION" --query 'LoadBalancers[].LoadBalancerName'
terraform state list                                           # expect: empty
```
