import logging
from collections import defaultdict

from spacel.provision.orbit.gdh import GitDeployHooksOrbitFactory
from spacel.provision.orbit.space import SpaceElevatorOrbitFactory

logger = logging.getLogger('spacel.provision.orbit.provider')


class ProviderOrbitFactory(object):
    """
    Constructs orbital VPCs according to providers.
    """

    def __init__(self, providers):
        self._providers = providers

    def orbit(self, orbit):
        # Index regions by provider:
        provider_regions = defaultdict(list)
        for region, orbit_region in orbit.regions.items():
            provider = orbit_region.provider
            logger.debug('Orbit "%s" uses provider: %s', orbit.name, provider)
            provider_regions[provider].append(region)

        # Fire providers sequentially:
        logger.debug('Region provider map: %s', dict(provider_regions))
        for provider_name, provider_regions in provider_regions.items():
            provider = self._providers.get(provider_name)
            if not provider:
                logger.warning('Unknown provider: %s', provider_name)
                continue
            provider.orbit(orbit, regions=provider_regions)

    @staticmethod
    def get(clients, change_sets, uploader, vpc, bastion, tables):
        return ProviderOrbitFactory({
            'spacel': SpaceElevatorOrbitFactory(clients, change_sets, uploader,
                                                vpc, bastion, tables),
            'gdh': GitDeployHooksOrbitFactory(clients, change_sets, uploader)
        })
