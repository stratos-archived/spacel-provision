import logging
from copy import deepcopy

import six

from spacel.model import (SpaceApp, SpaceDockerService, SpaceService,
                          SpaceServicePort)
from spacel.model.json.base import BaseJsonModelFactory, NAME, REGIONS, ALL

logger = logging.getLogger('spacel.model.json.app')


class SpaceAppJsonModelFactory(BaseJsonModelFactory):
    def app(self, orbit, params):
        name = params.get(NAME)
        regions = params.get(REGIONS, ())
        app = SpaceApp(orbit, name, regions)
        self._set_properties(app, params)

        self._services(app, params)
        self._files(app, params)
        self._spot(app, params)
        self._ports(app, params)

        return app

    def _services(self, app, params):
        merged_services = self._merged_map(app.regions, params, 'services')

        for region, app_region in app.regions.items():
            region_services = merged_services[region]
            for service_name, service_params in region_services.items():
                if not service_params:
                    continue

                if '.' not in service_name:
                    service_name += '.service'
                service_env = service_params.get('environment', {})
                unit_file = service_params.get('unit_file')
                if unit_file:
                    non_docker = SpaceService(service_name, unit_file,
                                              service_env)
                    app_region.services[service_name] = non_docker
                    continue

                docker_image = service_params.get('image')
                if docker_image:
                    ports = service_params.get('ports', {})
                    volumes = service_params.get('volumes', {})
                    docker = SpaceDockerService(service_name, docker_image,
                                                ports,
                                                volumes, service_env)
                    app_region.services[service_name] = docker
                    continue

                logger.warning('Invalid service: %s', service_name)

    def _files(self, app, params):
        merged_files = self._merged_map(app.regions, params, 'files')
        for region, app_region in app.regions.items():
            region_files = merged_files[region]
            for file_name, file_params in region_files.items():
                if file_params is None or file_params == {}:
                    continue
                app_region.files[file_name] = file_params

    @staticmethod
    def _spot(app, params):
        spot_from_all = params.get(ALL, {}).get('spot')
        for region, app_region in app.regions.items():
            spot = params.get(region, {}).get('spot', spot_from_all)
            if isinstance(spot, bool) and spot:
                app_region.spot = {}
            elif isinstance(spot, six.string_types) and bool(spot):
                app_region.spot = {}
            elif isinstance(spot, dict):
                app_region.spot = spot
            else:
                app_region.spot = None

    def _ports(self, app, params):
        merged_public_ports = self._merged_map(app.regions, params,
                                               'public_ports', default={80: {}})
        merged_private_ports = self._merged_map(app.regions, params,
                                                'private_ports')
        for region, app_region in app.regions.items():
            region_public_ports = merged_public_ports[region]
            for port, port_params in region_public_ports.items():
                app_region.public_ports[port] = SpaceServicePort(port,
                                                                 **port_params)

            app_region.private_ports = merged_private_ports[region]

    @staticmethod
    def _merged_map(regions, params, key, default=None):
        if default is None:
            default = {}
        merged = {}
        map_from_all = params.get(ALL, {}).get(key, default)
        for region in regions:
            map_from_region = params.get(region, {}).get(key, {})
            region_map = deepcopy(map_from_all)
            region_map.update(map_from_region)
            merged[region] = region_map

        return merged
