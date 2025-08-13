import boto3
import boto3.session
import base64


#This function is to create a new vpc
def create_vpc(name, client):
    try:
        #check if the vpc already exists
        response = client.describe_vpcs()['Vpcs']
        for vpc in response:
            tags = vpc.get('Tags', [])

            for tag in tags:
                if tag.get('Key') == 'Name' and tag.get('Value') == name:
                    return vpc['VpcId']


        #create a new vpc
        response = client.create_vpc(
        CidrBlock='10.0.0.0/16',
        TagSpecifications=[
        {
            'ResourceType' : 'vpc',
            'Tags': [{
                    'Key': 'Name',
                    'Value': name}]
            }
        ]
    )
        vpc_id = response['Vpc']['VpcId']

        waiter_vpc = client.get_waiter('vpc_available')
        waiter_vpc.wait(VpcIds=[vpc_id])

        print('The vpc has been created successfully')
    
    except Exception as e:
        print(e)

    return vpc_id



#This function to create public subnet
def create_subnet(name, cidr, zone, vpc_id, client):
    try:
        response = client.describe_subnets()['Subnets']
        for subnet in response:
            tags = subnet.get('Tags', [])

            for tag in tags:
                if tag.get('Key') == 'Name' and tag.get('Value') == name:
                    return subnet['SubnetId']
    

        response = client.create_subnet(
            TagSpecifications=[
                {
                    'ResourceType': 'subnet',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': name
                        },
                    ]
                },
            ],
            AvailabilityZone= zone,
            CidrBlock= cidr,
            VpcId= vpc_id 
            )

        subnet_id = response['Subnet']['SubnetId']

        waiter_subnet = client.get_waiter('subnet_available')
        waiter_subnet.wait(SubnetIds=[subnet_id])
        print('The subnet has been created successfully')

        return subnet_id

    
    except Exception as e:
        print(e)



#modifying subnet attribute
def enable_public_ip_on_subnet(subnet_id, client):
    client.modify_subnet_attribute(
    MapPublicIpOnLaunch={'Value': True},
    SubnetId=subnet_id,
)   
    print(f"Enable auto assign public ip for subnet id: {subnet_id}")



#create a internet gateway
def create_internet_gateway(name, client):
    try:
        response = client.describe_internet_gateways()['InternetGateways']
        for igw in response:
            tags = igw.get('Tags', [])

            for tag in tags:
                if tag.get('Key') == 'Name' and tag.get('Value') == name:
                    return igw['InternetGatewayId']


        response = client.create_internet_gateway(
        TagSpecifications=[
            {
                'ResourceType':'internet-gateway',
                'Tags': [
                    {
                        'Key': 'Name',
                        'Value': name
                    },
                ]
            },
        ],
    )   
        igw_id = response['InternetGateway']['InternetGatewayId']
        print('The internet gateway has been created successully')
        return igw_id

    except Exception as e:
        print(e)



#create a security group
def create_sg(name, description, vpc, client):
    response = client.create_security_group(
    Description=description,
    GroupName=name,
    VpcId=vpc,
    TagSpecifications=[
        {
            'ResourceType':'security-group',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': name
                },
            ]
        },
    ],
)   
    sg_id = response['GroupId']
    waiter_sg = client.get_waiter('security_group_exists')
    waiter_sg.wait(GroupIds=[sg_id])

    print('The security group has been created successfully')

    return sg_id



#create a natgateawy
def create_natgateway(name, subnet, client):
    try:
        #create an allocate address
        response = client.allocate_address(Domain='vpc')
        allocate_ip = response['AllocationId']


        #create a natgateway
        response = client.create_nat_gateway(
        AllocationId= allocate_ip,
        SubnetId= subnet,
        TagSpecifications=[
            {
                'ResourceType':'natgateway',
                'Tags': [
                    {
                        'Key': 'Name',
                        'Value': name
                    },
                ]
            },
        ],
    )   
        natgateway_id = response['NatGateway']['NatGatewayId']

        print('creating natgateway......')

        waiter_natgateway = client.get_waiter('nat_gateway_available')
        waiter_natgateway.wait(NatGatewayIds=[natgateway_id])

        print('The natgateway has been created successfully')
        return natgateway_id
    
    except Exception as e:
        print(e)



#create a route_table
def create_route_table(name, vpc_id, client):
    try:
        response = client.create_route_table(
        TagSpecifications=[
         {
                'ResourceType':'route-table',
                'Tags': [
                  {
                      'Key': 'Name',
                      'Value': name
                  },
              ]
         },
     ],
        VpcId=vpc_id)

        print('The route table has been created successfully')
        table_id = response['RouteTable']['RouteTableId']
    
        return table_id
    

    except Exception as e:
        print(e)



