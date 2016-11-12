#!/usr/bin/env python3


from spacel.aws import ClientCache
from spacel.main import setup_logging
from spacel.model import Orbit, SpaceApp
from spacel.model.orbit import NAME, REGIONS
from spacel.provision.app import SpaceElevatorAppFactory
from spacel.provision.orbit import SpaceElevatorOrbitFactory
from test_integ import ORBIT_NAME, ORBIT_REGIONS, APP_NAME

if __name__ == '__main__':
    setup_logging()
    clients = ClientCache()

    orbit = Orbit({
        NAME: ORBIT_NAME,
        REGIONS: ORBIT_REGIONS
    })
    app = SpaceApp(orbit, {
        NAME: APP_NAME
    })

    app_factory = SpaceElevatorAppFactory(clients, None, None, None)
    app_factory.delete_app(app)

    orbit_factory = SpaceElevatorOrbitFactory(clients, None, None, None, None,
                                              None)
    orbit_factory.delete_orbit(orbit)
