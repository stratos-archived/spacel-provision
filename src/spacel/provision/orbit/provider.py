from collections import defaultdict
import logging

from spacel.model.orbit import PROVIDER
from spacel.provision.orbit.gdh import GitDeployHooksOrbitFactory
from spacel.provision.orbit.space import SpaceElevatorOrbitFactory

logger = logging.getLogger('spacel.provision.orbit.provider')


class ProviderOrbitFactory(object):
    """
    Constructs orbital VPCs according to providers.
    """

    def __init__(self, providers):
        self._providers = providers

    def get_orbit(self, orbit, regions=None):
        regions = regions or orbit.regions

        # Index regions by provider:
        provider_regions = defaultdict(list)
        for region in regions:
            provider_name = orbit.get_param(region, PROVIDER)
            logger.debug('Orbit "%s" uses provider: %s', orbit.name,
                         provider_name)
            provider_regions[provider_name].append(region)

        # Fire providers sequentially:
        logger.debug('Region provider map: %s', dict(provider_regions))
        for provider_name, provider_regions in provider_regions.items():
            provider = self._providers.get(provider_name)
            if not provider:
                logger.warn('Unknown provider: %s', provider_name)
                continue
            provider.get_orbit(orbit, regions=provider_regions)

    @staticmethod
    def get(clients, change_sets, templates):
        return ProviderOrbitFactory({
            'spacel': SpaceElevatorOrbitFactory(clients, change_sets,
                                                templates),
            'gdh': GitDeployHooksOrbitFactory(clients, change_sets,
                                              'git-deploy',
                                              'git-deploy-develop')
        })
