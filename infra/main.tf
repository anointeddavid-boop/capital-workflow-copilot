terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    http = {
      source  = "hashicorp/http"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = var.region
}

# My current public IP, so only I can reach the server
data "http" "my_ip" {
  url = "https://checkip.amazonaws.com"
}

locals {
  my_cidr = "${chomp(data.http.my_ip.response_body)}/32"
}

# Latest Ubuntu 22.04 image from Canonical
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

data "aws_vpc" "default" {
  default = true
}

resource "aws_key_pair" "copilot" {
  key_name   = "copilot-key"
  public_key = file(pathexpand("~/.ssh/copilot_key.pub"))
}

resource "aws_security_group" "copilot" {
  name        = "copilot-sg"
  description = "SSH and API access from my IP only"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [local.my_cidr]
  }

  ingress {
    description = "API"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = [local.my_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "copilot" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.copilot.key_name
  vpc_security_group_ids = [aws_security_group.copilot.id]

  root_block_device {
    volume_size = 30
    volume_type = "gp3"
  }

  user_data = <<-EOT
    #!/bin/bash
    apt-get update -y
    apt-get install -y docker.io git curl
    apt-get install -y docker-compose-v2 || (mkdir -p /usr/local/lib/docker/cli-plugins && curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 -o /usr/local/lib/docker/cli-plugins/docker-compose && chmod +x /usr/local/lib/docker/cli-plugins/docker-compose)
    systemctl enable --now docker
    usermod -aG docker ubuntu
  EOT

  tags = {
    Name = "capital-workflow-copilot"
  }
}
