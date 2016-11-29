import json
import logging
import os
from collections import defaultdict

from spacel.model import SpaceService
from spacel.model.json import SpaceAppJsonModelFactory

logger = logging.getLogger('spacel.model.files.app')


class SpaceAppFilesModelFactory(object):
    def __init__(self, root_dir='.'):
        self._root_dir = root_dir
        self._json_factory = SpaceAppJsonModelFactory()

    def app(self, orbit, path):
        space_dir = os.path.join(self._root_dir, path, '.space')
        print(space_dir)
        if not os.path.isdir(space_dir):
            logger.error('Path %s not found.', path)
            return None

        # Crawl filesystem for parameters:
        app_json = defaultdict(dict)
        systemd = defaultdict(dict)
        environment = defaultdict(dict)
        other_files = defaultdict(dict)
        for root, dirs, files in os.walk(space_dir):
            # Context from directory:
            space_subdir = root[len(space_dir):]
            if not space_subdir:
                region = None
            else:
                region = space_subdir[1:]

            for space_file in files:
                space_file_path = os.path.join(root, space_file)
                ext = os.path.splitext(space_file)[1]
                file_data = self._read(space_file_path)
                if space_file == 'app.json':
                    app_json[region] = json.loads(file_data)
                elif ext == '.service' or ext == '.timer':
                    systemd[region][space_file] = file_data
                elif ext == '.env':
                    environment[region][space_file[:-4]] = \
                        self._env_map(file_data)
                else:
                    other_files[region][space_file] = file_data

        # Merge any discovered JSON files:
        app_params = app_json[None]
        for region in orbit.regions.keys():
            region_app_json = app_json[region]
            if region_app_json:
                app_params[region] = region_app_json

        app = self._json_factory.app(orbit, app_params)

        # Splice in systemd/environment from filesystem:
        for region, app_region in app.regions.items():
            app_region_services = systemd[region]
            app_region_files = other_files[region]

            # Units defined globally and not overridden in a region:
            for service, unit_file in systemd[None].items():
                if service in app_region_services:
                    continue
                app_region.services[service] = SpaceService(service, unit_file)

            # Units defined in a region (including overrides):
            for service, unit_file in app_region_services.items():
                if not unit_file:
                    continue
                app_region.services[service] = SpaceService(service, unit_file)

            # Environments:
            global_env = environment[None]
            app_region_env = environment[region]
            for service_name, service in app_region.services.items():
                service_env = service.environment
                service_env.update(global_env.get(service_name, {}))
                service_env.update(app_region_env.get(service_name, {}))

            # Files defined globally:
            for file_name, file_data in other_files[None].items():
                if file_name in app_region_files:
                    continue
                app_region.files[file_name] = file_data
            # Files defined in region:
            for file_name, file_data in app_region_files.items():
                app_region.files[file_name] = file_data

        return app

    @staticmethod
    def _read(path):
        with open(path) as path_in:
            return path_in.read()

    @staticmethod
    def _env_map(file_data):
        env_map = {}
        for env_entry in file_data.split('\n'):
            if env_entry.startswith('#'):
                continue
            equals_pos = env_entry.find('=')
            if equals_pos < 0:
                continue
            env_map[env_entry[:equals_pos]] = env_entry[equals_pos + 1:]
        return env_map
