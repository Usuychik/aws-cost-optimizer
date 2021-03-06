import os
import logging
import json

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

logging.basicConfig(format='%(asctime)s %(levelname)s [%(funcName)s] %(message)s')
logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)

# TAGS_OWN json_like list of tags
# TAGS_OWN={"Product":["CWW"],"Environment":["Development","DEV"]}
TAGS_OWN = json.loads(os.environ["TAGS_OWN"])
TAGS_EXCLUDE = json.loads(os.getenv("TAGS_EXCLUDE", '{"optimizer_exclude":""}'))
DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]
DYNAMODB_REGION = os.getenv("DYNAMODB_REGION", "us-east-1")
DB_BACKUP_KEEP_DAYS = int(os.getenv("DB_BACKUP_KEEP_DAYS", 14))
RDS_WAIT_TIME = int(os.getenv("RDS_WAIT_TIME", 600))
ECS_WAIT_TIME = int(os.getenv("ECS_WAIT_TIME", 300))
