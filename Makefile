# EKS lifecycle orchestration for the AI Race Engineer backend.
#
# Codifies the manual runbook in infra/k8s/README.md:
#   make apply    bring the whole stack up from nothing (terraform + add-ons + backend chart)
#   make destroy  tear it down cleanly, in the order that avoids a VPC DependencyViolation
#
# apply is auto-approved (demo-friendly, non-destructive). destroy asks for an interactive
# "yes" first (irreversible: cluster + RDS + data); AUTO_APPROVE=1 make destroy skips the prompt.
# Infra-dependent values are read from `terraform output` at runtime, never hardcoded.

SHELL := /bin/bash

TF_DIR     := infra/terraform
CHART      := infra/k8s/backend
CHART_NAME := ai-race-backend
NAMESPACE  := default

# Overridable knobs. IMAGE_TAG=latest is the local bring-up fallback; CD deploys sha tags.
IMAGE_TAG          ?= latest
LBC_CHART_VERSION  ?= 1.13.4
CSI_CHART_VERSION  ?= 1.6.0
# NOTE: pulled from main (unpinned) — pin to a release tag as a follow-up (see infra/k8s/README.md).
CSI_AWS_PROVIDER_URL := https://raw.githubusercontent.com/aws/secrets-store-csi-driver-provider-aws/main/deployment/aws-provider-installer.yaml

TF := terraform -chdir=$(TF_DIR)

.PHONY: help apply kubeconfig push lbc csi deploy url confirm-destroy destroy

help:
	@echo "AI Race Engineer — EKS lifecycle"
	@echo ""
	@echo "  make apply                 Bring the stack up from nothing (terraform apply -auto-approve,"
	@echo "                             then kubeconfig, image push, LBC, CSI driver, backend chart)."
	@echo "  make destroy               Tear down (ordered: helm uninstall -> wait for this cluster's"
	@echo "                             ALB to deprovision -> terraform destroy). Asks 'yes' first."
	@echo "  AUTO_APPROVE=1 make destroy   Same, unattended (skips the confirmation prompt)."
	@echo ""
	@echo "  make push                  Build + push the backend image to ECR (tag IMAGE_TAG=$(IMAGE_TAG))."
	@echo "  make deploy                Helm upgrade the backend chart only (assumes cluster + add-ons up)."
	@echo "  make kubeconfig | lbc | csi | url   Individual steps."

# ---- apply -----------------------------------------------------------------
apply:
	@echo ">> [1/7] terraform apply (auto-approve)"
	$(TF) init -input=false
	$(TF) apply -auto-approve
	@echo ">> [2/7] kubeconfig"
	@$(MAKE) --no-print-directory kubeconfig
	@echo ">> [3/7] build + push image ($(IMAGE_TAG))"
	@$(MAKE) --no-print-directory push
	@echo ">> [4/7] AWS Load Balancer Controller"
	@$(MAKE) --no-print-directory lbc
	@echo ">> [5/7] Secrets Store CSI driver + AWS provider"
	@$(MAKE) --no-print-directory csi
	@echo ">> [6/7] backend chart"
	@$(MAKE) --no-print-directory deploy
	@echo ">> [7/7] ALB address"
	@$(MAKE) --no-print-directory url

kubeconfig:
	aws eks update-kubeconfig \
	  --region $$($(TF) output -raw region) \
	  --name $$($(TF) output -raw cluster_name)

