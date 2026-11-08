output "public_ip" {
  value = aws_instance.copilot.public_ip
}

output "ssh_command" {
  value = "ssh -i ~/.ssh/copilot_key ubuntu@${aws_instance.copilot.public_ip}"
}
