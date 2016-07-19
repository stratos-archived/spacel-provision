import sys
import logging

from spacel.aws import ClientCache

from spacel.model import SpaceApp, Orbit
from spacel.model.orbit import PRIVATE_NETWORK
from spacel.provision.orbit import ProviderOrbitFactory
from spacel.provision.provision import CloudProvisioner
from spacel.provision.templates import TemplateCache


def main(args):
    # FIXME: this is a stub for driving spacel-agent tests

    # These should be set outside the application repository
    orbit_params = {
        'regions': ('us-east-1',),
        'defaults': {
            PRIVATE_NETWORK: '10.200'
        }
    }
    orbit = Orbit('test', orbit_params)

    # These should be read from the application repository:
    app_params = {
        'hostnames': ('test.mycloudand.me',),
        # 'scheme': 'internal',
        'health_check': 'HTTP:9200/',
        'instance_type': 't2.nano',
        'instance_min': 1,
        'instance_max': 1,
        'services': {
            'elasticsearch': {
                'image': 'pwagner/elasticsearch-aws',
                'ports': {
                    9200: 9200,
                    9300: 9300
                },
                'volumes': {
                    '/mnt/esdata': '/usr/share/elasticsearch/data'
                }
            }
        },
        'public_ports': {
            9200: {
                'sources': ('24.212.219.139/32', '54.148.229.21/32')
            }
        },
        'private_ports': {
            9300: ['TCP']
        },
        'volumes': {
            'esdata': {
                'count': 2,
                'size': 10
            }
        }
    }
    app = SpaceApp('elasticsearch', orbit, app_params)

    clients = ClientCache()
    templates = TemplateCache()

    orbit_factory = ProviderOrbitFactory.get(clients, templates)
    orbit_factory.get_orbit(orbit)

    provisioner = CloudProvisioner(clients, templates)
    provisioner.app(app)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logging.getLogger('boto3').setLevel(logging.CRITICAL)
    logging.getLogger('botocore').setLevel(logging.CRITICAL)
    logging.getLogger('spacel').setLevel(logging.DEBUG)

    main(sys.argv)
