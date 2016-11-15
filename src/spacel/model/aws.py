# https://github.com/pebble/vz-spacel-agent/blob/master/spacel-agent.yml
# see: plugins.ec2_publish.regions ; 'us-west-2' is automatic
VALID_REGIONS = (
    'us-west-2',
    'us-east-1',
    'eu-west-1',
    'ap-southeast-1',
    'sa-east-1',
    'ap-northeast-1'
)

INSTANCE_TYPES = (
    't2.nano'
)
