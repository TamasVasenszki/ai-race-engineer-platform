# Optional AI provider API key secrets. Created only when the variable is non-empty.
# mock and ollama providers don't need keys; claude needs ANTHROPIC_API_KEY; openai needs OPENAI_API_KEY.

resource "aws_secretsmanager_secret" "anthropic_api_key" {
  count       = var.anthropic_api_key != "" ? 1 : 0
  name        = "${var.project_name}/anthropic-api-key"
  description = "Anthropic API key for Claude provider."

  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "anthropic_api_key" {
  count         = var.anthropic_api_key != "" ? 1 : 0
  secret_id     = aws_secretsmanager_secret.anthropic_api_key[0].id
  secret_string = var.anthropic_api_key
}

resource "aws_secretsmanager_secret" "openai_api_key" {
  count       = var.openai_api_key != "" ? 1 : 0
  name        = "${var.project_name}/openai-api-key"
  description = "OpenAI API key."

  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "openai_api_key" {
  count         = var.openai_api_key != "" ? 1 : 0
  secret_id     = aws_secretsmanager_secret.openai_api_key[0].id
  secret_string = var.openai_api_key
}
