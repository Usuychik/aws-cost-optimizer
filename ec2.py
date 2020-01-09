from common import *


def find_ec2(region: str):
    result = []
    client = boto3.resource('ec2',  region_name=region)
    instances = client.instances.all()
    for instance in instances:
        res = {}
        tags = {}
        name = ""
        asg_instance = False
        exclude = False
        for tag in instance.tags:
            if tag['Key'] == "aws:autoscaling:groupName":
                asg_instance = True
            if tag['Key'] in TAGS_EXCLUDE:
                exclude = True
            if tag['Key'] in TAGS_OWN:
                if tag['Value'] in TAGS_OWN[tag['Key']]:
                    tags[tag['Key']] = tag['Value']
            if tag['Key'] == 'Name':
                name = tag['Value']
        if asg_instance:
            continue
        if set(tags.keys()) == set(TAGS_OWN.keys()):
            res['ID'] = instance.id
            res['Type'] = 'EC2'
            res['Region'] = region
            res['Name'] = name
            res['State'] = ResourceState.Real
            res['Params'] = {
                'State': instance.state['Name'],
                'StateCode': instance.state['Code']
            }
            if exclude:
                print("Excluded recourse: \n{}".format(pformat(res)))
            else:
                result.append(res)
    return result


def instance_stop(region, resource):
    ec2 = boto3.resource('ec2', region_name=region)
    if resource['Params']['StateCode'] == 16:
        logger.info("Stop instance: id={}, name={}".format(resource['ID'], resource['Name']))
        instance = ec2.Instance(resource['ID'])
        instance.stop()
        resource['State'] = ResourceState.Shutdown
    return resource


def instance_start(region, resource):
    ec2 = boto3.resource('ec2', region_name=region)
    if resource['Params']['StateCode'] == 16 and resource['State'] == ResourceState.Shutdown:
        logger.info("Start instance: id={}, name={}".format(resource['ID'], resource['Name']))
        instance = ec2.Instance(resource['ID'])
        instance.start()
        resource['State'] = ResourceState.Started
    return resource
