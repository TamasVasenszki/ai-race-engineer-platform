# Randomly generated DB password — never committed, lives only in state + Secrets Manager.
resource "random_password" "db" {
  length  = 24
  special = false
}

# Full async connection string the backend reads from DATABASE_URL.
locals {
  database_url = "postgresql+asyncpg://${var.db_username}:${random_password.db.result}@${aws_db_instance.postgres.address}:5432/${var.db_name}"
}

resource "aws_secretsmanager_secret" "database_url" {
  name        = "${local.name}/database-url"
  description = "Backend DATABASE_URL (async SQLAlchemy connection string)."

  # Delete immediately on destroy (no recovery window) so re-apply doesn't hit
  # "secret already exists" / "scheduled for deletion".
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "database_url" {
  secret_id     = aws_secretsmanager_secret.database_url.id
  secret_string = local.database_url
}

# Stubbed empty Anthropic key so switching AI_PROVIDER=claude later is just a value update.
resource "aws_secretsmanager_secret" "anthropic_api_key" {
  name        = "${local.name}/anthropic-api-key"
  description = "Anthropic API key (empty until a live Claude key is provisioned)."

  # Delete immediately on destroy (no recovery window) so re-apply doesn't hit
  # "secret already exists" / "scheduled for deletion".
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "anthropic_api_key" {
  secret_id     = aws_secretsmanager_secret.anthropic_api_key.id
  secret_string = ""
}