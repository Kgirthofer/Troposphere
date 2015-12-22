#!/usr/bin/env python

from troposphere import FindInMap, GetAZs, Ref, Select, Template, Parameter, Join, Equals, If
from constants import *
import troposphere.ec2 as ec2
import troposphere.elasticloadbalancing as elb
import troposphere.cloudwatch as cloudwatch
import troposphere.iam as iam
import abc
from constants import *

USER_TAG_COUNT=0

class CloudformationAbstractBaseClass:

    """ Abstract base class with some common CFN functionality """

    __metaclass__ = abc.ABCMeta

    template = Template()

    DEFAULT_TAGS = []

    SSH_FROM_ANYWHERE = ec2.SecurityGroupRule(
        IpProtocol="tcp",
        FromPort="22",
        ToPort="22",
        CidrIp=QUAD_ZERO_CIDR
    )

    ELB_HTTP_LISTENER = elb.Listener(
        LoadBalancerPort="80",
        Protocol="HTTP",
        InstancePort="80",
        InstanceProtocol="HTTP"  
    )

    def __init__(self):
        self.add_mappings()

    def add_default_parameters(self):
        self.environment_type = self.template.add_parameter(Parameter(
            "EnvironmentName",
            Description=ENVIRONMENT_MSG,
            Type="String",
            MinLength="1",
            AllowedValues=VALID_ENVIRONMENTS,
            ConstraintDescription=INVALID_ENVIRONMENT_MSG,
        ))
        self.isprod_condition = self.template.add_condition('IsProd', Equals(Ref(self.environment_type), 'prod'))
        self.account_name = self.template.add_parameter(Parameter(
            "Account",
            Description=ACCOUNT_MSG,
            Type="String",
            MinLength="1",
            AllowedValues=VALID_ACCOUNTS,
        ))
        self.department_information = self.template.add_parameter(Parameter(
                    "DepartmentInformationTag",
                    Description="Value for Department Information (GL_DEPT) tag",
                    Type="String",
                    MinLength="1",
                    Default="gld=8864"
        ))
        self.business_unit_information = self.template.add_parameter(Parameter(
                    "BUInformationTag",
                    Description="Value for Business Unit Information (GL_BU) tag",
                    Type="String",
                    MinLength="1",
                    Default="glbu=00001"
        ))
        self.application_information = self.template.add_parameter(Parameter(
                    "ApplicationInformationTag",
                    Description="Value for ApplicationInformation tag",
                    Type="String",
                    MinLength="1",
                    Default="appname=GirthoferPlatform;owner=karlgirthofer@.com;email=karlgirthofer@gmail.com;brand=Girthofer"
        ))
        self.infrastructure_information = self.template.add_parameter(Parameter(
                    "InfrastructureInformationTag",
                    Description="Value for InfrastructureInformation tag",
                    Type="String",
                    MinLength="1"
        ))
        self.security_information = self.template.add_parameter(Parameter(
                    "SecurityInformationTag",
                    Description="Value for SecurityInformaton tag",
                    Type="String",
                    MinLength="1"
        ))
    def add_default_windows_parameters(self):
        self.S3BinariesBucket = self.template.add_parameter(Parameter(
                    "S3BinariesBucket",
                    Description="Value the S3 bucket to retrieve binaries from for Windows bootstrapping",
                    Type="String",
                    MinLength="1",
                    Default="WindowsBootstrap"
        ))
        self.S3ScriptsBucket = self.template.add_parameter(Parameter(
                    "S3ScriptsBucket",
                    Description="Value the S3 bucket to retrieve scripts from for Windows bootstrapping",
                    Type="String",
                    MinLength="1",
                    Default="WindowsBootstrapScripts"
        ))
        self.domain_admin_username = self.template.add_parameter(Parameter(
            "DomainAdminUser",
            Description="User to join domain",
            Type="String",
            MinLength="5",
            MaxLength="25",
            AllowedPattern="[a-zA-Z0-9]*"
        ))
        self.domain_admin_password = self.template.add_parameter(Parameter(
            "DomainAdminPassword",
            Description= "Password to join domain",
            Type= "String",
            MinLength= "8",
            MaxLength= "32",
            AllowedPattern= "(?=^.{6,255}$)((?=.*\\d)(?=.*[A-Z])(?=.*[a-z])|(?=.*\\d)(?=.*[^A-Za-z0-9])(?=.*[a-z])|(?=.*[^A-Za-z0-9])(?=.*[A-Z])(?=.*[a-z])|(?=.*\\d)(?=.*[A-Z])(?=.*[^A-Za-z0-9]))^.*",
            NoEcho= True
        ))

    def get_tags_as_list(self, az_index, *name_joins):

        # Added a switch to allow us to create names that do not have the az_index specified. Could be cleaned up
        # 'None' sohuld be 
        if az_index is None:
            return [
            ec2.Tag("Name", Join("",["ti-", FindInMap("REGIONNAMEMAPPINGS", Ref("AWS::Region"), "Name"), 
                    ] + [e for e in name_joins] )),
            ec2.Tag("gl_dept", Ref(self.department_information)),
            ec2.Tag("gl_bu", Ref(self.business_unit_information)),
            ec2.Tag("app_info", Ref(self.application_information)),
            ec2.Tag("infra_info", Ref(self.infrastructure_information)),
            ec2.Tag("sec_info", Ref(self.security_information))
            ]
        else:
            return [
            ec2.Tag("Name", Join("",["ti-", FindInMap("REGIONNAMEMAPPINGS", Ref("AWS::Region"), "Name"), 
                Select(az_index, FindInMap("AZNAMEMAPPINGS", 
                            Ref(self.account_name),
                            FindInMap("REGIONNAMEMAPPINGS", Ref("AWS::Region"), "Name"))
                            ), 
                    ] + [e for e in name_joins] )),
            ec2.Tag("gl_dept", Ref(self.department_information)),
            ec2.Tag("gl_bu", Ref(self.business_unit_information)),
            ec2.Tag("app_info", Ref(self.application_information)),
            ec2.Tag("infra_info", Ref(self.infrastructure_information)),
            ec2.Tag("sec_info", Ref(self.security_information))
            ]

    """def add_default_cloudwatch_alarms(self, hostname, instance, postfix = ''):

        self.cloudwatch_alarm_1 = self.template.add_resource(cloudwatch.Alarm(
            "CPUAlarm" + postfix,
            ActionsEnabled=True,
            AlarmActions=If("IsProd", ["arn:aws:sns:us-east-1:"], ["arn:aws:sns:us-east-1::" ]),
            AlarmName= Join("",["CPU_",hostname,]),
            AlarmDescription=Join("",["CPU Monitor for ",hostname, postfix]),
            ComparisonOperator="GreaterThanThreshold",
            Dimensions=[cloudwatch.MetricDimension(Name="InstanceId", Value= instance)],
            EvaluationPeriods= "5",
            InsufficientDataActions=If("IsProd", ["arn:aws:sns:us-east-1::"], ["arn:aws:sns:us-east-1::" ]),
            MetricName= "CPUUtilization",
            Namespace= "AWS/EC2",
            OKActions=If("IsProd", ["arn:aws:sns:us-east-1::"], ["arn:aws:sns:us-east-1::" ]),
            Period= "60",
            Statistic= "Average",
            Threshold= "75",
            Unit= "Percent"
        ))
        self.cloudwatch_alarm_2 = self.template.add_resource(cloudwatch.Alarm(
            "HealthAlarm" + postfix,
             Adjust this to enable notifications 
            ActionsEnabled=False, 
            
            AlarmActions=If("IsProd", ["arn:aws:sns:us-east-1::"], ["arn:aws:sns:us-east-1::" ]),            AlarmName= Join("",["HEALTH_",hostname]),
            
            AlarmDescription=Join("",["Health Monitor for ",hostname]),
            ComparisonOperator="GreaterThanOrEqualToThreshold",
            Dimensions=[cloudwatch.MetricDimension(Name="InstanceId", Value= instance)],
            EvaluationPeriods= "1",
            InsufficientDataActions=If("IsProd", ["arn:aws:sns:us-east-1::"], ["arn:aws:sns:us-east-1::" ]),
            MetricName= "StatusCheckFailed",
            Namespace= "AWS/EC2",
            Instert SNS ARN Name Here
            OKActions=If("IsProd", ["arn:aws:sns:us-east-1::"], ["arn:aws:sns:us-east-1::" ]), 
            Period= "60",
            Statistic= "Average",
            Threshold= "1",
            Unit= "Count"
    
        ))"""

    def add_default_instance_role(self, prefix,S3BinariesBucket, S3ScriptsBucket):
        # Creatng default role and default policy for templates
        self.instance_role = self.template.add_resource(iam.Role(
            "%sInstanceRole" % prefix,
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

        self.instance_ec2_policy = self.template.add_resource(iam.PolicyType(
          "%sS3Policy" % prefix,
          PolicyName="Default_Bootstrap_S3",
          PolicyDocument={
            # to allow us to update things
            "Statement": [{
                "Effect": "Allow",
                "Action": [ "s3:GetObject" ],
                "Resource": [
                    Join("", [ "arn:aws:s3:::", S3BinariesBucket, "" ]),
                    Join("", [ "arn:aws:s3:::", S3BinariesBucket, "/*" ]),
                ]
                },{
                "Effect": "Allow",
                "Action": [ "s3:GetObject" ],
                "Resource": [
                    Join("", [ "arn:aws:s3:::", S3ScriptsBucket, "" ]),
                    Join("", [ "arn:aws:s3:::", S3ScriptsBucket, "/*" ]),
                ]},
            ]
          },
          Roles=[ Ref(self.instance_role) ]
        ))

        self.instance_profile = self.template.add_resource(iam.InstanceProfile(
          "%sInstanceProfile" % prefix,
          Path="/",
          Roles=[ Ref(self.instance_role) ]
        ))

    def add_mappings(self):
        self.region_to_az = self.template.add_mapping('RegionToAz', REGION_TO_AZ)
        self.base_sgs = self.template.add_mapping('BASESGS', BASE_SGS)
        self.vpc_mapping = self.template.add_mapping('VPCMAPPING', VPC_MAPPING)
        self.subnet_mapping = self.template.add_mapping('SUBNETMAPPINGS', SUBNET_MAPPING)
        self.tier_ip_mapping = self.template.add_mapping('TIERIPMAPPINGS', TIER_IP_MAPPING)
        self.region_convention_mapping = self.template.add_mapping('REGIONNAMEMAPPINGS', REGION_TO_CONVENTION_MAPPING)
        self.az_convention_mapping = self.template.add_mapping('AZNAMEMAPPINGS', AZS_TO_CONVENTION_MAPPING)
        self.az_per_account = self.template.add_mapping('ACCOUNTAZS', AZ_PER_ACCOUNT)

    def make_subnet(self, name, description, azindex, cidrblockref, vpcref):
        return ec2.Subnet(
            name, 
            AvailabilityZone=Select(azindex, FindInMap("RegionToAz", Ref("AWS::Region"), "AZ")),
            CidrBlock=cidrblockref,
            VpcId=vpcref,
            Tags=self.DEFAULT_TAGS + [
                ec2.Tag("Name", name),
                ec2.Tag("Description", description)
            ]
        )

    # You might want to shrink up the metadata as its long!
    # hostname is set within the executables section via string insertion
    # This is given as a method rahter than just a string in constants.py to allow hostname insertion.
    def get_windows_metadata(self, servername, rolename, instance_logical_name,):
        WINDOWS_INSTANCE_METADATA = {
            
        }
        return WINDOWS_INSTANCE_METADATA




    def make_subnet_with_tags(self, name, description, azindex, cidrblockref, vpcref, taglist=[]):
        return ec2.Subnet(
            name, 
            AvailabilityZone=Select(azindex, FindInMap("RegionToAz", Ref("AWS::Region"), "AZ")),
            CidrBlock=cidrblockref,
            VpcId=vpcref,
            Tags=taglist
        )


    def make_subnet_association(self, name, subnetref, routetableref):
        return ec2.SubnetRouteTableAssociation(
            name,
            SubnetId=subnetref,
            RouteTableId=routetableref
        )


    def make_acl_with_tags(self, name, vpcref, taglist=[]):
        return ec2.NetworkAcl(
            name,
            Tags=taglist,
            VpcId=vpcref
            )


    def make_acl_subnet_association(self, name, subnetref, ntwaclref ):
        return ec2.SubnetNetworkAclAssociation(
            name,
            SubnetId=subnetref,
            NetworkAclId=ntwaclref
            )


    def add_gateways(self, vpcref, taglist=[]):
        """ Creates the internet gateway and associates/attaches it to the VPC """
        internet_gateway = ec2.InternetGateway(
            "InternetGateway",
            Tags=taglist
        )
        vpc_gateway_attachment = ec2.VPCGatewayAttachment(
            "VPCGatewayAttachment",
            VpcId=vpcref,
            InternetGatewayId=Ref(internet_gateway),
        )
        return (internet_gateway, vpc_gateway_attachment)


    def add_virtual_pgw(self, name, vpcref, taglist=[]):
        """ Creates the Virtual Private gateway and associates/attaches it to the VPC """
        vp_gateway = ec2.VPNGateway(
            "%sVPNGateway" % name,
            Type="ipsec.1",
            Tags=taglist
        )
        vpc_vpg_attachment = ec2.VPCGatewayAttachment(
            "%sVPCVPNGatewayAttachment" % name,
            VpcId=vpcref,
            VpnGatewayId=Ref(vp_gateway)
        )
        return (vp_gateway, vpc_vpg_attachment)


    def add_defaultAclEntry(self, name, aclref):

        aclEntryIngress = self.add_defaultAclEntryIngress(name, aclref)
        aclEntryEgress  = self.add_defaultAclEntryEngress(name, aclref)

        return (aclEntryIngress, aclEntryEgress) 
    

    def add_defaultAclEntryIngress(self, name, aclref):

        return ec2.NetworkAclEntry(
            "%sIngress" % name,
            CidrBlock="0.0.0.0/0",
            NetworkAclId=Ref(aclref),
            Egress=False,
            Protocol="-1",
            RuleAction="ALLOW",
            RuleNumber=100
        )
    

    def add_defaultAclEntryEngress(self, name, aclref):

        return ec2.NetworkAclEntry(
            "%sEgress" % name,
            CidrBlock="0.0.0.0/0",
            Egress=True,
            NetworkAclId=Ref(aclref),
            Protocol="-1",
            RuleAction="ALLOW",
            RuleNumber=100
        )


    def add_route_table(self, vpcref, name, tags):
        return ec2.RouteTable(
            name,
            VpcId=vpcref,
            Tags=tags
        )
        
    def add_routing_tables(self, vpcref):
        """ Creates common route tables for public and private resources.
            They are not really functional until a route is associated
            with them, but that can't happen until NAT or IGW is available.
            Also we do this so that the default Main=Yes route table is left
            free of any routes other than "local", therefore subnets must
            be told to use public or private to be able to route out """
        
        public = self.add_route_table(vpcref, "PublicRouteTable", self.DEFAULT_TAGS)
        private = self.add_route_table(vpcref, "PrivateRouteTable", self.DEFAULT_TAGS)
        return (public, private)

    def get_name_tag(self, name):
        return ec2.Tag("Name", name)

    @abc.abstractmethod
    def add_parameters(self):
        """ Stub abstract method to add parameters """
        return


    @abc.abstractmethod
    def add_outputs(self):
        """ Stub to add outputs """
        return

if __name__ == "__main__":
    pass
