#!/usr/bin/env python

# Generic set of useful constants and expressions for building
# cloudformation templates with Troposphere
#
# Some messages terse/abbreviated to save characters and try to
# stay within CFN upload limits. Also the default messages may not
# be terribly useful without additional context so are largely
# here for completeness



# Migration specific constants
USER_TAG_COUNT            = 7           # The number of user generated tags for each instance
INTERNAL_IP_RANGE         = "10.0.0.0/8"
VPCID                     = "" # prod VCP
DEFAULT_VPC_CIDR          = "10.0.0.0/18"


REGION_TO_CONVENTION_MAPPING = {
    "us-east-1" : { "Name" : "use1" },
    "eu-west-1" : { "Name" : "euw1" },
    "us-west-2" : { "Name" : "usw2" },
    "ap-northeast-1" : {"Name" : "apne1"}
}

# This is not used functionality. But is used for tagging
VPC_MAPPING =  {
      "euw1" : { "prod" : "xx.xx.xx.xx/xx" },
      "use1" : { "prod" : "10.0.0.0/18", "test" : "10.0.10.0/18" },
      "usw2" : { "prod" : "xx.xx.xx.xx/xx", "test" : "xx.xx.xx.xx/xx" },
      "apne1" : { "prod" : "xx.xx.xx.xx/xx" }
}

AWS_LINUX_AMI = {
    "eu-west-1":      { "AMI": "ami-a921dfde" },
    "us-east-1":      { "AMI": "ami-2f726546" },
    "us-west-2":      { "AMI": "ami-b8f69f88" },  # oregon
    "us-west-1":      { "AMI": "ami-84f1cfc1" },
    "ap-southeast-1": { "AMI": "ami-787c2c2a" }, # singapore
    "ap-southeast-2": { "AMI": "ami-0bc85031" },  # sydney
    "ap-northeast-1": { "AMI": "ami-a1bec3a0" }, # tokyo
    "sa-east-1":      { "AMI": "ami-89de7c94" }
}

BASE_SGS = {
         "Common"            :  {'prod' : 'sg-ebd1e48f', 'test' : 'xx'},
}

SUBNET_MAPPING = {
    "use1" : {
        "prod" : "10.0.", "test" : "10.0."
    },
}

TIER_IP_MAPPING = {
    "tier0"  :   {"prod" : "10.0/24", "test" : "xx.xx/24" }, #web   
    "tier1"  :   {"prod" : "11.0/24", "test" : "xx.xx/24" }, #app
    "tier2"  :   {"prod" : "12.0/24", "test" : "xx.xx/24" }, #data(base)
    "tier3"  :   {"prod" : "13.0/24", "test" : "xx.xx/24" }, #mgmt(management)
}

PROD_SUBNET_MAPPING = {
    "web"   :   {"AZb" : "subnet-", "AZc" : "subnet-" },
    "app"   :   {"AZb" : "subnet-", "AZc" : "subnet-" },
    "data"  :   {"AZb" : "subnet-", "AZc" : "subnet-" },
    "mgmt"  :   {"AZb" : "subnet-", "AZc" : "subnet-" },
}

TIER_IP_MAPPING_AGGR = {
    "web"   :   {"prod" : "10.0/23", "test" : "xx.xx/23" },
    "app"   :   {"prod" : "11.0/23", "test" : "xx.xx/23" },
    "data"  :   {"prod" : "12.0/23", "test" : "xx.xx/23" },
    "mgmt"  :   {"prod" : "13.0/23", "test" : "xx.xx/23" },
}

TIERS = {
            "0" : "WebTier",
            "1" : "AppTier",
            "2" : "DataTier",
            "3" : "MgmtTier",
}

AZS_TO_CONVENTION_MAPPING = {
    "prod"  : { "use1" : ["a", "b", "c"]},
}

AZ_PER_ACCOUNT = {
        "prod"  : { "use1" : ["us-east-1a", "us-east-1b","us-east-1c"]}, 
    } 

# Random ones

