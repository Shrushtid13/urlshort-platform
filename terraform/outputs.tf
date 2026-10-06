output "cluster_name" { value = module.eks.cluster_name }
output "kubeconfig_command" {
  value = "aws eks update-kubeconfig --region ${var.region} --name ${module.eks.cluster_name}"
}
output "github_actions_role_arn" {
  value       = aws_iam_role.gha.arn
  description = "Set as repo variable AWS_ROLE_ARN"
}
output "github_plan_role_arn" {
  value       = aws_iam_role.plan.arn
  description = "The ARN of the IAM role for GitHub Actions to run terraform plan"
}
