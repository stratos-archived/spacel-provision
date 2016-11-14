# spacel-provision

Space Elevator is a project to assist with launching general purpose applications into AWS.

The name is derived from Pebble's internal definition of an *orbit*: a multi-region tier of the deployment lifecycle (i.e. multiple orbits like "test" and "production" are expected).


## Features

* Docker on Debian 8 runtime.
* Public internet ELB applications.
* Private (orbit/region-only) ELB applications.
* Flexible firewalls: customize ports and limit ingress to specific IP blocks/applications.
* Configurable alarms: CloudWatch metrics to multiple endpoints: email, Slack or PagerDuty.
* Configurable scaling policy
* Cache support: Redis cluster, per region.
* Database support: public/private RDS, per region or global.
* ACM integration for Amazon-provided HTTPS.

## Usage

Spacel-provision requires an [orbit manifest](https://github.com/pebble/spacel-provision/tree/master/sample/orbit), and an [application manifest](https://github.com/pebble/spacel-provision/tree/master/sample/app).

The orbit manifest can be shared by multiple applications. Application manifests are unique to each application in an orbit.
In a continuous integration system, the orbit manifest lives on the CI server while the application manifest lives with each project.

Environment Variables:
* `LAMBDA_BUCKET` **REQUIRED** Name of S3 bucket for storing Lambda function code.
* `LAMBDA_REGION` **REQUIRED** Region of `LAMBDA_BUCKET`.
* `TEMPLATE_BUCKET` Name of S3 bucket for storing CloudFormation templates (if not specified, `LAMBDA_BUCKET` is used).
* `TEMPLATE_REGION` Region of `TEMPLATE_BUCKET` (if not specified, `LAMBDA_REGION` is used).
* `WEBHOOKS_PAGERDUTY` Default endpoint for PagerDuty notifications: should use PagerDuty [CloudWatch Integration](https://www.pagerduty.com/docs/guides/aws-cloudwatch-integration-guide/)
* `PAGERDUTY_API_KEY` API key for PagerDuty, for auto-registering PagerDuty services when applications are added.
* `SPACEL_AGENT_CHANNEL` Channel of [spacel-agent AMI](https://github.com/pebble/vz-spacel-agent) to use. This can be `stable` (default) or `latest`.


## Architecture

Orbits are instantiated as a single VPC, in whatever AWS regions they are active in.
Orbit VPCs saturate every AZ of their host region (i.e. an orbit VPC in a region with 3 AZs will have `3n` subnets).
There is no peering/VPNs linking the VPCs of an orbit together: regions are isolated by design.


Applications launched into an orbit run in an AutoscalingGroup, within that orbit's VPCs.
Applications run on [Debian 8 AMIs](https://github.com/pebble/vz-spacel-agent), which use a custom [agent](https://github.com/pebble/spacel-agent) to handle bootstrap behaviour.
Applications are defined as a collection of systemd units, with a bias towards units that wrap a Docker container. 


With the exception of KMS keys, all Orbit resources are provisioned via CloudFormation.
At it's core, spacel-provision is [CloudFormation templates](https://github.com/pebble/spacel-provision/tree/master/src/spacel/cloudformation), and Python logic to customize them.


## Console Access

Every region runs bastion host(s) as an SSH gateway for troubleshooting. These are the only internet-accessible SSH ports.
SSH keys are stored in DynamoDb, and must be updated in *each* region that an orbit uses.


To add an SSH key to an orbit, add an item to the `${orbit}-users` table:
```
{
    'name': {'S': 'yourname'},
    'keys': {'SS': ['ssh-rsa ....']}
}
```

To grant the user login permission, add an item in the `${orbit}-services` table:
```
{
    'name': {'S': 'someapp'},
    'admins': {'SS': ['yourname']}
}
```

The service name should match the `name` field of the app being deployed.
The string `SPACE_ELEVATOR_OPERATORS` is a special service name value with allows logging into _any_ instance in the orbit/region.