DEFAULT_SOURCE_IP         = "86.169.99.119"
DEFAULT_SOURCE_CIDR       = "86.169.99.119/32"
QUAD_ZERO_CIDR            = "0.0.0.0/0"

VALID_TRUE_FALSE_VALUES   = [ "true", "false" ]

# Unable to make this AZ dynamic at the moment without big complication

NAT_AZ                    = "AZa"
NAT_CREATE_TIMEOUT        = "500"
NAT_AZ2                    = "AZb"

# DB related

DEFAULT_DB_STORAGE        = "20"
MIN_DB_STORAGE            = "5"
MAX_DB_STORAGE            = "1024"
INVALID_DB_STORAGE_MSG    = "must be number between 5 and 1024 (gb)"

# Typically use 3x AZ's but not all regions support this so might break
# in some circumstances

# REQUIRED_AZS              = { "0": "AZa", "1": "AZb", "2": "AZc" }
# This needs to be 1 and 2 as we do not have AZa in the account

REQUIRED_AZS              = { "0": "AZa", "1": "AZb"} #Edited as we only use 2 AZs here
REQUIRED_AZS_CONVENTION   = { "0": "a", "1": "b"}

VALID_AZ_VALUES           = [ "AZa", "AZb", "AZc" ]
INVALID_AZ_MSG            = "Must be a valid AZ = AZa, AZb or AZc"

# 3 AZ's used here
#REQUIRED_AZS              = { "0": "AZc", "1": "AZd", "2": "AZe" }
#VALID_AZ_VALUES           = [ "AZc", "AZd", "AZe" ]
#INVALID_AZ_MSG            = "Must be a valid AZ = AZc, AZd or AZe"

# for simple strings

NUMBER_STRING             = "\d+"
OPTIONAL_NUMBER_STRING    = "\d*"
ALPHANUMERIC_LC_STRING    = "[a-z0-9\-]*"
ALPHANUMERIC_STRING       = "[a-zA-Z0-9]*"
VALID_STRING_REGEX        = "[a-zA-Z]" + ALPHANUMERIC_STRING
OPTIONAL_CSV_STRING       = "[a-zA-Z0-9\-,]+|^$"
INVALID_STRING_MSG        = "Must be alphanumeric string"
OPTIONAL_TIME_WINDOW      = "\d\d:\d\d-\d\d:\d\d|^$"
# eg thu:01:10-thu:01:40
OPTIONAL_DOWTIME_WINDOW   = "[a-z][a-z][a-z]:\d\d:\d\d-[a-z][a-z][a-z]:\d\d:\d\d|^$"

# eg STAGING

ENVIRONMENT_MSG           = "Environment (Test [test], Dev [d], QA [q], UAT [u], RC [r], Production [prod])."
ENVIRONMENT_LOCATION_MSG = "Location of the environment (euw1, use1, usw2, apne1). Input whole abbreviation."
VALID_ENVIRONMENTS        = ["test", "dev", "prod"]
VALID_ENVIRONMENT_LOCATIONS = [ "euw1", "use1", "usw2", "apne1" ]

ACCOUNT_MSG = "Account this template is being run in e.g. prod or test"
VALID_ACCOUNTS = ["prod", "test"]

VALID_ENVIRONMENT_REGEX   = ALPHANUMERIC_LC_STRING
INVALID_ENVIRONMENT_MSG   = "Provide a lower case env name eg dev, test, prod etc"
INVALID_ENVIRONMENT_LOCATION_MSG = "Provide location in accepted format - euw1, use1 usw2, apne1"

# eg 12.34.56.78

IP_MSG                    = "Enter an IP"
EIP_MAX_LENGTH            = 15
VALID_IP_REGEX            = "\\d{1,3}+\\.\\d{1,3}+\\.\\d{1,3}+\\.\\d{1,3}"
INVALID_IP_MSG            = "Must be valid IP xx.xx.xx.xx"

# eg 12.34.56.78/32

CIDR_IP_MSG               = "Enter a CIDR form IP"
CIDR_MAX_LENGTH           = 18
VALID_CIDR_IP_REGEX       = VALID_IP_REGEX + "/\\d{1,2}"
INVALID_CIDR_IP_MSG       = "Must be valid CIDR form xx.xx.xx.xx/xx"

