# AWS Infrastructure Automation with Boto3

This repository contains Python scripts that automate AWS infrastructure setup using **Boto3**.  
The scripts cover VPC creation, subnets, route tables, Internet/NAT Gateways, security groups, EC2 instances, IAM roles, load balancers, target groups, and auto scaling configuration.

## Features
- Create and configure VPC, public & private subnets
- Setup routing, Internet Gateway, and NAT Gateway
- Create EC2 instances with IAM roles
- Configure Target Groups and Application Load Balancer
- Setup Auto Scaling groups and launch templates

## Prerequisites
- Python 3.9+
- AWS CLI configured with a profile
- Boto3 installed:  
  ```bash
  pip install boto3
