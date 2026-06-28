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

# No Anthropic key secret: prod runs AI_PROVIDER=mock, and Secrets Manager rejects an
# empty secret_string. Add a real secret here when switching to AI_PROVIDER=claude.