#!/usr/bin/env python

import os
import sys

from troposphere import GetAtt, GetAZs, Join, Output, Parameter, Ref, Select, FindInMap
import troposphere.cloudformation as cf
import troposphere.ec2 as ec2

from base import CloudformationAbstractBaseClass
from constants import *


class BaseSGs(CloudformationAbstractBaseClass):

    def __init__(self):
        super(BaseSGs, self).__init__()
        self.template.add_description("Template to create generic Security Group")
        self.add_parameters()
        self.add_main_sgs()
        self.add_outputs()


    def add_parameters(self):

        """ Implements the abstract method and defines a number of parameters the
            calling process or GUI must supply """
        super(BaseSGs,self).add_default_parameters()

        self.vpc_id = self.template.add_parameter(Parameter(
            "VpcId",
            Description="The ID of the existing Virtual Private Cloud (VPC)",
            Type="AWS::EC2::VPC::Id",
            MinLength="1",
            AllowedPattern=VALID_VPC_REGEX,
            ConstraintDescription=INVALID_VPC_MSG
        ))

    def add_main_sgs(self):

        self.sg_standardsg = self.template.add_resource(ec2.SecurityGroup(
            "NonLoopingSG",
            GroupDescription="Security Group that statcially lists all rules",
            Tags=self.get_tags_as_list(None, '-nonloopingSg-tag'),
            VpcId=Ref(self.vpc_id),
            SecurityGroupIngress=[
              ec2.SecurityGroupRule( IpProtocol="tcp", FromPort="22", ToPort="22", CidrIp="10.0.0.0/18" ),
            ]
        ))

        """ Here is the list that the SG will loop through """

        loop_rules = [
            {'prot': 'tcp', 'fp' : '8080', 'tp': '8080'},
            {'prot': 'tcp', 'fp' : '80', 'tp': '80'},
            {'prot': 'tcp', 'fp' : '3389', 'tp': '3389'},
        ]

        """ This is where the looping sg is declared"""
        self.sg_loopsg = self.template.add_resource(ec2.SecurityGroup(
            "LoopingSecurityGroup",
            GroupDescription="Security Group that loops through a list loop_rules",
            Tags=self.get_tags_as_list(None, '-loopingSg-tag'),
            VpcId=Ref(self.vpc_id),
        ))
        """ no fucking clue what this does, but you need it"""
        self.sg_loopsg_ingress = []

        """ This is where the sg loops. The SG is created and this loop appends on to that sg adding the IpProtocol
        and what ever else information until the list completes.  """
        for i, props in enumerate(loop_rules):
            self.sg_loopsg_ingress.append(self.template.add_resource(ec2.SecurityGroupIngress(
                "LoopSGingress%i" %i,
                GroupId = Ref(self.sg_loopsg),
                IpProtocol=props['prot'],
                FromPort=props['fp'],
                ToPort=props['tp'],
                SourceSecurityGroupId=Ref(self.sg_loopsg) 
        )))

    def add_outputs(self):

        # Implements the abstract method and writes IDs of various
        #     created resources

        self.template.add_output(Output(
            "vpcid",
            Description="ID of the VPC",
            Value=Ref(self.vpc_id)
        ))
        self.template.add_output(Output(
            "NonLoopingSG",
            Description="ID of the non-looping SG",
            Value=Ref(self.sg_standardsg)
        ))
        self.template.add_output(Output(
            "LoopingSecurityGroup",
            Description="ID of the looping SG",
            Value=Ref(self.sg_loopsg)
        ))

if __name__ == "__main__":
    basesgs = BaseSGs()
    print(basesgs.template.to_json())