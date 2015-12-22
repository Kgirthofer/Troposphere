#!/usr/bin/env python

import os
import sys

from troposphere import GetAtt, GetAZs, Join, Output, Parameter, Ref, Select, FindInMap, Base64
import troposphere.cloudformation as cf
import troposphere.ec2 as ec2
import troposphere.iam as iam

from base import CloudformationAbstractBaseClass
from constants import *


class NATStack(CloudformationAbstractBaseClass):

    def __init__(self):
        # super(NATStack, self).__init__()
        self.template.add_description("Template which creates two NATs, modifies route tables and enables HA NAT failover")

        # various definitions and constants at the top
        self.add_parameters()
        self.add_mappings()

        self.add_nat_instance_role()
        self.add_nat_sg()

        self.add_nat_instances()

        self.allocate_eips()
        self.add_routes()


        # outputs that might be of interest
        self.add_outputs()


    def add_parameters(self):

        """ Implements the abstract method and defines a number of parameters the
            calling process or GUI must supply """

        super(NATStack,self).add_default_parameters()

        self.keyname_param = self.template.add_parameter(Parameter(
            "KeyName",
            Description=KEYNAME_MSG,
            Type="AWS::EC2::KeyPair::KeyName",
            MinLength="1",
            AllowedPattern=VALID_KEYNAME_REGEX,
            ConstraintDescription=INVALID_KEYNAME_MSG,
            Default=""
        ))
        self.vpc_id = self.template.add_parameter(Parameter(
            "VpcId",
            Description="The ID of the existing Virtual Private Cloud (VPC)",
            Type="AWS::EC2::VPC::Id",
            MinLength="1",
            AllowedPattern=VALID_VPC_REGEX,
            ConstraintDescription=INVALID_VPC_MSG,
            Default=""
        ))
        self.mgmt_subnet_1 = self.template.add_parameter(Parameter(
            "MGMTSubnet1",
            Description="The ID Management Subnet in AZ 1",
            Type="AWS::EC2::Subnet::Id",
            MinLength="1",
            ConstraintDescription=INVALID_SUBNET_MSG,
            Default=""
        ))
        self.mgmt_subnet_2 = self.template.add_parameter(Parameter(
            "MGMTSubnet2",
            Description="The ID Management Subnet in AZ 2",
            Type="AWS::EC2::Subnet::Id",
            MinLength="1",
            ConstraintDescription=INVALID_SUBNET_MSG,
            Default=""
        ))
        self.private_route_table_1 = self.template.add_parameter(Parameter(
            "PrivateRouteTable1",
            Description="The ID of the Private Route Table in AZ 1",
            Type="String",
            AllowedPattern=VALID_RTB_REGEX,
            ConstraintDescription=INVALID_RTB_MSG,
            Default=""
        ))
        self.private_route_table_2 = self.template.add_parameter(Parameter(
            "PrivateRouteTable2",
            Description="The ID of the Private Route Table in AZ 2",
            Type="String",
            AllowedPattern=VALID_RTB_REGEX,
            ConstraintDescription=INVALID_RTB_MSG,
            Default=""
        ))
        self.ss_route_table_1 = self.template.add_parameter(Parameter(
            "SSRouteTable1",
            Description="The ID of the Shared Services Route Table in AZ 1",
            Type="String",
            AllowedPattern=VALID_RTB_REGEX,
            ConstraintDescription=INVALID_RTB_MSG,
            Default=""
        ))
        self.ss_route_table_2 = self.template.add_parameter(Parameter(
            "SSRouteTable2",
            Description="The ID of the Shared Services Route Table in AZ 2",
            Type="String",
            AllowedPattern=VALID_RTB_REGEX,
            ConstraintDescription=INVALID_RTB_MSG,
            Default=""
        ))

        # NAT Speciific Parameters
        self.nat_hostname_1 = self.template.add_parameter(Parameter(
            "NatHostname1",
            Description= "Prefix that should be used for the NAT hostnames",
            Type= "String",
            Default= "",
        ))
        self.nat_hostname_2 = self.template.add_parameter(Parameter(
            "NatHostname2",
            Description= "Prefix that should be used for the NAT hostnames",
            Type= "String",
            Default= "",
        ))

        self.nat_size = self.template.add_parameter(Parameter(
            "NatSize",
            Description= "Instance type for NAT nodes",
            Type= "String",
            Default= "t2.medium",
            AllowedValues= INSTANCE_TYPES,
            ConstraintDescription= INVALID_INSTANCE_TYPE_MSG
        ))
        self.ping_number = self.template.add_parameter(Parameter(
            "PingNumber",
            Description= "The number of times the health check will ping the alternate NAT Node",
            Type= "String",
            Default= "10",
        ))
        self.ping_timeout = self.template.add_parameter(Parameter(
            "PingTimeout",
            Description= "The number of seconds to wait for each ping response before determining that the ping has failed",
            Type= "String",
            Default= "2",
        ))
        self.time_between_pings = self.template.add_parameter(Parameter(
            "PingWait",
            Description= "The number of seconds to wait between health checks",
            Type= "String",
            Default= "2",
        ))
        self.time_for_instance_stop = self.template.add_parameter(Parameter(
            "InstanceStopWaitTime",
            Description= "The number of seconds to wait for alternate NAT Node to stop before attempting to stop it again",
            Type= "String",
            Default= "60",
        ))
        self.time_for_instance_start = self.template.add_parameter(Parameter(
            "InstanceStartWaitTime",
            Description= "The number of seconds to wait for alternate NAT Node to restart before resuming health checks again",
            Type= "String",
            Default= "300",
        ))

        self.instance_resources_bucket_name_param = self.template.add_parameter(Parameter(
            "UploadBucketName",
            Description="Bucket name for NAT Failover Script",
            Type="String",
            MinLength="1",
            Default=""
        ))
        self.ec2_instance_ami = self.template.add_parameter(Parameter(
            "EC2InstanceAmi",
            Description="Instance Base AMI for the NATs",
            Type="String",
            MinLength="1",
            AllowedPattern=VALID_AMI_REGEX,
            ConstraintDescription=INVALID_AMI_MSG,
            Default=""
        ))

    def add_mappings(self):
        self.vpc_mapping = self.template.add_mapping('VPCMAPPING', VPC_MAPPING)
        self.region_convention_mapping = self.template.add_mapping('REGIONNAMEMAPPINGS', REGION_TO_CONVENTION_MAPPING)
        self.nat_ami_mapping = self.template.add_mapping('NATAMIMAPPING',AWS_NAT_AMI)

        self.az_convention_mapping = self.template.add_mapping('AZNAMEMAPPINGS', AZS_TO_CONVENTION_MAPPING)
        self.az_per_account = self.template.add_mapping('ACCOUNTAZS', AZ_PER_ACCOUNT)

    def add_nat_instance_role(self):
        # Create a role for the NAT Instance
        # FIXME: Going to need to be able to grab and set own EIP
        self.nat_instance_role = self.template.add_resource(iam.Role(
            "NatInstanceRole",
            AssumeRolePolicyDocument={
              "Statement": [{
                "Effect": "Allow",
                "Principal": {
                  "Service": [ "ec2.amazonaws.com" ]
                },
                "Action": [ "sts:AssumeRole" ]
              }]
            },
            Path="/"
        ))

        # The NAT does not have any perms in this particular config
        self.nat_instance_ec2_policy = self.template.add_resource(iam.PolicyType(
          "NatInstanceEC2Policy",
          PolicyName="NAT_Takeover",
          PolicyDocument={
            # to allow us to update things
            "Statement": [{
              "Effect": "Allow",
              "Action": [
                "ec2:AssociateAddress",
                "ec2:DescribeInstances",
                "ec2:DescribeRouteTables",
                "ec2:CreateRoute",
                "ec2:ReplaceRoute",
                "ec2:StartInstances",
                "ec2:StopInstances"
              ], 
              "Resource": "*", # Perhaps come and change this, and use waitcondition handles to prevent other stuff happening
            }]
          },
          Roles=[ Ref(self.nat_instance_role) ]
        ))

        self.nat_instance_ec2_policy = self.template.add_resource(iam.PolicyType(
          "NatInstanceS3Policy",
          PolicyName="NAT_S3_Pull",
          PolicyDocument={
            # to allow us to update things
            "Statement": [{
                "Effect": "Allow",
                "Action": [ "s3:GetObject" ],
                "Resource": [
                    Join("", [ "arn:aws:s3:::", Ref(self.instance_resources_bucket_name_param), "" ]),
                    Join("", [ "arn:aws:s3:::", Ref(self.instance_resources_bucket_name_param), "/*" ]),
                ]
                },{
                "Effect": "Allow",
                "Action": [ "s3:PutObject" ],
                "Resource": [
                    Join("", [ "arn:aws:s3:::", Ref(self.instance_resources_bucket_name_param), "" ]),
                    Join("", [ "arn:aws:s3:::", Ref(self.instance_resources_bucket_name_param), "/*" ]),
                ]},
            ]
          },
          Roles=[ Ref(self.nat_instance_role) ]
        ))

        self.nat_instance_profile = self.template.add_resource(iam.InstanceProfile(
          "NatInstanceProfile",
          Path="/",
          Roles=[ Ref(self.nat_instance_role) ]
        ))


    def allocate_eips(self):
        self.eip1 = self.template.add_resource(ec2.EIP(
            "EIP1",
            Domain="vpc",
            InstanceId=Ref(self.nat_instance_1),
        ))
        self.eip2 = self.template.add_resource(ec2.EIP(
            "EIP2",
            Domain="vpc",
            InstanceId=Ref(self.nat_instance_2),
        ))

    def add_nat_sg(self):
        self.nat_instance_sg = self.template.add_resource(ec2.SecurityGroup(
            "NATSG",
            GroupDescription="Rules NAT instances. Also allows access to HA Nodes",
            VpcId=Ref(self.vpc_id),
            SecurityGroupIngress=[
              ec2.SecurityGroupRule( IpProtocol="tcp", FromPort="22", ToPort="22", CidrIp="10.0.0.0/8"),
              ec2.SecurityGroupRule( IpProtocol="tcp", FromPort="53", ToPort="53", CidrIp=FindInMap("VPCMAPPING", 
                                FindInMap("REGIONNAMEMAPPINGS", Ref("AWS::Region"), "Name"), Ref(self.environment_type))),
              ec2.SecurityGroupRule( IpProtocol="udp", FromPort="53", ToPort="53", CidrIp=FindInMap("VPCMAPPING", 
                                FindInMap("REGIONNAMEMAPPINGS", Ref("AWS::Region"), "Name"), Ref(self.environment_type))),
              ec2.SecurityGroupRule( IpProtocol="tcp", FromPort="80", ToPort="80", CidrIp=FindInMap("VPCMAPPING", 
                                FindInMap("REGIONNAMEMAPPINGS", Ref("AWS::Region"), "Name"), Ref(self.environment_type))),
              ec2.SecurityGroupRule( IpProtocol="tcp", FromPort="443", ToPort="443", CidrIp=FindInMap("VPCMAPPING", 
                                FindInMap("REGIONNAMEMAPPINGS", Ref("AWS::Region"), "Name"), Ref(self.environment_type))),
              ec2.SecurityGroupRule( IpProtocol="icmp", FromPort="-1", ToPort="-1", CidrIp="10.0.0.0/8"),

            ],

            Tags=self.get_tags_as_list(0, '-bigdata-sg-natsg')
        ))
    
        self.nat_ping_rule = self.template.add_resource(ec2.SecurityGroupIngress(
            "NATPingRule",
            GroupId=Ref(self.nat_instance_sg),
            SourceSecurityGroupId=Ref(self.nat_instance_sg),
            IpProtocol="icmp", 
            FromPort="-1", 
            ToPort="-1", 
        ))

    def add_nat_instances(self):

        self.eip_wait_handle_1 = self.template.add_resource(cf.WaitConditionHandle("EIPAttachmentHandle1"))
        self.userdata_wait_handle_1 = self.template.add_resource(cf.WaitConditionHandle("UserdataCompletionHandle1"))

        self.eip_wait_handle_2 = self.template.add_resource(cf.WaitConditionHandle("EIPAttachmentHandle2"))
        self.userdata_wait_handle_2 = self.template.add_resource(cf.WaitConditionHandle("UserdataCompletionHandle2"))

        tags1=self.get_tags_as_list(0, '-bigdata-mgmt-', Ref(self.nat_hostname_1))

        tags2=self.get_tags_as_list(1, '-bigdata-mgmt-',Ref(self.nat_hostname_2))

        self.nat_instance_1 = self.template.add_resource(ec2.Instance(
            "NATInstance1",
            IamInstanceProfile=Ref(self.nat_instance_profile),
            InstanceType=Ref(self.nat_size),
            KeyName=Ref(self.keyname_param),
            SubnetId=Ref(self.mgmt_subnet_1),
            ImageId=Ref(self.ec2_instance_ami),  #FindInMap("NATAMIMAPPING", Ref("AWS::Region"), "AMI"),
            SecurityGroupIds=[Ref(self.nat_instance_sg)],
            SourceDestCheck="false",
            Tags=tags1,
            #DependsOn=self.vpcgw.name,
            # We need to wait for NAT to become available, we assume that
            # if userdata is executing then we are good to go, so cfn-signal back
            # * * * * * * * * * * * * * * * * * *
            # PS Make sure other instances that require nat use DependsOn=WaitCondition, not
            # the nat itself as this takes some time to spin up
            # * * * * * * * * * * * * * * * * * *
            UserData=Base64(Join("", [
"#!/bin/bash -x\n", 
"exec > >(tee /var/log/user_data_run.log)\n", 
"exec 2>&1\n", 
"date\n", 
"ping -c 5 www.google.com > /var/log/ping-test.log\n", 
"##### Install cfn-init to interpret and act upon the metadata\n", 
"##### Ubuntu does not have this be default\n", 

"yum update -y aws*\n", 
". /etc/profile.d/aws-apitools-common.sh\n", 
"CFN=aws-cfn-bootstrap-latest\n", 
"wget -P /root https://s3.amazonaws.com/cloudformation-examples/${CFN}.tar.gz\n", 
"mkdir -p /root/${CFN}\n", 
"tar xvfz /root/${CFN}.tar.gz --strip-components=1 -C /root/${CFN}\n", 
"easy_install /root/${CFN}/","\n", 
"easy_install awscli\n", 
"/opt/aws/bin/cfn-signal -e 0 -r 'EIP is attached' '",Ref(self.eip_wait_handle_1),"' > /var/log/cfn-signal.log\n",

"##### change the hostname to something more identifible\n", 
"INSTANCEID=$(curl http://169.254.169.254//latest/meta-data/instance-id )\n", 
"INSTANCEIP=$(curl http://169.254.169.254//latest/meta-data/local-ipv4 )\n", 
"INSTANCEPUBLICIP=$(curl http://169.254.169.254//latest/meta-data/public-ipv4 )\n",

"NEWHOSTNAME=",Ref(self.nat_hostname_1),".timeinc.com\n",

"echo $NEWHOSTNAME > /etc/hostname\n", 
"sed -i '1i 127.0.0.1 '$NEWHOSTNAME /etc/hosts\n", 
"hostname -F /etc/hostname\n", 

"/opt/aws/bin/cfn-signal -e 0 -r 'NAT instance is ready for bootstrapping' '",Ref(self.userdata_wait_handle_1),"' > /var/log/cfn-signal.log\n",

"# Configure iptables\n", 
"/sbin/iptables -t nat -A POSTROUTING -o eth0 -s 0.0.0.0/0 -j MASQUERADE\n", 
"/sbin/iptables-save > /etc/sysconfig/iptables\n", 
"# Configure ip forwarding and redirects\n", 
"echo 1 >  /proc/sys/net/ipv4/ip_forward && echo 0 >  /proc/sys/net/ipv4/conf/eth0/send_redirects\n", 
"mkdir -p /etc/sysctl.d/\n", 
"cat <<EOF > /etc/sysctl.d/nat.conf\n", 
"net.ipv4.ip_forward = 1\n", 
"net.ipv4.conf.eth0.send_redirects = 0\n", 
"EOF\n",

"aws s3 cp s3://",Ref(self.instance_resources_bucket_name_param), "/nat_monitor.sh /root/nat_monitor.sh\n", 
"sed -i.bak 's/$4/$5/g' /root/nat_monitor.sh\n",

"# Wait for NAT #2 to boot up and update PrivateRouteTable2\n",
"sleep 180\n",
"NAT_ID=\n",
"# CloudFormation should have updated the PrivateRouteTable2 by now (due to yum update), however loop to make sure\n",
"while [ \"$NAT_ID\" == \"\" ]; do\n",
"  sleep 60\n",
"  NAT_ID=`/opt/aws/bin/ec2-describe-route-tables ",Ref(self.private_route_table_2), 
" -U https://ec2.",Ref("AWS::Region"), ".amazonaws.com | grep 0.0.0.0/0 | awk '{print $2;}'`\n",
"  #echo `date` \"-- NAT_ID=$NAT_ID\" >> /tmp/test.log\n",
"done\n",
"# Update NAT_ID, NAT_RT_ID, and My_RT_ID\n", 

# ToDo - Change line below to "sed -i.bak \"s/NAT_ID=/NAT_ID=",{ "Ref" : "NATInstances1" },"/g\" /root/nat_monitor.sh\n",
"sed -i.bak \"s/NAT_ID=/NAT_ID=$NAT_ID/g\" /root/nat_monitor.sh\n",
"sed -i.bak \"s/NAT_RT_ID1=/NAT_RT_ID1=",Ref(self.private_route_table_2),"/g\" /root/nat_monitor.sh\n",

# "sed -i.bak\"s/NAT_ID=/NAT_ID=$NAT_ID/g\" /root/nat_monitor.sh > /root/nat_monitor.tmp\n",
# Set up the relative route tables for each NAT

"sed -i.bak \"s/NAT_RT_ID2=/NAT_RT_ID2=",Ref(self.ss_route_table_2),"/g\" /root/nat_monitor.sh\n",

"sed -i.bak \"s/My_RT_ID1=/My_RT_ID1=",Ref(self.private_route_table_1),"/g\" /root/nat_monitor.sh\n",

"sed \"s/My_RT_ID2=/My_RT_ID2=",Ref(self.ss_route_table_1),"/g\" /root/nat_monitor.sh > /root/nat_monitor.tmp\n",


"sed \"s/EC2_URL=/EC2_URL=https:\\/\\/ec2.",Ref("AWS::Region"), ".amazonaws.com","/g\" /root/nat_monitor.tmp > /root/nat_monitor.sh\n",

"sed \"s/Num_Pings=3/Num_Pings=",Ref(self.ping_number),"/g\" /root/nat_monitor.sh > /root/nat_monitor.tmp\n",

"sed \"s/Ping_Timeout=1/Ping_Timeout=",Ref(self.ping_timeout),"/g\" /root/nat_monitor.tmp > /root/nat_monitor.sh\n",

"sed \"s/Wait_Between_Pings=2/Wait_Between_Pings=",Ref(self.time_between_pings),"/g\" /root/nat_monitor.sh > /root/nat_monitor.tmp\n",

"sed \"s/Wait_for_Instance_Stop=60/Wait_for_Instance_Stop=",Ref(self.time_for_instance_stop),"/g\" /root/nat_monitor.tmp > /root/nat_monitor.sh\n",

"sed \"s/Wait_for_Instance_Start=300/Wait_for_Instance_Start=",Ref(self.time_for_instance_start),"/g\" /root/nat_monitor.sh > /root/nat_monitor.tmp\n",

"mv /root/nat_monitor.tmp /root/nat_monitor.sh\n",
"chmod a+x /root/nat_monitor.sh\n",
"echo '@reboot /root/nat_monitor.sh > /var/log/nat_monitor.log' | crontab\n",
"/root/nat_monitor.sh > /var/log/nat_monitor.log &\n",

"exit 0\n"
            ]))
        ))

        self.nat_instance_2 = self.template.add_resource(ec2.Instance(
            "NATInstance2",
            IamInstanceProfile=Ref(self.nat_instance_profile),
            InstanceType=Ref(self.nat_size),
            KeyName=Ref(self.keyname_param),
            SubnetId=Ref(self.mgmt_subnet_2),
            ImageId=Ref(self.ec2_instance_ami), #FindInMap("NATAMIMAPPING", Ref("AWS::Region"), "AMI"),
            SecurityGroupIds=[Ref(self.nat_instance_sg)],
            SourceDestCheck="false",
            Tags=tags2,
            #DependsOn=self.vpcgw.name,
            # We need to wait for NAT to become available, we assume that
            # if userdata is executing then we are good to go, so cfn-signal back
            # * * * * * * * * * * * * * * * * * *
            # PS Make sure other instances that require nat use DependsOn=WaitCondition, not
            # the nat itself as this takes some time to spin up
            # * * * * * * * * * * * * * * * * * *
            UserData=Base64(Join("", [
"#!/bin/bash -x\n", 
"exec > >(tee /var/log/user_data_run.log)\n", 
"exec 2>&1\n", 
"date\n", 
"ping -c 5 www.google.com > /var/log/ping-test.log\n", 
"##### Install cfn-init to interpret and act upon the metadata\n", 
"##### Ubuntu does not have this be default\n", 

"yum update -y aws*\n", 
". /etc/profile.d/aws-apitools-common.sh\n", 
"CFN=aws-cfn-bootstrap-latest\n", 
"wget -P /root https://s3.amazonaws.com/cloudformation-examples/${CFN}.tar.gz\n", 
"mkdir -p /root/${CFN}\n", 
"tar xvfz /root/${CFN}.tar.gz --strip-components=1 -C /root/${CFN}\n", 
"easy_install /root/${CFN}/","\n", 
"easy_install awscli\n", 
"/opt/aws/bin/cfn-signal -e 0 -r 'EIP is attached' '",Ref(self.eip_wait_handle_2),"' > /var/log/cfn-signal.log\n",

"##### change the hostname to something more identifible\n", 
"INSTANCEID=$(curl http://169.254.169.254//latest/meta-data/instance-id )\n", 
"INSTANCEIP=$(curl http://169.254.169.254//latest/meta-data/local-ipv4 )\n", 
"INSTANCEPUBLICIP=$(curl http://169.254.169.254//latest/meta-data/public-ipv4 )\n",

"NEWHOSTNAME=",Ref(self.nat_hostname_2),".timeinc.com\n",

"echo $NEWHOSTNAME > /etc/hostname\n", 
"sed -i '1i 127.0.0.1 '$NEWHOSTNAME /etc/hosts\n", 
"hostname -F /etc/hostname\n", 

"/opt/aws/bin/cfn-signal -e 0 -r 'NAT instance is ready for bootstrapping' '",Ref(self.userdata_wait_handle_2),"' > /var/log/cfn-signal.log\n",

"# Configure iptables\n", 
"/sbin/iptables -t nat -A POSTROUTING -o eth0 -s 0.0.0.0/0 -j MASQUERADE\n", 
"/sbin/iptables-save > /etc/sysconfig/iptables\n", 
"# Configure ip forwarding and redirects\n", 
"echo 1 >  /proc/sys/net/ipv4/ip_forward && echo 0 >  /proc/sys/net/ipv4/conf/eth0/send_redirects\n", 
"mkdir -p /etc/sysctl.d/\n", 
"cat <<EOF > /etc/sysctl.d/nat.conf\n", 
"net.ipv4.ip_forward = 1\n", 
"net.ipv4.conf.eth0.send_redirects = 0\n", 
"EOF\n",

"aws s3 cp s3://",Ref(self.instance_resources_bucket_name_param), "/nat_monitor.sh /root/nat_monitor.sh\n", 
"sed -i.bak 's/$4/$5/g' /root/nat_monitor.sh\n",

"# Update NAT_ID, NAT_RT_ID, and My_RT_ID\n",
"sed -i.bak \"s/NAT_ID=/NAT_ID=",Ref(self.nat_instance_1),"/g\" /root/nat_monitor.sh\n",
# "sed -i.bak\"s/NAT_ID=/NAT_ID=",Ref(self.nat_instance_1),"/g\" /root/nat_monitor.sh > /root/nat_monitor.tmp\n",

# Set up the relative route tables for each NAT
"sed -i.bak \"s/NAT_RT_ID1=/NAT_RT_ID1=",Ref(self.private_route_table_1),"/g\" /root/nat_monitor.sh\n",
# "sed -i.bak \"s/NAT_RT_ID1=/NAT_RT_ID1=",Ref(self.private_route_table_1), "/g\" /root/nat_monitor.sh\n",

"sed -i.bak \"s/NAT_RT_ID2=/NAT_RT_ID2=",Ref(self.ss_route_table_1),"/g\" /root/nat_monitor.sh\n",

"sed -i.bak \"s/My_RT_ID1=/My_RT_ID1=",Ref(self.private_route_table_2),"/g\" /root/nat_monitor.sh\n",

"sed \"s/My_RT_ID2=/My_RT_ID2=",Ref(self.ss_route_table_2),"/g\" /root/nat_monitor.sh > /root/nat_monitor.tmp\n",


"sed \"s/EC2_URL=/EC2_URL=https:\\/\\/ec2.",Ref("AWS::Region"), ".amazonaws.com","/g\" /root/nat_monitor.tmp > /root/nat_monitor.sh\n",

"sed \"s/Num_Pings=3/Num_Pings=",Ref(self.ping_number),"/g\" /root/nat_monitor.sh > /root/nat_monitor.tmp\n",

"sed \"s/Ping_Timeout=1/Ping_Timeout=",Ref(self.ping_timeout),"/g\" /root/nat_monitor.tmp > /root/nat_monitor.sh\n",

"sed \"s/Wait_Between_Pings=2/Wait_Between_Pings=",Ref(self.time_between_pings),"/g\" /root/nat_monitor.sh > /root/nat_monitor.tmp\n",

"sed \"s/Wait_for_Instance_Stop=60/Wait_for_Instance_Stop=",Ref(self.time_for_instance_stop),"/g\" /root/nat_monitor.tmp > /root/nat_monitor.sh\n",

"sed \"s/Wait_for_Instance_Start=300/Wait_for_Instance_Start=",Ref(self.time_for_instance_start),"/g\" /root/nat_monitor.sh > /root/nat_monitor.tmp\n",

"mv /root/nat_monitor.tmp /root/nat_monitor.sh\n",
"chmod a+x /root/nat_monitor.sh\n",
"echo '@reboot /root/nat_monitor.sh > /var/log/nat_monitor.log' | crontab\n",
"/root/nat_monitor.sh > /var/log/nat_monitor.log &\n",

"exit 0\n"
            ]))
        ))

        self.eip_waitcondition_1 = self.template.add_resource(cf.WaitCondition(
                "EipAttachmentCondition1",
                DependsOn=self.nat_instance_1.name,
                Handle=Ref(self.eip_wait_handle_1),
                Timeout="1000"
            ))
        self.eip_waitcondition_2 = self.template.add_resource(cf.WaitCondition(
                "EipAttachmentCondition2",
                DependsOn=self.nat_instance_2.name,
                Handle=Ref(self.eip_wait_handle_2),
                Timeout="1000"
            ))
        self.userdata_waitcondition_1 = self.template.add_resource(cf.WaitCondition(
            "UserDataCompletionCondition1",
            DependsOn=self.nat_instance_1.name,
            Handle=Ref(self.userdata_wait_handle_1),
            Timeout="1000"
        ))
        self.userdata_waitcondition_2 = self.template.add_resource(cf.WaitCondition(
            "UserDataCompletionCondition2",
            DependsOn=self.nat_instance_2.name,
            Handle=Ref(self.userdata_wait_handle_2),
            Timeout="1000"
        ))

    def add_routes(self):
        self.private_route_1 = self.template.add_resource(ec2.Route(
            "PrivateRoute1",
            RouteTableId = Ref(self.private_route_table_1),
            DestinationCidrBlock= "0.0.0.0/0",
            InstanceId=Ref(self.nat_instance_1)
        ))
        self.private_route_2 = self.template.add_resource(ec2.Route(
            "PrivateRoute2",
            RouteTableId = Ref(self.private_route_table_2),
            DestinationCidrBlock= "0.0.0.0/0",
            InstanceId=Ref(self.nat_instance_2)
        ))
        self.ss_route_1 = self.template.add_resource(ec2.Route(
            "SSRoute1",
            RouteTableId = Ref(self.ss_route_table_1),
            DestinationCidrBlock= "0.0.0.0/0",
            InstanceId=Ref(self.nat_instance_1)
        ))
        self.ss_route_2 = self.template.add_resource(ec2.Route(
            "SSRoute2",
            RouteTableId = Ref(self.ss_route_table_2),
            DestinationCidrBlock= "0.0.0.0/0",
            InstanceId=Ref(self.nat_instance_2)
        ))

    def add_outputs(self):

        # """ Implements the abstract method and writes IDs of various
        #     created resources """
        self.template.add_output(Output(
            "vpcid",
            Description="ID of the VPC",
            Value=Ref(self.vpc_id)
        ))
        self.template.add_output(Output(
            "NATAZbIP",
            Description="Public IP of the NAT in AZ b",
            Value=GetAtt(self.nat_instance_1, "PublicIp")
        ))
        self.template.add_output(Output(
            "NATAZcIP",
            Description="Public IP of the NAT in AZ c",
            Value=GetAtt(self.nat_instance_2, "PublicIp")
        ))
#
# End of Class

if __name__ == "__main__":
    natstack = NATStack()
    print(natstack.template.to_json())
