**DESCRIPTION**
aws-cost-optimizer can stop/start AWS resources based on Tags.
Currently it stop:
 - ECS tasks (scale to 0)
 - ASG (scale to 0)
 - EC2
 - RDS
 
 Stop flow: ECS -> ASG -> EC2 -> RDS
 
 Start flow: RDS -> EC2 -> ASG -> ECS
 
**CONFIGURATION**

Next *ENV* variables should be configured:

    *TAGS_OWN* - json-like string with Keys representing tags to search 
                 and Values should be list of possible tag values.
                 Keys are processed with AND operator
                 Values inside Key are processed with OR operator
     
     *DYNAMODB_TABLE* - table-name, which will be used for storing states
     
Example of *TAGS_OWN*
     
    TAGS_OWN={"Product":["TEST","test"],"Environment":["Development","DEV"]}
    
    it will look for all resources which have tag Product and tag Environment with values:
    "Test" or "test for Product and "Development" or "DEV" for Environment


**Example usage in GitLab CI/CD**

    stages:
      - info
      - task
    
    .worker_template:
      stage: info
      tags:
        - docker
      image: "usuychick/aws-start-stop:latest"
      script:
        - 'echo "TAGS_OWN: $TAGS_OWN"'
        - python3 -u  /opt/aws/app.py $TASK
    
    
    info_worker:
      extends:
        - .worker_template
      script:
        - 'echo "TAGS_OWN: $TAGS_OWN"'
        - python3 -u /opt/aws/app.py info
      only:
        - schedules
      variables:
        AWS_ACCESS_KEY_ID: $AWS_TEST_KEY
        AWS_SECRET_ACCESS_KEY: $AWS_TEST_SECRET
        TASK: info
    
    stop_worker:
      extends:
        - .worker_template
      stage: task
      only:
        variables:
          - $TASK == "stop"
      variables:
        AWS_ACCESS_KEY_ID: $AWS_TEST_KEY
        AWS_SECRET_ACCESS_KEY: $AWS_TEST_SECRET
    
    start_worker:
      extends:
        - .worker_template
      stage: task
      only:
        variables:
          - $TASK == "start"
      variables:
        AWS_ACCESS_KEY_ID: $AWS_TEST_KEY
        AWS_SECRET_ACCESS_KEY: $AWS_TEST_SECRET