#attach an internet gateway to vpc
def attach_igw(vpc, igw, client):
    response = client.attach_internet_gateway(
    InternetGatewayId=igw,
    VpcId=vpc)

    print('The internet gateway has been attached to vpc successfully')
    return response



#create a public route
def create_public_route(client, rt, igw):
    client.create_route(
    RouteTableId= rt,
    DestinationCidrBlock='0.0.0.0/0',
    GatewayId= igw
)



#create a private route
def create_private_route(client, rt, ngw):
    client.create_route(
    RouteTableId= rt,
    DestinationCidrBlock='0.0.0.0/0',
    NatGatewayId= ngw
)   



#associate to route table
def associate_route_table(client, subnet, rt):
    response =client.associate_route_table(
    SubnetId= subnet,
    RouteTableId= rt
)   
    return response



#thie function for reading files
def read_file(file):
    try:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()

            return content
    
    except Exception as e:
        print(e)



#create IAM role
def create_iam_role(name, json_file, client):
    try:
        response = client.list_roles()['Roles']
        for role in response:
            tags = role.get('Tags', [])

            for tag in tags:
                if tag.get('Key') == 'Name' and tag.get('Value') == name:
                    return role['Arn']

        trust_policy= read_file(json_file)

        response = client.create_role(
        RoleName=name,
        AssumeRolePolicyDocument= trust_policy,
        Tags=[
            {
                'Key': 'Name',
                'Value': name
            },
        ]
    )   
        role_name = response['Role']['RoleName']
        return role_name
    
    except Exception as e:
        print(e)



#create an instance profile
def create_instance_profile(name, client):
    response = client.list_instance_profiles()['InstanceProfiles']
    for profile in response:
        if profile['InstanceProfileName'] == name:
            return profile['InstanceProfileName']


    response = client.create_instance_profile(
    InstanceProfileName= name,
    Tags=[
        {
            'Key': 'Name',
            'Value': name
        },
    ]
)   
    name_profile = response['InstanceProfile']['InstanceProfileName']
    return name_profile



#attach role to instance
def attach_role_to_instance(client, profile, role):
    client.add_role_to_instance_profile(
    InstanceProfileName= profile,
    RoleName= role
)




#set inbound traffics from a group
def sg_ingress_group(sg_id, from_p, to_p, protocol, group, description, client):
    client.authorize_security_group_ingress(
    GroupId= sg_id,
    IpPermissions=[
        {
            'FromPort': from_p,
            'IpProtocol': protocol,
            'UserIdGroupPairs': [
                {
                    'GroupId': group,
                    'Description': description,
                },
            ],
            'ToPort': to_p,
        },
    ],
)



#set inbound traffics from a cidr
def sg_ingress_cidr(sg_id, from_p, to_p, protocol, cidr, description, client):
    client.authorize_security_group_ingress(
    GroupId= sg_id,
    IpPermissions=[
        {
            'FromPort': from_p,
            'IpProtocol': protocol,
            'IpRanges': [
                {
                    'CidrIp': cidr,
                    'Description': description,
                },
            ],
            'ToPort': to_p,
        },
    ],
)



#set outbound traffics
def sg_egress_group(sg_id, from_p, to_p, protocol, group, description, client):
    client.authorize_security_group_egress(
    GroupId= sg_id,
    IpPermissions=[
        {
            'FromPort': from_p,
            'IpProtocol': protocol,
            'ToPort': to_p,
            'UserIdGroupPairs': [
                {
                    'GroupId': group,
                    'Description': description
                },
            ],
        },
    ],
)



#set outbound traffics
def sg_egress_cidr(sg_id, from_p, to_p, protocol, cidr, description, client):
    client.authorize_security_group_egress(
    GroupId= sg_id,
    IpPermissions=[
        {
            'FromPort': from_p,
            'IpProtocol': protocol,
            'ToPort': to_p,
            'UserIdGroupPairs': [
                {
                    'CidrIp': cidr,
                    'Description': description
                },
            ],
        },
    ],
)



#create an EC2 instance
def run_instance(image, type, key, sg, subnet, userdata, name, profile, client):
    try:
        response = client.run_instances(
        BlockDeviceMappings=[
          {
                'DeviceName': '/dev/sdh',
                'Ebs': {
                   'VolumeSize': 100,
                   'Encrypted': True
                 },            
             },
         ],
        ImageId= image,
        InstanceType= type,
        KeyName= key,
        MaxCount=1,
        MinCount=1,
        SecurityGroupIds= [sg],
        SubnetId= subnet,
        UserData= userdata,
        IamInstanceProfile={'Name': profile},
        TagSpecifications=[
        {
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value':name,
                },
            ],
        },
    ],
)   
        instance_id = response['Instances'][0]['InstanceId']

        waiter_ec2 = client.get_waiter('instance_running')
        waiter_ec2.wait(InstanceIds= [instance_id])

        print('The EC2 instances has been created successfully')

        return instance_id


    except Exception as e:
        print(e)



