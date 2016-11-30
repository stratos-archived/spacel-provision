import json
import logging
import os
from collections import defaultdict

from spacel.model import SpaceService
from spacel.model.json import SpaceAppJsonModelFactory
from spacel.security import EncryptedPayload

logger = logging.getLogger('spacel.model.files.app')


class SpaceAppFilesModelFactory(object):
    """
    Constructs a SpaceApp from a directory hierarchy.
    """

    def __init__(self, root_dir='.'):
        self._root_dir = root_dir
        self._json_factory = SpaceAppJsonModelFactory()

    def app(self, orbit, path):
        """
        Construct SpaceApp.
        :param orbit: Orbit.
        :param path: Path for app descriptor(s).
        :return: SpaceApp; None if path not found.
        """
        space_dir = os.path.join(self._root_dir, path, '.space')
        if not os.path.isdir(space_dir):
            logger.error('Path %s not found.', path)
            return None

        # Crawl filesystem for parameters:
        app_json, environment, other_files, systemd = self._crawl(space_dir)

        # Build App based on merged JSON descriptor:
        app = self._app(orbit, app_json)

        # Mix-in other discovered files:
        self._splice(app, environment, other_files, systemd)

        return app

    def _crawl(self, space_dir):
        app_json = defaultdict(dict)  # app.json
        systemd = defaultdict(dict)  # *.service, *.timer
        env_files = defaultdict(dict)  # *.env
        other_files = defaultdict(dict)  # None of the above
        for root, dirs, files in os.walk(space_dir):
            # Context from directory:
            space_subdir = root[len(space_dir):]
            if not space_subdir:
                region = None
            else:
                region = space_subdir[1:]

            for space_file in files:
                ext = os.path.splitext(space_file)[1]
                file_data = self._read(os.path.join(root, space_file))
                if space_file == 'app.json':
                    app_json[region] = json.loads(file_data)
                    continue
                elif ext == '.env':
                    base_file = space_file[:-4]  # Trim ".env" suffix
                    env_files[region][base_file] = self._env_map(file_data)
                elif ext == '.crypt':
                    payload = EncryptedPayload.from_json(file_data)
                    if payload:
                        space_file = space_file[:-6]  # Trim ".crypt" suffix
                        ext = os.path.splitext(space_file)[1]
                        if ext == '.env':  # pragma: no cover
                            logger.warning('Encrypting full .env files (like' +
                                           ' %s) is not recommended, as local' +
                                           ' decryption is required to merge.',
                                           space_file)
                        file_data = payload.obj()

                if ext == '.service' or ext == '.timer':
                    systemd[region][space_file] = file_data
                else:
                    other_files[region][space_file] = file_data

        return app_json, env_files, other_files, systemd

    def _app(self, orbit, app_json):
        # Merge JSON files to a single SpaceApp descriptor:
        app_params = app_json[None]
        for region in orbit.regions.keys():
            region_app_json = app_json[region]
            if region_app_json:
                app_params[region] = region_app_json

        return self._json_factory.app(orbit, app_params)

    def _splice(self, app, environment, other_files, systemd):
        for region, app_region in app.regions.items():
            self._splice_units(region, app_region, systemd)
            self._splice_env(region, app_region, environment)
            self._splice_files(region, app_region, other_files)

    @staticmethod
    def _splice_units(region, app_region, systemd):
        app_region_services = systemd[region]
        for service, unit_file in systemd[None].items():
            if service in app_region_services:
                continue
            app_region.services[service] = SpaceService(service, unit_file)
        for service, unit_file in app_region_services.items():
            if not unit_file:
                continue
            app_region.services[service] = SpaceService(service, unit_file)

    @staticmethod
    def _splice_env(region, app_region, environment):
        global_env = environment[None]
        app_region_env = environment[region]
        for service_name, service in app_region.services.items():
            service_env = service.environment
            service_env.update(global_env.get(service_name, {}))
            service_env.update(app_region_env.get(service_name, {}))

    @staticmethod
    def _splice_files(region, app_region, other_files):
        app_region_files = other_files[region]
        for file_name, file_data in other_files[None].items():
            if file_name in app_region_files:
                continue
            app_region.files[file_name] = file_data
        for file_name, file_data in app_region_files.items():
            app_region.files[file_name] = file_data

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
