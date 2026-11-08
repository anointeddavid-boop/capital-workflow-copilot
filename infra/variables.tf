variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "Server size. t3.medium has 4 GB of memory, enough for the search model."
  type        = string
  default     = "t3.medium"
}
