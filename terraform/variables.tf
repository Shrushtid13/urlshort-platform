variable "region" {
  type    = string
  default = "ap-south-1"
}
variable "cluster_name" {
  type    = string
  default = "urlshort"
}
variable "node_instance_type" {
  type    = string
  default = "t3.medium"
}
variable "node_count" {
  type    = number
  default = 2
}
