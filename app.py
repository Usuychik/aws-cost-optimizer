#!/usr/bin/env python3
from config import *
import asg
import ec2
import rds
import ecs
from common import *
from pprint import pprint, pformat
import sys
import time
import logging


def print_info(resources, type, region):
    temp_arr = []
    for resource in resources:
        temp_arr.append({'ID': resource['ID'], 'Name': resource['Name']})
    if len(temp_arr) > 0:
        logger.info("{} will be handled by app in region {}: \n{}".format(type,region, pformat(temp_arr)))


def stop():
    db_backup()
    ecs_exists = False
    for region in aws_get_ec2_regions():
        logger.info("Stop ECS for region: {}".format(region))
        resources = ecs.find_ecs(region)
        for res in resources:
            db_item = db_get_item(res['ID'], 'ECS')
            if (not db_item) or db_item['State'] != ResourceState.Shutdown:
                db_save_resource(res)
            db_item = db_get_item(res['ID'], 'ECS')
            resp = ecs.scale_zero(region, db_item)
            db_save_resource(resp)
            ecs_exists = True
        # clear non-existing resources
        clear_db(region, 'ECS', resources)

    if ecs_exists:
        logger.info("ECS found. Sleep {} seconds before continue".format(ECS_WAIT_TIME))
        time.sleep(ECS_WAIT_TIME)

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
        logger.info("RDS found. Sleep {} seconds before continue".format(RDS_WAIT_TIME))
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

        # ECS scale up
        resources = ecs.find_ecs(region)
        for res in resources:
            db_item = db_get_item(res['ID'], 'ECS')
            if db_item and db_item['State'] == ResourceState.Shutdown:
                resp = ecs.scale_up(region, db_item)
                db_save_resource(resp)
        # clear non-existing resources
        clear_db(region, 'ECS', resources)


def info():
    for region in aws_get_ec2_regions():
        res = ecs.find_ecs(region)
        print_info(res, 'ECS', region)

        res = asg.find_asg(region)
        print_info(res, 'ASG', region)

        res = ec2.find_ec2(region)
        print_info(res, 'EC2', region)

        res = rds.find_rds(region)
        print_info(res, 'RDS', region)


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
