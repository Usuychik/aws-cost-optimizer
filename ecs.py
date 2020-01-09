from common import *
from config import *


def find_ecs(region: str):
    result = []
    client = boto3.client('ecs', region_name=region)
    response = client.list_clusters()
    for cluster_arn in response['clusterArns']:
        cluster = client.describe_clusters(clusters=[cluster_arn],include=['TAGS'])['clusters'][0]
        res = {}
        tags = {}
        exclude = False
        for tag in cluster['tags']:
            if tag['key'] in TAGS_EXCLUDE:
                exclude = True
            if tag['key'] in TAGS_OWN:
                if tag['value'] in TAGS_OWN[tag['key']]:
                    tags[tag['key']] = tag['value']
        if set(tags.keys()) == set(TAGS_OWN.keys()):
            res['ID'] = cluster['clusterArn']
            res['Type'] = 'ECS'
            res['Region'] = region
            res['Name'] = cluster['clusterName']
            res['State'] = ResourceState.Real
            services = []
            res_services = []
            resp = client.list_services(cluster=res['ID'])
            services = services + resp['serviceArns']
            while 'nextToken' in resp:
                resp = client.list_services(cluster=res['ID'], nextToken=resp['nextToken'])
                services = services + resp['serviceArns']

            for service in services:
                srv = client.describe_services(cluster=res['ID'], services=[service])['services'][0]
                res_services.append({
                    'ServiceArn': srv['serviceArn'],
                    'ServiceName': srv['serviceName'],
                    'DesiredCount': srv['desiredCount'],
                    'taskDefinition': srv['taskDefinition'].split("/")[1]
                })

            res['Params'] = {
                'Status': cluster['status'],
                'Services': res_services
            }
            if exclude:
                print("Excluded recourse: \n{}".format(pformat(res)))
            else:
                result.append(res)
    return result


def scale_zero(region: str, resource):
    logger.info("Scale down ECS: {}".format(resource['Name']))
    client = boto3.client('ecs',  region_name=region)
    for service in resource['Params']['Services']:
        if service['DesiredCount'] != 0:
            client.update_service(cluster=resource['Name'], service=service['ServiceName'], desiredCount=0)
    resource['State'] = ResourceState.Shutdown
    return resource


def scale_up(region: str, resource):
    logger.info("Scale up ECS: {}".format(resource['Name']))
    client = boto3.client('ecs',  region_name=region)
    for service in resource['Params']['Services']:
        if service['DesiredCount'] != 0:
            client.update_service(cluster=resource['Name'], service=service['ServiceName'], desiredCount=service['DesiredCount'])
    resource['State'] = ResourceState.Started
    return resource
