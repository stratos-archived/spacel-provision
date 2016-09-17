import logging
from spacel.provision import clean_name, bool_param
from spacel.provision.db.base import BaseTemplateDecorator

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
    def add_rds(self, app, region, template, databases):
        if not databases:
            logger.debug('No databases specified.')
            return

        params = template['Parameters']
        resources = template['Resources']
        app_name = app.name
        orbit_name = app.orbit.name

        user_data = self._user_data(resources)
        db_intro = user_data.index('"databases":{') + 1

        added_databases = 0
        for name, db_params in databases.items():
            db_global = db_params.get('global')
            if db_global and db_global != region:
                continue

            db_type = db_params.get('type', 'postgres')

            db_version = db_params.get('version', DEFAULT_VERSIONS.get(db_type))
            if not db_version:
                logger.warn('Database "%s" has invalid "version".', name)
                continue

            db_port = db_params.get('port', DEFAULT_PORTS.get(db_type))
            if not db_port:
                logger.warn('Database "%s" has invalid "port".', name)
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

            rds_resource = 'Db%s' % clean_name(name)
            rds_desc = '%s for %s in %s' % (name, app_name, orbit_name)
            logger.debug('Creating database "%s".', name)

            # Create a parameter for the database password:
            password_param = '%sPassword' % rds_resource
            params[password_param] = {
                'Type': 'String',
                'Description': 'Password for database %s' % name,
                'NoEcho': True,
                # FIXME: not this
                'Default': 'Writeme123'
            }

            # Security group for database:
            rds_sg_resource = '%sSg' % rds_resource
            resources[rds_sg_resource] = {
                'Type': 'AWS::EC2::SecurityGroup',
                'Properties': {
                    'GroupDescription': rds_desc,
                    'VpcId': {'Ref': 'VpcId'},
                    'SecurityGroupIngress': [
                        {
                            'IpProtocol': 'tcp',
                            'FromPort': db_port,
                            'ToPort': db_port,
                            'SourceSecurityGroupId': {'Ref': 'Sg'}
                        }
                    ]
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
                    logger.warn('Overriding "storage_type" of "%s": ' +
                                '"iops" requires io1.', name)
                    rds_params['StorageType'] = 'io1'

            # Workaround for the instance_type default not supporting crypt
            # Other t2's fail, but at least that's the user's fault.
            if encrypted and instance_type == 'db.t2.micro':
                logger.warn('Overriding "instance_type" of "%s": ' +
                            '"encrypted" requires t2.large".', name)
                rds_params['DBInstanceClass'] = 'db.t2.large'

            resources[rds_resource] = {
                'Type': 'AWS::RDS::DBInstance',
                'Properties': rds_params
            }

            # Inject a labeled reference to this cache replication group:
            # Read this backwards, and note the trailing comma.
            user_data.insert(db_intro, ',')
            user_data.insert(db_intro, '","region": "%s"}' % region)
            user_data.insert(db_intro, {'Ref': rds_resource})
            user_data.insert(db_intro, '"%s":{"name":"' % name)
            added_databases += 1

            self._add_client_resources(resources, app, region, db_port,
                                       db_params, rds_sg_resource)
        if added_databases:
            del user_data[db_intro + (4 * added_databases) - 1]

    @staticmethod
    def _instance_type(params):
        instance_type = params.get('instance_type', 'db.t2.micro')
        if not instance_type.startswith('db.'):
            instance_type = 'db.' + instance_type
        return instance_type
