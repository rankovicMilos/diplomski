terraform {
  backend "s3" {
    bucket = "sra-thesis-tfstate-CHANGE-ME" # create this bucket first; backends cannot use variables
    key    = "poc_environment/terraform.tfstate"
    region = "eu-central-1"
  }
}