# eg my-aws-key

KEYNAME_MSG               = "Enter name of existing key"
VALID_KEYNAME_REGEX	      = "[\w-\.]*"
INVALID_KEYNAME_MSG       = "Must be valid key name"

# for internal construction, since most AWS resources have this form

EIGHT_DIGIT_HEX           = "[a-f0-9]{8}"

#

VALID_BASE64_REGEX        = "^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{4})$"
INVALID_BASE64_MSG        = "Must be valid Base64-encoded data"

# eg vpc-a1b2c3d4

VPC_MSG                   = "Enter existing VPC"
VALID_VPC_REGEX           = "vpc-" + EIGHT_DIGIT_HEX
INVALID_VPC_MSG           = "Must be valid VPC = vpc-xxxxxxxx"

# eg ami-a1b2c3d4

AMI_MSG                   = "Enter existing AMI"
VALID_AMI_REGEX           = "ami-" + EIGHT_DIGIT_HEX
INVALID_AMI_MSG           = "Must be valid AMI = ami-xxxxxxxx"

# eg rtb-a1b2c3d4

RTB_MSG                   = "Enter route table"
VALID_RTB_REGEX           = "rtb-" + EIGHT_DIGIT_HEX
INVALID_RTB_MSG           = "Must be valid route table = rtb-xxxxxxxx"

# eg subnet-a1b2c3d4

SUBNET_MSG                = "Enter subnet"
VALID_SUBNET_REGEX        = "subnet-" + EIGHT_DIGIT_HEX
INVALID_SUBNET_MSG        = "Must be valid subnet = subnet-xxxxxxxx"

# eg sg-a1b2c3d4

SG_MSG                    = "Enter security group"
VALID_SG_REGEX            = "sg-" + EIGHT_DIGIT_HEX
INVALID_SG_MSG            = "Must be valid security group = sg-xxxxxxxx"

# eg eipalloc-a1b2c3d4

EIPALLOC_MSG              = "Enter elastic IP allocation"
VALID_EIPALLOC_REGEX      = "eipalloc-" + EIGHT_DIGIT_HEX
INVALID_EIPALLOC_MSG      = "Must be valid EIP alloc = eipalloc-xxxxxxxx"

# eg eni-a1b2c3d4

ENI_MSG                   = "Enter ENI"
VALID_ENI_REGEX           = "eni-" + EIGHT_DIGIT_HEX
INVALID_ENI_MSG           = "Must be valid network intf = eni-xxxxxxxx"

# eg ebs vol types

VOLUME_MSG                = "Enter volume type"
VOLUME_TYPES              = [ "standard", "io1" ]
INVALID_VOLUME_TYPE_MSG   = "Must be valid EBS vol type - standard or io1"

# db snapshots can pretty much be any string

DB_SNAPSHOT_MSG           = "DB Snapshot (optional)"
VALID_DB_SNAPSHOT_REGEX   = "[a-zA-Z0-9]*"
INVALID_DB_SNAPSHOT_MSG   = INVALID_STRING_MSG

# eg mysql, oracle-se1, postgres etc

DB_ENGINE_MSG             = "Engine Selection"
DB_ENGINE_DEFAULT         = "MySQL"
DB_ENGINE_TYPES           = [ "MySQL", "postgres", "oracle-se1", "oracle-se", "oracle-ee", "sqlserver-ee", "sqlserver-se", "sqlserver-ex", "sqlserver-web" ]
INVALID_DB_ENGINE_TYPE    = "Must be a valid AWS db engine type"

# eg 5.5, 5.6 for mysql but varies per engine

DB_ENGINE_VERSION_MSG     = "Engine Version"
DB_ENGINE_VERSION_DEFAULT = "5.6"
INVALID_DB_ENGINE_VERSION = "Must be a valid AWS db engine version"

# DB port, goes hand in hand with engine

DB_PORT_MSG               = "DB port"
DB_PORT_DEFAULT           = "3306"
VALID_DB_PORT_REGEX       = NUMBER_STRING
INVALID_DB_PORT_MSG       = "Must be a number"

