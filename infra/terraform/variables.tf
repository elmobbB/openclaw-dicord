variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "name" {
  type    = string
  default = "openclaw-bot"
}

variable "instance_type" {
  type    = string
  default = "t3.small"
}

variable "root_volume_gb" {
  type    = number
  default = 30
}

variable "repo_url" {
  type = string
}

variable "app_dir" {
  type    = string
  default = "/opt/openclaw"
}

variable "compose_file" {
  type    = string
  default = "docker-compose.prod.yml"
}

variable "ssm_parameter_name" {
  type    = string
  default = "/openclaw/prod/env"
}

variable "ssh_ingress_cidrs" {
  type    = list(string)
  default = []
}

variable "api_ingress_cidrs" {
  type    = list(string)
  default = []
}

variable "key_pair_name" {
  type    = string
  default = ""
}
