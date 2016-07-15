NAME = 'test'
REGION = 'us-east-1'
VPC_ID = 'vpc-123456'
IP_ADDRESS = '127.0.0.1'


def cf_outputs(outputs):
    return [{'OutputKey': k, 'OutputValue': v} for k, v in outputs.items()]
