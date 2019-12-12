#!/usr/bin/env python3
from config import *
import asg
import ec2
import rds
from common import *
from pprint import pprint, pformat
import sys
import time


def clear_db(region, res_type, resources):
    present_ids = []
    if len(resources) > 0:
        present_ids = [sub['ID'] for sub in resources]
    db_ids = db_get_region_ids_by_type(region, res_type)
    clear_ids = list(set(db_ids) - set(present_ids))
    for id in clear_ids:
        db_delete_item(id, res_type)


def stop():
    db_backup()
    for region in aws_get_ec2_regions():
        logger.info("Stop resources for region: {}".format(region))
        
        # ASG scale to 0
        resources = asg.find_asg(region)
        for res in resources:
            db_item = db_get_item(res['ID'], 'ASG')
            if (not db_item) or db_item['State'] != ResourceState.Shutdown:
                db_save_resource(res)
            db_item = db_get_item(res['ID'], 'ASG')
            resp = asg.scale_zero(region, db_item)
            db_save_resource(resp)
        # clear non-existing resources
        clear_db(region, 'ASG', resources)

        # EC2 shutdown
        resources = ec2.find_ec2(region)
        for res in resources:
            db_item = db_get_item(res['ID'], 'EC2')
            if (not db_item) or db_item['State'] != ResourceState.Shutdown:
                db_save_resource(res)
            db_item = db_get_item(res['ID'], 'EC2')
            resp = ec2.instance_stop(region, db_item)
            db_save_resource(resp)
        # clear non-existing resources
        clear_db(region, 'EC2', resources)

    for region in aws_get_ec2_regions():
        # RDS stop
        resources = rds.find_rds(region)
        for res in resources:
            db_item = db_get_item(res['ID'], 'RDS')
            if (not db_item) or db_item['State'] != ResourceState.Shutdown:
                db_save_resource(res)
            db_item = db_get_item(res['ID'], 'RDS')
            resp = rds.instance_stop(region, db_item)
            db_save_resource(resp)
        # clear non-existing resources
        clear_db(region, 'RDS', resources)


def start():
    rds_exists = False
    for region in aws_get_ec2_regions():
        logger.info("Start RDS for region: {}".format(region))
        resources = rds.find_rds(region)
        for res in resources:
            db_item = db_get_item(res['ID'], 'RDS')
            if db_item and db_item['State'] == ResourceState.Shutdown:
                rds_exists = True
                resp = rds.instance_start(region, db_item)
                db_save_resource(resp)
        # clear non-existing resources
        clear_db(region, 'RDS', resources)

    if rds_exists:
        logger.info("RDS found. Sleep {} second before continue".format(RDS_WAIT_TIME))
        time.sleep(RDS_WAIT_TIME)

    for region in aws_get_ec2_regions():
        logger.info("Start resources for region: {}".format(region))

        # EC2 start
        resources = ec2.find_ec2(region)
        for res in resources:
            db_item = db_get_item(res['ID'], 'EC2')
            if db_item and db_item['State'] == ResourceState.Shutdown:
                resp = ec2.instance_start(region, db_item)
                db_save_resource(resp)
        # clear non-existing resources
        clear_db(region, 'EC2', resources)

        # ASG scale up
        resources = asg.find_asg(region)
        for res in resources:
            db_item = db_get_item(res['ID'], 'ASG')
            if db_item and db_item['State'] == ResourceState.Shutdown:
                resp = asg.scale_up(region, db_item)
                db_save_resource(resp)
        # clear non-existing resources
        clear_db(region, 'ASG', resources)


def info():
    for region in aws_get_ec2_regions():
        res = asg.find_asg(region)
        temp_arr = []
        for resource in res:
            temp_arr.append({'ID': resource['ID'], 'Name': resource['Name']})
        logger.info("ASG will be handled by app in region {}: \n{}".format(region,pformat(temp_arr)))

        res = ec2.find_ec2(region)
        temp_arr = []
        for resource in res:
            temp_arr.append({'ID': resource['ID'], 'Name': resource['Name']})
        logger.info("EC2 will be handled by app in region {}: \n{}".format(region, pformat(temp_arr)))

        res = rds.find_rds(region)
        temp_arr = []
        for resource in res:
            temp_arr.append({'ID': resource['ID'], 'Name': resource['Name']})
        logger.info("RDS will be handled by app in region {}: \n{}".format(region, pformat(temp_arr)))


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("Usage: app.py <start/stop/info>")
        exit(0)
    dynamodb_tables = get_dynamodb_tables()
    if DYNAMODB_TABLE not in dynamodb_tables:
        create_dynamodb(DYNAMODB_TABLE)
    if sys.argv[1] == "info":
        info()
    elif sys.argv[1] == "start":
        start()
    elif sys.argv[1] == "stop":
        stop()
    else:
        print("Usage: app.py <start/stop/info>")
#         pprint(db_get_region_ids_by_type('us-east-1', 'ASG'))
#    res = asg.find_asg('us-east-1')
#    asg.db_save(res)
#    asg.zero_scale('us-east-1', 'cww-k8s-worker-dev-spot-nat')
#    asg.scale_up('us-east-1', 'arn:aws:autoscaling:us-east-1:338870042854:autoScalingGroup:2d530adb-61c6-41bd-8eba-82e2472db106:autoScalingGroupName/cww-k8s-worker-dev-spot-nat')
#    pprint(ec2.find_ec2('us-east-1'))

