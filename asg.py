from common import *
import json


def find_asg(region: str):
    result = []
    client = boto3.client('autoscaling',  region_name=region)
    asgs = client.describe_auto_scaling_groups()['AutoScalingGroups']
    #pprint(asgs)
    for asg in asgs:
        res = {}
        tags = {}
        for tag in asg['Tags']:
            if tag['Key'] in TAGS_OWN:
                if tag['Value'] in TAGS_OWN[tag['Key']]:
                    tags[tag['Key']] = tag['Value']
        if set(tags.keys()) == set(TAGS_OWN.keys()):
            res['ID'] = asg['AutoScalingGroupARN']
            res['Type'] = 'ASG'
            res['Region'] = region
            res['Name'] = asg['AutoScalingGroupName']
            res['State'] = ResourceState.Real
            res['Params'] = {
                'DesiredCapacity': asg['DesiredCapacity'],
                'MaxSize': asg['MaxSize'],
                'MinSize': asg['MinSize']
            }
            result.append(res)
    return result


def scale_zero(region: str, resource):
    logger.info("Scale Down ASG: {}".format(resource['Name']))
    client = boto3.client('autoscaling',  region_name=region)
    client.update_auto_scaling_group(
        AutoScalingGroupName=resource['Name'],
        MinSize=0,
        MaxSize=0,
        DesiredCapacity=0
    )
    resource['State'] = ResourceState.Shutdown
    return resource


def scale_up(region: str, resource):
    saved_config = db_get_item(resource['ID'], 'ASG')
    client = boto3.client('autoscaling',  region_name=region)
    if saved_config:
        logger.info("Scale UP ASG: {}".format(resource['Name']))
        client.update_auto_scaling_group(
            AutoScalingGroupName=saved_config['Name'],
            MinSize=saved_config['Params']['MinSize'],
            MaxSize=saved_config['Params']['MaxSize'],
            DesiredCapacity=saved_config['Params']['DesiredCapacity']
        )
    resource['State'] = ResourceState.Started
    return resource
