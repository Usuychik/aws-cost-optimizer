from common import *
from config import *


def find_volumes(region: str):
    result = []
    ecs_resources = db_get_resources_by_type('ECS', region)
    tasks_name = []
    for ecs in ecs_resources:
        for service in ecs['Params']['Services']:
            tasks_name.append(service['taskDefinition'].rsplit('-', 1)[0])

    client = boto3.client('ec2',  region_name=region)
    volumes_dict = client.describe_volumes()
    for volume in volumes_dict['Volumes']:
        if volume['State'] != 'available':
            continue
        exclude = False
        if 'Tags' in volume:
            for tag in volume['Tags']:
                if tag['Key'] in TAGS_EXCLUDE:
                    exclude = True
                if tag['Key'] == 'Name':
                    for task in tasks_name:
                        if task in tag['Value']:
                            if exclude:
                                print("Excluded volume: {}".format(volume['VolumeId']))
                            else:
                                result.append(volume['VolumeId'])

    return result


def delete_volume(volume_id, region):
    logger.info("Delete volume {}".format(volume_id))
    ec2 = boto3.resource('ec2', region_name=region)
    volume = ec2.Volume(volume_id)
    volume.delete()
