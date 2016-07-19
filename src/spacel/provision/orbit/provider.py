import logging

from spacel.model.orbit import PROVIDER
from spacel.provision.orbit.gdh import GitDeployHooksOrbitFactory
from spacel.provision.orbit.space import SpaceElevatorOrbitFactory

logger = logging.getLogger('spacel')


class ProviderOrbitFactory(object):
    """
    Constructs orbital VPCs according to providers.
    """

    def __init__(self, providers):
        self._providers = providers

    def get_orbit(self, orbit):
        for region in orbit.regions:
            provider_name = orbit.get_param(region, PROVIDER)

            provider = self._providers.get(provider_name)
            if not provider:
                logger.warn('Unknown provider: %s', provider_name)
                return None

            return provider.get_orbit(orbit)

    @staticmethod
    def get(clients, templates):
        return ProviderOrbitFactory({
            'spacel': SpaceElevatorOrbitFactory(clients, templates),
            'gdh': GitDeployHooksOrbitFactory(clients, 'git-deploy')
        })
