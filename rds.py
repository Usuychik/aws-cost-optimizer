from common import *


def find_rds(region: str):
    result = []
    client = boto3.client('rds', region_name=region)
    response = client.describe_db_instances()

    for instance in response['DBInstances']:
        res = {}
        tags = {}
        rds_tags = client.list_tags_for_resource(ResourceName=instance['DBInstanceArn'])['TagList']
        for tag in rds_tags:
            if tag['Key'] in TAGS_OWN:
                if tag['Value'] in TAGS_OWN[tag['Key']]:
                    tags[tag['Key']] = tag['Value']
        if set(tags.keys()) == set(TAGS_OWN.keys()):
            res['ID'] = instance['DBInstanceArn']
            res['Type'] = 'RDS'
            res['Region'] = region
            res['Name'] = instance['DBInstanceIdentifier']
            res['State'] = ResourceState.Real
            res['Params'] = {
                'Status': instance['DBInstanceStatus']
            }
            result.append(res)
    return result


def instance_stop(region, resource):
    rds = boto3.client('rds', region_name=region)
    if resource['Params']['Status'] in ['available']:
        logger.info("Stop instance: id={}, name={}".format(resource['ID'], resource['Name']))
        rds.stop_db_instance(DBInstanceIdentifier=resource['Name'])
        resource['State'] = ResourceState.Shutdown
    return resource


def instance_start(region, resource):
    rds = boto3.client('rds', region_name=region)
    if resource['Params']['Status'] in ['available'] and resource['State'] == ResourceState.Shutdown:
        logger.info("Start instance: id={}, name={}".format(resource['ID'], resource['Name']))
        rds.start_db_instance(DBInstanceIdentifier=resource['Name'])
        resource['State'] = ResourceState.Started
    return resource
