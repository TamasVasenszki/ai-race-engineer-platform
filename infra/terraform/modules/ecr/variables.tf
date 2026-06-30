variable "project_name" {
  description = "Prefix used to name and tag all resources."
  type        = string
}

variable "image_retention_count" {
  description = "Number of most-recent images to keep in the repository."
  type        = number
  default     = 10
}