push:
	@REGION=$$($(TF) output -raw region); \
	ECR_URL=$$($(TF) output -raw ecr_repository_url); \
	aws ecr get-login-password --region $$REGION \
	  | docker login --username AWS --password-stdin $${ECR_URL%/*}; \
	docker buildx build --platform linux/amd64 -t $$ECR_URL:$(IMAGE_TAG) ./backend --push

lbc:
	helm repo add eks https://aws.github.io/eks-charts 2>/dev/null || true
	helm repo update eks
	@REGION=$$($(TF) output -raw region); \
	CLUSTER=$$($(TF) output -raw cluster_name); \
	VPC=$$($(TF) output -raw vpc_id); \
	helm upgrade --install aws-load-balancer-controller eks/aws-load-balancer-controller \
	  --version $(LBC_CHART_VERSION) --namespace kube-system \
	  --set clusterName=$$CLUSTER --set region=$$REGION --set vpcId=$$VPC \
	  --set serviceAccount.create=true --set serviceAccount.name=aws-load-balancer-controller
	kubectl -n kube-system rollout status deployment/aws-load-balancer-controller --timeout=180s

csi:
	helm repo add secrets-store-csi-driver \
	  https://kubernetes-sigs.github.io/secrets-store-csi-driver/charts 2>/dev/null || true
	helm repo update secrets-store-csi-driver
	helm upgrade --install csi-secrets-store \
	  secrets-store-csi-driver/secrets-store-csi-driver \
	  --version $(CSI_CHART_VERSION) --namespace kube-system \
	  --set syncSecret.enabled=true \
	  --set 'tokenRequests[0].audience=sts.amazonaws.com' \
	  --set 'tokenRequests[1].audience=pods.eks.amazonaws.com'
	kubectl apply -f $(CSI_AWS_PROVIDER_URL)
	kubectl -n kube-system rollout status daemonset/csi-secrets-store-provider-aws --timeout=180s

deploy:
	@REGION=$$($(TF) output -raw region); \
	ECR_URL=$$($(TF) output -raw ecr_repository_url); \
	SECRET=$$($(TF) output -raw database_url_secret_name); \
	helm upgrade --install $(CHART_NAME) $(CHART) --namespace $(NAMESPACE) \
	  --set image.repository=$$ECR_URL --set image.tag=$(IMAGE_TAG) \
	  --set aws.region=$$REGION --set aws.databaseUrlSecretName=$$SECRET \
	  --wait --timeout 10m

url:
	@ALB=""; \
	for i in $$(seq 1 40); do \
	  ALB=$$(kubectl -n $(NAMESPACE) get ingress $(CHART_NAME) \
	    -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null); \
	  if [ -n "$$ALB" ]; then break; fi; \
	  echo "   waiting for ALB address..."; sleep 15; \
	done; \
	if [ -z "$$ALB" ]; then echo "ALB address not ready (timeout)"; exit 1; fi; \
	echo "   backend: http://$$ALB/health"

# ---- destroy ---------------------------------------------------------------
confirm-destroy:
ifndef AUTO_APPROVE
	@read -r -p "This DESTROYS the cluster, RDS, and all data. Type 'yes' to continue: " ans; \
	if [ "$$ans" != "yes" ]; then echo "aborted"; exit 1; fi
endif

# Single shell block: CLUSTER/REGION are captured before `terraform destroy` wipes the state,
# so the post-destroy cleanliness check can still filter by the cluster tag.
destroy: confirm-destroy
	@set -e; \
	REGION=$$($(TF) output -raw region); \
	CLUSTER=$$($(TF) output -raw cluster_name); \
	echo ">> uninstalling backend chart (deletes the Ingress -> LBC deprovisions the ALB)"; \
	helm uninstall $(CHART_NAME) -n $(NAMESPACE) || true; \
	echo ">> waiting for $$CLUSTER's ALB(s) to be deprovisioned (tag-filtered; shared account)"; \
	for i in $$(seq 1 40); do \
	  N=$$(aws resourcegroupstaggingapi get-resources --region $$REGION \
	        --resource-type-filters elasticloadbalancing:loadbalancer \
	        --tag-filters Key=elbv2.k8s.aws/cluster,Values=$$CLUSTER \
	        --query 'length(ResourceTagMappingList)' --output text 2>/dev/null || echo "?"); \
	  if [ "$$N" = "0" ]; then echo "   ALB(s) gone"; break; fi; \
	  if [ "$$i" -eq 40 ]; then \
	    echo "ERROR: $$CLUSTER ALB(s) still present after timeout; aborting before terraform destroy"; \
	    exit 1; fi; \
	  echo "   $$N ALB(s) still present for $$CLUSTER..."; sleep 15; \
	done; \
	echo ">> removing cluster add-ons"; \
	kubectl delete -f $(CSI_AWS_PROVIDER_URL) --ignore-not-found=true || true; \
	helm uninstall csi-secrets-store -n kube-system || true; \
	helm uninstall aws-load-balancer-controller -n kube-system || true; \
	echo ">> terraform destroy"; \
	$(TF) destroy -auto-approve; \
	echo ">> cleanliness check: $$CLUSTER-tagged ALBs remaining"; \
	LEFT=$$(aws resourcegroupstaggingapi get-resources --region $$REGION \
	         --resource-type-filters elasticloadbalancing:loadbalancer \
	         --tag-filters Key=elbv2.k8s.aws/cluster,Values=$$CLUSTER \
	         --query 'length(ResourceTagMappingList)' --output text 2>/dev/null || echo "?"); \
	echo "   remaining: $$LEFT (expect 0)"; \
	echo ">> destroyed"
