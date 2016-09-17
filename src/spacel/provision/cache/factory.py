import logging
from spacel.provision import clean_name

logger = logging.getLogger('spacel.provision.cache.factory')

REDIS_PORT = '6379'

# https://docs.aws.amazon.com/AmazonElastiCache/latest/UserGuide/SelectEngine.html
REDIS_VERSION = '2.8.24'


class CacheFactory(object):
    def __init__(self, ingress):
        self._ingress = ingress

    def add_caches(self, app, region, template, caches):
        if not caches:
            logger.debug('No caches specified.')
            return

        app_name = app.name
        orbit_name = app.orbit.name
        resources = template['Resources']

        # Get UserData components:
        user_data = (resources['Lc']
                     ['Properties']
                     ['UserData']
                     ['Fn::Base64']
                     ['Fn::Join'][1])
        # Find the breadcrumb for the cache map:
        cache_intro = user_data.index('"caches":{') + 1

        added_caches = 0
        for name, params in caches.items():
            # How many replicas?
            replicas = self._replicas(params)
            if replicas is None:
                logger.warn('Cache "%s" has invalid "replicas".', name)
                continue
            default_automatic_failover = replicas > 0
            automatic_failover = params.get('automatic_failover',
                                            default_automatic_failover)

            instance_type = self._instance_type(params, automatic_failover)
            redis_version = params.get('version', REDIS_VERSION)

            cache_resource = 'Cache%s' % clean_name(name)
            cache_desc = '%s for %s in %s' % (name, app_name, orbit_name)
            logger.debug('Creating cache "%s".', name)

            # Security group for cache:
            cache_sg_resource = '%sSg' % cache_resource
            resources[cache_sg_resource] = {
                'Type': 'AWS::EC2::SecurityGroup',
                'Properties': {
                    'GroupDescription': cache_desc,
                    # Trying to get a non-VPC instance
                    'VpcId': {'Ref': 'VpcId'},
                    'SecurityGroupIngress': [
                        {
                            'IpProtocol': 'tcp',
                            'FromPort': REDIS_PORT,
                            'ToPort': REDIS_PORT,
                            'SourceSecurityGroupId': {'Ref': 'Sg'}
                        }
                    ]
                }
            }

            # Cache:
            resources[cache_resource] = {
                'Type': 'AWS::ElastiCache::ReplicationGroup',
                'Properties': {
                    'AutomaticFailoverEnabled': automatic_failover,
                    'AutoMinorVersionUpgrade': True,
                    'CacheNodeType': instance_type,
                    'CacheSubnetGroupName': {'Ref': 'PrivateCacheSubnetGroup'},
                    'Engine': 'redis',
                    'EngineVersion': redis_version,
                    'NumCacheClusters': (1 + replicas),
                    'Port': REDIS_PORT,
                    'ReplicationGroupDescription': cache_desc,
                    'SecurityGroupIds': [{'Ref': cache_sg_resource}]
                }
            }

            # Inject a labeled reference to this cache replication group:
            # Read this backwards, and note the trailing comma.
            user_data.insert(cache_intro, ',')
            user_data.insert(cache_intro, '"')
            user_data.insert(cache_intro, {'Ref': cache_resource})
            user_data.insert(cache_intro, '"%s":"' % name)
            added_caches += 1

            clients = params.get('clients', ())
            ingress_resources = \
                self._ingress.ingress_resources(app.orbit,
                                                region,
                                                6379,
                                                clients,
                                                sg_ref=cache_sg_resource)
            resources.update(ingress_resources)

        # If we added any caches, remove trailing comma:
        if added_caches:
            del user_data[cache_intro + (4 * added_caches) - 1]

    @staticmethod
    def _replicas(params):
        replicas = params.get('replicas', 0)
        try:
            return int(replicas)
        except ValueError:
            return None

    @staticmethod
    def _instance_type(params, automatic_failover):
        default_instance_type = (automatic_failover and 'cache.m3.medium'
                                 or 'cache.t2.micro')
        instance_type = params.get('instance_type', default_instance_type)
        if not instance_type.startswith('cache.'):
            instance_type = 'cache.' + instance_type
        return instance_type
