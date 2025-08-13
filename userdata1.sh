#!bin/bash
yum update -y
yum install httpd -y
systemctl start httpd
systemctl enable httpd
echo "This is server ***1*** in AWS region US-EAST-1 in AZ US-EAST-1A" > /var/www/html/index.html