terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}

resource "aws_security_group" "openclaw" {
  name        = "${var.name}-sg"
  description = "OpenClaw bot EC2 security group"
  vpc_id      = data.aws_vpc.default.id

  dynamic "ingress" {
    for_each = var.ssh_ingress_cidrs
    content {
      description = "SSH"
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      cidr_blocks = [ingress.value]
    }
  }

  dynamic "ingress" {
    for_each = var.api_ingress_cidrs
    content {
      description = "API (optional)"
      from_port   = 8000
      to_port     = 8000
      protocol    = "tcp"
      cidr_blocks = [ingress.value]
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

data "aws_iam_policy_document" "assume_ec2" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "openclaw" {
  name               = "${var.name}-role"
  assume_role_policy = data.aws_iam_policy_document.assume_ec2.json
}

resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.openclaw.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

data "aws_iam_policy_document" "ssm_param" {
  statement {
    actions = [
      "ssm:GetParameter",
      "ssm:GetParameters",
    ]
    resources = [
      "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter${var.ssm_parameter_name}"
    ]
  }

  statement {
    actions = ["kms:Decrypt"]
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["ssm.${var.aws_region}.amazonaws.com"]
    }
  }
}

data "aws_caller_identity" "current" {}

resource "aws_iam_policy" "ssm_param" {
  name   = "${var.name}-ssm-param"
  policy = data.aws_iam_policy_document.ssm_param.json
}

resource "aws_iam_role_policy_attachment" "ssm_param" {
  role       = aws_iam_role.openclaw.name
  policy_arn = aws_iam_policy.ssm_param.arn
}

resource "aws_iam_instance_profile" "openclaw" {
  name = "${var.name}-profile"
  role = aws_iam_role.openclaw.name
}

resource "aws_instance" "openclaw" {
  ami                         = data.aws_ami.al2023.id
  instance_type               = var.instance_type
  subnet_id                   = data.aws_subnets.default.ids[0]
  vpc_security_group_ids      = [aws_security_group.openclaw.id]
  iam_instance_profile        = aws_iam_instance_profile.openclaw.name
  associate_public_ip_address = true
  key_name                    = var.key_pair_name != "" ? var.key_pair_name : null

  root_block_device {
    volume_size = var.root_volume_gb
  }

  user_data = templatefile("${path.module}/user_data.sh", {
    repo_url            = var.repo_url
    app_dir             = var.app_dir
    compose_file        = var.compose_file
    ssm_parameter_name  = var.ssm_parameter_name
    aws_region          = var.aws_region
  })

  tags = {
    Name = var.name
  }
}