#create a target group
def create_target_group(name, vpc_id, client):
    try:
        response_d = client.describe_target_groups()['TargetGroups']
        for target in response_d:
            if target['TargetGroupName'] == name:
                return target['TargetGroupArn']

        response_c = client.create_target_group(
        Name=name,
        Protocol='HTTP',
        Port=80,
        VpcId=vpc_id,
        TargetType='instance',
    )   

        target_arn = response_c['TargetGroups'][0]['TargetGroupArn']
        return target_arn


    except Exception as e:
        print(e)



#register targets
def register_targets(tg_arn, tg_id_port, client):
    client.register_targets(
    TargetGroupArn= tg_arn,
    Targets= tg_id_port

    )



#create a load balancer
def create_load_balancer(name, subnet, sg, client):
    try:
        response = client.create_load_balancer(
        Name= name,
        Subnets= subnet,
        SecurityGroups= sg,
        Scheme='internet-facing'
)

        lb_id = response['LoadBalancers'][0]['LoadBalancerArn']

        print('creating load balancer....')
        waiter_lb = client.get_waiter('load_balancer_available')
        waiter_lb.wait(LoadBalancerArns=[lb_id])
        print('The load balancer has been created successfully')


        return lb_id
    
    except Exception as e:
        print(e)



#create listener
def create_listener(tg_arn, lb_arn, port, client):
    try:
        client.create_listener(
            DefaultActions=[
            {
                'TargetGroupArn': tg_arn,
                'Type': 'forward',
            },
        ],
        LoadBalancerArn= lb_arn,
        Port= port,
        Protocol='HTTP',
)   
        print('The listener has been created successfully')

    except Exception as e:
        print(e)




#create a launch template
def create_launch_template(profile, image, instance_type, subnet, key, userdata, name, sg, client):
    try:
        encoded_userdata = base64.b64encode(userdata.encode('utf-8')).decode('utf-8')

        response = client.create_launch_template(
            LaunchTemplateData={
            'ImageId': image,
            'InstanceType': instance_type,
            'BlockDeviceMappings': [
                {
                'DeviceName': '/dev/sdh',
                'Ebs': {
                   'VolumeSize': 100,
                   'Encrypted': True,
                   }            
                 }
            ],
            'IamInstanceProfile': {'Name': profile},
            'NetworkInterfaces': [
                {
                'DeviceIndex': 0,
                'SubnetId': subnet,
                'Groups': [sg],
                'AssociatePublicIpAddress': True
                }
            ],
            'UserData':encoded_userdata,
            'KeyName':key,
            'TagSpecifications': [
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': name,
                        },
                    ],
                },
            ],
        },
            LaunchTemplateName= name
)


        print('The template has been created successfully')
        return response['LaunchTemplate']['LaunchTemplateId']
    

    except Exception as e:
        print(e)




#create auto scaling
def create_auto_scaling(name, tg_arn, min, max, des, subnet, launch_id, client):
    try:
        response = client.create_auto_scaling_group(
            AutoScalingGroupName= name,
            LaunchTemplate={
                'LaunchTemplateId': launch_id,
            },
            MinSize= min,
            MaxSize= max,
            DesiredCapacity= des,
            VPCZoneIdentifier= subnet,
            TargetGroupARNs=[tg_arn],
)   

        print("The autoscaling has been created successfully")

        
    except Exception as e:
        print(e)