# DB IOS is a number, but by default not used (blank) - CFN::If function helps in the code here

DB_IOPS_MSG               = "DB IOPS (optional, in 1000 iops increments)"
DB_IOPS_DEFAULT           = ""
VALID_DB_IOPS_REGEX       = OPTIONAL_NUMBER_STRING
INVALID_DB_IOPS_MSG       = "Must be number in multiple of 1000 or blank for no IOPS"

# How long to retain automated backups

DB_BACKUP_RETENTION_PERIOD_MSG         = "Number of dats which automatic backups are retained"
INVALID_DB_BACKUP_RETENTION_PERIOD_MSG = "Must be a number"
DEFAULT_DB_BACKUP_RETENTION_PERIOD     = "14"

# When to do a DB backup

DB_BACKUP_WINDOW_MSG      = "Backup Window (leave blank for random overnight GMT, no overlap with maint)"
DB_BACKUP_WINDOW_DEFAULT  = ""
VALID_DB_BACKUP_WINDOW_REGEX = OPTIONAL_TIME_WINDOW
INVALID_DB_BACKUP_WINDOW_MSG = "Must be hh:mm-hh:mm or blank"

# When to do DB maintenance

DB_MAINT_WINDOW_MSG      = "Maintenance Window (leave blank for random overnight GMT, no overlap with backup)"
DB_MAINT_WINDOW_DEFAULT  = ""
VALID_DB_MAINT_WINDOW_REGEX = OPTIONAL_DOWTIME_WINDOW
INVALID_DB_MAINT_WINDOW_MSG = "Must be hh:mm-hh:mm window or blank"

# Constants for hostnames
HOSTNAME_MSG = "Hostname of instances."
INVALID_HOSTNAME_MSG = ("This hostname does not follow the convention of: " +
                        "region-az-test|prod-app-kernel-fn-# " +
                        "Please see the documentation for additional "
                        "assistance.")

# Last updated - 21/3/14 - see either of the following
# http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-types.html
# http://aws.amazon.com/ec2/instance-types/

NAT_INSTANCE_TYPES = ["t2.small","t2.medium","m1.small","m1.medium",]

INSTANCE_TYPES = [
    # "general purpose"
    "t2.small",
    "t2.medium",
    "m1.small",
    "m1.medium",
    "m1.large",
    "m1.xlarge",
    "m3.medium",
    "m3.large",
    "m3.xlarge",
    "m3.2xlarge",
    # "compute optimized"
    "c1.medium",
    "c1.xlarge",
    "c3.large",
    "c3.xlarge",
    "c3.2xlarge",
    "c3.4xlarge",
    "c3.8xlarge",
    "cc2.8xlarge",
    # "New compute optimized"
    "c4.large",
    "c4.xlarge",
    "c4.2large",
    "c4.4xlarge",
    "c4.8large",
    # "memory optimized"
    "m2.xlarge",
    "m2.2xlarge",
    "m2.4xlarge",
    "cr1.8xlarge",
    "r3.large",
    "r3.xlarge",
    "r3.2xlarge",
    "r3.4xlarge",
    "r3.8xlarge",
    # "storage optimized"
    "hi1.4xlarge",
    "hs1.8xlarge",
    "i2.xlarge",
    "i2.2xlarge",
    "i2.4xlarge",
    "i2.8xlarge",
    "d2.xlarge",
    "d2.2xlarge",
    "d2.4xlarge",
    "d2.8xlarge",
    # "micro instances"
    "t1.micro",
    "t2.micro",
    # "gpu instances"
    "cg1.4xlarge",
    "g2.2xlarge"
]
INVALID_INSTANCE_TYPE_MSG = "Must be valid EC2 instance type xx.xxxxx"

# Last updated - 21/3/14 - see either of the following
# See AWS RDS User Guide: http://goo.gl/AmB8l

