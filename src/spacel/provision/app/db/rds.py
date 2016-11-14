import logging
from botocore.exceptions import ClientError

from spacel.provision import clean_name, bool_param
from spacel.provision.app.db.base import BaseTemplateDecorator

logger = logging.getLogger('spacel.provision.rds.factory')

DEFAULT_VERSIONS = {
    'mysql': '5.7.10',
    'postgres': '9.5.2'
}

DEFAULT_PORTS = {
    'mysql': 3306,
    'postgres': 5432
}


class RdsFactory(BaseTemplateDecorator):
    def __init__(self, clients, ingress, passwords):
        super(RdsFactory, self).__init__(ingress)
        self._clients = clients
        self._passwords = passwords

    def add_rds(self, app, region, template):
        if not app.databases:
            logger.debug('No databases specified.')
            return

        params = template['Parameters']
        resources = template['Resources']
        app_name = app.name
        orbit_name = app.orbit.name

        user_data = self._user_data(resources)
        db_intro = user_data.index('"databases":{') + 1

        added_databases = 0
        secret_params = {}
        iam_statements = []
        for name, db_params in app.databases.items():
            password_label = 'rds:%s' % name
            rds_resource = 'Db%s' % clean_name(name)

            db_global = db_params.get('global')
            if db_global and db_global != region:
                # If connecting to a global DB, query for stored password:
                encrypted, _ = \
                    self._passwords.get_password(app, region, password_label,
                                                 generate=False)
                if not encrypted:
                    continue

                rds_id = self._rds_id(app, db_global, rds_resource)
                if not rds_id:
                    continue
                iam_statements.append({
                    'Effect': 'Allow',
                    'Action': 'rds:DescribeDBInstances',
                    'Resource': {'Fn::Join': ['', [
                        'arn:aws:rds:%s:' % db_global,
                        {'Ref': 'AWS::AccountId'},
                        ':db:%s' % rds_id
                    ]]}
                })

                user_data.insert(db_intro, ',')
                user_data.insert(db_intro, ',"region": "%s"}' % db_global)
                user_data.insert(db_intro,
                                 '","password": %s' % encrypted.json())
                user_data.insert(db_intro, rds_id)
                user_data.insert(db_intro, '"%s":{"name":"' % name)
                added_databases += 1

                continue

            db_type = db_params.get('type', 'postgres')

            db_version = db_params.get('version', DEFAULT_VERSIONS.get(db_type))
            if not db_version:
                logger.warning('Database "%s" has invalid "version".', name)
                continue

            db_port = db_params.get('port', DEFAULT_PORTS.get(db_type))
            if not db_port:
                logger.warning('Database "%s" has invalid "port".', name)
                continue

            instance_type = self._instance_type(db_params)
            multi_az = bool_param(db_params, 'multi_az', False)
            encrypted = bool_param(db_params, 'encrypted', False)
            storage_size = db_params.get('size', '5')
            storage_type = db_params.get('storage_type', 'gp2')
            storage_iops = db_params.get('iops', None)
            db_username = db_params.get('username', name)

            public = bool_param(db_params, 'public', False)
            db_subnet_group = '%sRdsSubnetGroup' % (public and 'Public'
                                                    or 'Private')

            rds_desc = '%s for %s in %s' % (name, app_name, orbit_name)
            logger.debug('Creating database "%s".', name)

            # Create a parameter for the database password:
            password_param = '%sPassword' % rds_resource
            params[password_param] = {
                'Type': 'String',
                'Description': 'Password for database %s' % name,
                'NoEcho': True
            }

            # Security group for database:
            rds_sg_resource = '%sSg' % rds_resource
            resources[rds_sg_resource] = {
                'Type': 'AWS::EC2::SecurityGroup',
                'Properties': {
                    'GroupDescription': rds_desc,
                    'VpcId': {'Ref': 'VpcId'},
                    'SecurityGroupIngress': [{
                        'IpProtocol': 'tcp',
                        'FromPort': db_port,
                        'ToPort': db_port,
                        'SourceSecurityGroupId': {'Ref': 'Sg'}
                    }]
                }
            }

            rds_params = {
                'AllocatedStorage': storage_size,
                'AllowMajorVersionUpgrade': False,
                'AutoMinorVersionUpgrade': True,
                'DBInstanceClass': instance_type,
                'DBName': name,
                'DBSubnetGroupName': {'Ref': db_subnet_group},
                'Engine': db_type,
                'EngineVersion': db_version,
                'MasterUsername': db_username,
                'MasterUserPassword': {'Ref': password_param},
                'MultiAZ': multi_az,
                'Port': db_port,
                'PubliclyAccessible': public,
                'StorageEncrypted': encrypted,
                'StorageType': storage_type,
                'VPCSecurityGroups': [{'Ref': rds_sg_resource}]
            }

            if storage_iops:
                rds_params['Iops'] = storage_iops
                if storage_type != 'io1':
                    logger.warning('Overriding "storage_type" of "%s": ' +
                                   '"iops" requires io1.', name)
                    rds_params['StorageType'] = 'io1'

            # Workaround for the instance_type default not supporting crypt
            # Other t2's fail, but at least that's the user's fault.
            if encrypted and instance_type == 'db.t2.micro':
                logger.warning('Overriding "instance_type" of "%s": ' +
                               '"encrypted" requires t2.large".', name)
                rds_params['DBInstanceClass'] = 'db.t2.large'

            resources[rds_resource] = {
                'Type': 'AWS::RDS::DBInstance',
                'Properties': rds_params
            }

            encrypted, plaintext_func = \
                self._passwords.get_password(app, region, password_label)

            # If hosting a global DB, store the password in each region:
            if db_global:
                region_clients = []
                for other_region in app.regions:
                    if region == other_region:
                        continue
                    self._passwords.set_password(app, other_region,
                                                 password_label, plaintext_func)
                    region_clients.append(other_region)

                # Inject other regions into 'clients' list
                db_clients = db_params.get('clients')
                if db_clients is None:
                    db_params['clients'] = region_clients
                else:
                    db_clients += region_clients

            iam_statements.append({
                'Effect': 'Allow',
                'Action': 'rds:DescribeDBInstances',
                'Resource': {'Fn::Join': ['', [
                    'arn:aws:rds:%s:' % region,
                    {'Ref': 'AWS::AccountId'},
                    ':db:',
                    {'Ref': rds_resource},
                ]]}
            })

            # Inject a labeled reference to this cache replication group:
            # Read this backwards, and note the trailing comma.
            user_data.insert(db_intro, ',')
            user_data.insert(db_intro, ',"region": "%s"}' % region)
            user_data.insert(db_intro, '","password": %s' % encrypted.json())
            user_data.insert(db_intro, {'Ref': rds_resource})
            user_data.insert(db_intro, '"%s":{"name":"' % name)
            added_databases += 1

            self._add_client_resources(resources, app, region, db_port,
                                       db_params, rds_sg_resource)
            secret_params[password_param] = plaintext_func

        if iam_statements:
            resources['RdsPolicy'] = {
                'DependsOn': 'Role',
                'Type': 'AWS::IAM::Policy',
                'Properties': {
                    'PolicyName': 'DescribeRdsDatabases',
                    'Roles': [{'Ref': 'Role'}],
                    'PolicyDocument': {
                        'Statement': iam_statements
                    }
                }
            }

        if added_databases:
            del user_data[db_intro + (5 * added_databases) - 1]

        return secret_params

    def _rds_id(self, app, region, rds_resource):
        cloudformation = self._clients.cloudformation(region)
        stack_name = '%s-%s' % (app.orbit.name, app.name)
        try:
            resource = cloudformation.describe_stack_resource(
                StackName=stack_name,
                LogicalResourceId=rds_resource)
            return (resource['StackResourceDetail']
                    ['PhysicalResourceId'])
        except ClientError as e:
            e_message = e.response['Error'].get('Message', '')
            if 'does not exist' in e_message:
                logger.debug('App %s not found in %s in %s.', app.name,
                             app.orbit.name, region)
                return None
            raise e

    @staticmethod
    def _instance_type(params):
        instance_type = params.get('instance_type', 'db.t2.micro')
        if not instance_type.startswith('db.'):
            instance_type = 'db.' + instance_type
        return instance_type