#create the main function
def main():
    #create a session with aws
    #create an object of ec2 service
    try:
        aws_session = boto3.session.Session(profile_name='Jehad_aljamal',region_name='us-east-1')
        client_ec2_obj = aws_session.client(service_name='ec2')
        client_iam_obj = aws_session.client(service_name='iam')
        client_alb_obj = aws_session.client(service_name='elbv2')
        client_autoscaling_obj = aws_session.client(service_name='autoscaling')
        


        #calling the vpc function
        vpc_id = create_vpc('vpc-project',client_ec2_obj)


        #calling the subnet function 4 times
        public_subnet1= create_subnet('public_subnet1','10.0.10.0/24','us-east-1a',vpc_id,client_ec2_obj)
        public_subnet2= create_subnet('public_subnet2','10.0.20.0/24','us-east-1b',vpc_id,client_ec2_obj)
        private_subnet1= create_subnet('private_subnet1','10.0.100.0/24','us-east-1a',vpc_id,client_ec2_obj)
        private_subnet2= create_subnet('private_subnet2','10.0.200.0/24','us-east-1b',vpc_id,client_ec2_obj)



        #enable auto-assign public ip to the public subnets
        enable_public_ip_on_subnet(public_subnet1, client_ec2_obj)
        enable_public_ip_on_subnet(public_subnet2, client_ec2_obj)


        #calling the internet gateway and natgateway functions
        igw_id = create_internet_gateway('igw-project', client_ec2_obj)


        #attached igw to the project vpc
        igw_attached = attach_igw(vpc_id, igw_id, client_ec2_obj)


        #create a public route table and 2 private route tables
        public_rt1 = create_route_table('public_RT', vpc_id, client_ec2_obj)
        private_rt1 = create_route_table('private_RT1', vpc_id, client_ec2_obj)
        private_rt2 = create_route_table('private_RT2', vpc_id, client_ec2_obj)

        
        #create a natgateway
        ngw_id = create_natgateway('ngw-project', public_subnet1, client_ec2_obj)


        #attach routs to the route tables
        create_public_route(client_ec2_obj, public_rt1, igw_id)
        create_private_route(client_ec2_obj, private_rt1, ngw_id)
        create_private_route(client_ec2_obj, private_rt2, ngw_id)


        #associate subnets to route tables
        associate_route_table(client_ec2_obj, public_subnet1, public_rt1)
        associate_route_table(client_ec2_obj, public_subnet2, public_rt1)
        associate_route_table(client_ec2_obj, private_subnet1, private_rt1)
        associate_route_table(client_ec2_obj, private_subnet2, private_rt2)


        print('The vpc infrastructure is ready to use')


        
        #create role and instance profile, then attach role to the profile
        iam_role = create_iam_role('ssm-project', 'ssm.json', client_iam_obj)
        print('Iam role has been created successfully')

        instance_profile = create_instance_profile('ssm-role', client_iam_obj)
        print('Iam role has been created successfully')

        attach_role_to_instance(client_iam_obj, instance_profile, iam_role)
        print('The role has been attached to instance profile successfully')



        #create a security group
        sg_id = create_sg('webSG','This is to allow to access private instances',vpc_id,client_ec2_obj)

        sg_ingress_cidr(sg_id, 22, 22, 'tcp', '0.0.0.0/0','allow ssh connection',client_ec2_obj)
        sg_ingress_cidr(sg_id, 80, 80, 'tcp', '0.0.0.0/0','allow web access',client_ec2_obj)
        sg_ingress_cidr(sg_id, 443, 443, 'tcp', '0.0.0.0/0','allow secured web access',client_ec2_obj)




        #create 2 instances
        web_server1 = run_instance('ami-0de716d6197524dd9', 't2.micro', 'Bash-key', sg_id, private_subnet1, read_file('userdata1.sh'), 'webserver1', instance_profile, client_ec2_obj)
        web_server2 = run_instance('ami-0de716d6197524dd9', 't2.micro', 'Bash-key', sg_id, private_subnet2, read_file('userdata2.sh'), 'webserver2', instance_profile, client_ec2_obj)



        #create a target group
        tg_arn = create_target_group('webTG', vpc_id, client_alb_obj)
        print('creating target group .....')



        #register targets
        register_tg = register_targets(tg_arn, [{'Id':web_server1,'Port':80},{'Id':web_server2,'Port':80}], client_alb_obj)
        print('registering targets .....')



        
        #create a SG for the load balancer
        albsg_id = create_sg('ALBSG', 'This albsg security group allow only the port 80', vpc_id, client_ec2_obj) 
        sg_ingress_cidr(albsg_id, 80, 80, 'tcp', '0.0.0.0/0', 'allow 80 port', client_ec2_obj)        
        sg_egress_group(albsg_id, 80, 80, 'tcp', sg_id, 'allow 80 port', client_ec2_obj)



        #modifying inbound traffics
        sg_ingress_group(sg_id, 22, 22, 'tcp', albsg_id,'allow ssh connection',client_ec2_obj)
        sg_ingress_group(sg_id, 80, 80, 'tcp', albsg_id,'allow web access',client_ec2_obj)
        sg_ingress_group(sg_id, 443, 443, 'tcp', albsg_id,'allow secured web access',client_ec2_obj)
        


        #create load balancer
        alb_arn = create_load_balancer('webALB', [public_subnet1,public_subnet2], [albsg_id], client_alb_obj)
        
        #create listener
        listener1 = create_listener(tg_arn, alb_arn, 80, client_alb_obj)


        
        
        #creating launch configuration
        template1_id = create_launch_template(instance_profile, 'ami-0de716d6197524dd9', 't2.micro', private_subnet1, 'Bash-key', read_file('userdata.sh'), 'template1', sg_id, client_ec2_obj)
        
        #create autoscaling
        autoscaling = create_auto_scaling('autoscaling-project', tg_arn, 1, 3, 2, private_subnet1, template1_id, client_autoscaling_obj)

        #the project has done 
        print('The project has done successfully.')



    except Exception as e:
        print(e)


if __name__ == '__main__':
    print('Running the script')
    main()