DB_INSTANCE_TYPES = [
    # "micro instances"
    "db.t1.micro",
    # "standard - second generation"
    "db.m3.medium",
    "db.m3.large",
    "db.m3.xlarge",
    "db.m3.2xlarge",
    # "standard - first generation"
    "db.m1.small",
    "db.m1.medium",
    "db.m1.large",
    "db.m1.xlarge",
    # "memory optimized"
    "db.m2.xlarge",
    "db.m2.2xlarge",
    "db.m2.4xlarge",
    "db.cr1.8xlarge",
]
INVALID_DB_INSTANCE_TYPE_MSG = "Must be valid RDS instance type db.xx.xxxx"
DEFAULT_DB_INSTANCE_TYPE = "db.m1.small"

"""
Last updated - 18/5/15 - these sometimes disappear
"""

AWS_NAT_AMI = {
    "eu-west-1":      { "AMI": "ami-6975eb1e" },
    "eu-west-2":      { "AMI": "ami-46073a5b" },
    "us-east-1":      { "AMI": "ami-303b1458" },
    "us-west-1":      { "AMI": "ami-7da94839" },
    "us-west-2":      { "AMI": "ami-69ae8259" },
    "sa-east-1":      { "AMI": "ami-fbfa41e6" },
    "ap-northeast-1": { "AMI": "ami-b49dace6" },
    "ap-southeast-1": { "AMI": "ami-03cf3903" },
    "ap-southeast-2": { "AMI": "ami-e7ee9edd" },
}

"""
Last updated - 4/14/14 - these often disappear!
See OpenVPN web page: http://goo.gl/cbgaW
"""

OPENVPN_AS_AMI = {
    "eu-west-1":      { "AMI": "ami-159b6162" },
    "us-east-1":      { "AMI": "ami-d34658ba" },
    "us-west-2":      { "AMI": "ami-8e4e24be" },  # oregon
    "us-west-1":      { "AMI": "ami-d08bb295" },
    "ap-southeast-1": { "AMI": "ami-80297ad2" }, # singapore
    "ap-southeast-2": { "AMI": "ami-077fe73d" },  # sydney
    "ap-northeast-1": { "AMI": "ami-e5364ee4" }, # tokyo
    "sa-east-1":      { "AMI": "ami-d73193ca" }
}

"""
Last updated - 4/17/14
"""

AWS_LINUX_AMI = {
    "eu-west-1":      { "AMI": "ami-a921dfde" },
    "us-east-1":      { "AMI": "ami-2f726546" },
    "us-west-2":      { "AMI": "ami-b8f69f88" },  # oregon
    "us-west-1":      { "AMI": "ami-84f1cfc1" },
    "ap-southeast-1": { "AMI": "ami-787c2c2a" }, # singapore
    "ap-southeast-2": { "AMI": "ami-0bc85031" },  # sydney
    "ap-northeast-1": { "AMI": "ami-a1bec3a0" }, # tokyo
    "sa-east-1":      { "AMI": "ami-89de7c94" }
}

AWS_MONGODB_AMI = {
    "eu-west-1":      { "AMI": "ami-5317c124" },
    "us-east-1":      { "AMI": "ami-f0ef2098" },
    "us-west-2":      { "AMI": "ami-cfd0a9ff" },  # oregon
    "us-west-1":      { "AMI": "ami-050a0940" },
    "ap-southeast-1": { "AMI": "ami-4ad78e18" }, # singapore
    "ap-southeast-2": { "AMI": "ami-87ec8bbd" },  # sydney
    "ap-northeast-1": { "AMI": "ami-01bcef00" }, # tokyo
    "sa-east-1":      { "AMI": "ami-dfec45c2" }
}

REGION_TO_AZ = {
        "us-west-1" : { "AZ" : ["us-west-1a", "us-west-1b", "us-west-1c"] }, # Needs to be checked!
        "us-east-1" : { "AZ" : ["us-east-1a", "us-east-1b", "us-east-1c", "us-east-1d"] },
        "us-west-2" : { "AZ" : ["us-west-2a", "us-west-2b", "us-west-2c"] },
        "eu-west-1" : { "AZ" : ["eu-west-1a", "eu-west-1b", "eu-west-1c"] }
}

if __name__ == "__main__":
    pass

