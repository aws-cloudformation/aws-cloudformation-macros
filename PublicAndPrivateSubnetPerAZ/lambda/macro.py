import boto3
import copy


ec2 = boto3.client('ec2')

def handler(event, _):

    # Globals
    # region = event['region']
    # accountId = event['accountId']
    # transformId = event['transformId']
    # params = event['params']
    requestId = event['requestId']
    fragment = event['fragment']
    # templateParameterValues = event['templateParameterValues']

    # Retrieves availability zones for this region
    response = ec2.describe_availability_zones()
    AZs = response['AvailabilityZones']

    #Grab resources that need to be duplicated
    VPCPubSn1 = fragment['Resources']['VPCPubSn1']
    VPCPrivSn1 = fragment['Resources']['VPCPrivSn1']
    # PubSnRtAssoc1 = fragment['Resources']['VPCPubSn1RtAssoc']
    # PubSnRtAssoc1 = fragment['Resources']['VPCPrivSn1RtAssoc']

    #iterate and add new resources
    for i in range(1,len(AZs)+1): # Create a range from 1 - total number of AZs
        if i == 1:   # Only add resources if there is more than 1 AZ
            continue

        # Create new Public Subnet based of VPCPubSN1
        fragment['Resources']['VPCPubSn' + str(i)] = copy.deepcopy(VPCPubSn1)
        fragment['Resources']['VPCPubSn' + str(i)]['Properties']['CidrBlock']['Fn::Select'][0] = i - 1
        fragment['Resources']['VPCPubSn' + str(i)]['Properties']['AvailabilityZone']['Fn::Select'][0] = str(i - 1)

        # Create new Private Subnet based of VPCPrivSN1
        fragment['Resources']['VPCPrivSn' + str(i)] = copy.deepcopy(VPCPrivSn1)
        fragment['Resources']['VPCPrivSn' + str(i)]['Properties']['CidrBlock']['Fn::Select'][0] = len(AZs) + i - 1
        fragment['Resources']['VPCPrivSn' + str(i)]['Properties']['AvailabilityZone']['Fn::Select'][0] = str(i - 1)

        # Create Public RT Association
        fragment['Resources']['VPCPubSn' + str(i) + 'RtAssoc'] = {}
        fragment['Resources']['VPCPubSn' + str(i) + 'RtAssoc']['Type'] = 'AWS::EC2::SubnetRouteTableAssociation'
        fragment['Resources']['VPCPubSn' + str(i) + 'RtAssoc']['Properties'] = {}
        fragment['Resources']['VPCPubSn' + str(i) + 'RtAssoc']['Properties']['RouteTableId'] = {}
        fragment['Resources']['VPCPubSn' + str(i) + 'RtAssoc']['Properties']['RouteTableId']['Ref'] = 'VPCPubRt1'
        fragment['Resources']['VPCPubSn' + str(i) + 'RtAssoc']['Properties']['SubnetId'] = {}
        fragment['Resources']['VPCPubSn' + str(i) + 'RtAssoc']['Properties']['SubnetId']['Ref'] = 'VPCPubSn' + str(i)

        # Create Private RT Association
        fragment['Resources']['VPCPrivSn' + str(i) + 'RtAssoc'] = {}
        fragment['Resources']['VPCPrivSn' + str(i) + 'RtAssoc']['Type'] = 'AWS::EC2::SubnetRouteTableAssociation'
        fragment['Resources']['VPCPrivSn' + str(i) + 'RtAssoc']['Properties'] = {}
        fragment['Resources']['VPCPrivSn' + str(i) + 'RtAssoc']['Properties']['RouteTableId'] = {}
        fragment['Resources']['VPCPrivSn' + str(i) + 'RtAssoc']['Properties']['RouteTableId']['Ref'] = 'VPCPrivRt1'
        fragment['Resources']['VPCPrivSn' + str(i) + 'RtAssoc']['Properties']['SubnetId'] = {}
        fragment['Resources']['VPCPrivSn' + str(i) + 'RtAssoc']['Properties']['SubnetId']['Ref'] = 'VPCPrivSn' + str(i)

    r = {}
    r['requestId'] = requestId
    r['status'] = 'SUCCESS'
    r['fragment'] = fragment

    return r
