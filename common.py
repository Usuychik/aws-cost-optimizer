from config import *
import boto3
import decimal
import json
from enum import IntEnum
from boto3.dynamodb.conditions import Key, Attr
from pprint import pprint
from datetime import datetime, timedelta

class ResourceState(IntEnum):
    Real = 0
    Started = 1
    Shutdown = 2


# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


def aws_get_ec2_regions():
    regions = []
    client = boto3.client('ec2', region_name=DYNAMODB_REGION)
    regions = [region['RegionName'] for region in client.describe_regions()['Regions']]
    return regions


def get_dynamodb_tables():
    dynamodb = boto3.client('dynamodb', region_name=DYNAMODB_REGION)
    return dynamodb.list_tables()['TableNames']


def create_dynamodb(dbname: str):
    dynamodb = boto3.client('dynamodb', region_name=DYNAMODB_REGION)
    table = dynamodb.create_table(
        TableName=dbname,
        BillingMode='PAY_PER_REQUEST',
        KeySchema=[
            {
                'AttributeName': 'ID',
                'KeyType': 'HASH'  # Partition key
            },
            {
                'AttributeName': 'Type',
                'KeyType': 'RANGE'  # Sort key
            }

        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'ID',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'Type',
                'AttributeType': 'S'
            },
        ]
    )
    table.meta.client.get_waiter('table_exists').wait(TableName=dbname)


def db_backup():
    dynamodb = boto3.client('dynamodb', region_name=DYNAMODB_REGION)
    dynamodb.create_backup(
        TableName=DYNAMODB_TABLE,
        BackupName=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    )

def db_save_resource(resource):
    dynamodb = boto3.resource('dynamodb', region_name=DYNAMODB_REGION).Table(DYNAMODB_TABLE)
    #Save dict params as string
    resource['Params'] = json.dumps(resource['Params'])
    dynamodb.put_item(Item=resource)


def db_get_item(id, resource_type):
    dynamodb = boto3.resource('dynamodb', region_name=DYNAMODB_REGION).Table(DYNAMODB_TABLE)
    response = dynamodb.get_item(
        Key={
            'ID': id,
            'Type': resource_type
        }
    )
    if 'Item' not in response:
        return {}
    res = response['Item']
    res['Params'] = json.loads(res['Params'])
    return res


def db_get_resources_by_type(resource_type):
    dynamodb = boto3.resource('dynamodb', region_name=DYNAMODB_REGION).Table(DYNAMODB_TABLE)
    response = dynamodb.scan(FilterExpression=Attr('Type').eq(resource_type))
    items = []
    if 'Items' in response:
        for item in response['Items']:
            res = item
            res['Params'] = json.loads(item['Params'])
            items.append(res)
    return items


def db_get_ids_by_type(resource_type):
    dynamodb = boto3.resource('dynamodb', region_name=DYNAMODB_REGION).Table(DYNAMODB_TABLE)
    response = dynamodb.scan(FilterExpression=Attr('Type').eq(resource_type), ProjectionExpression='ID')
    items = []
    if 'Items' in response:
        for item in response['Items']:
            items.append(item['ID'])
    return items


def db_get_region_ids_by_type(region, resource_type):
    dynamodb = boto3.resource('dynamodb', region_name=DYNAMODB_REGION).Table(DYNAMODB_TABLE)
    response = dynamodb.scan(FilterExpression=Attr('Type').eq(resource_type) & Attr('Region').eq(region), ProjectionExpression='ID')
    items = []
    if 'Items' in response:
        for item in response['Items']:
            items.append(item['ID'])
    return items


def db_delete_item(id, res_type):
    dynamodb = boto3.resource('dynamodb', region_name=DYNAMODB_REGION).Table(DYNAMODB_TABLE)
    dynamodb.delete_item(Key={'ID': id, 'Type': res_type})
