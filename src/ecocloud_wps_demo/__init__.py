import os.path

from pyramid.config import Configurator

from pywps import configuration as wpsconfig


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)

    # app specific stuff
    config.add_route(name='wps', pattern='/wps')
    config.add_route(name='outputs', pattern='/outputs/*filename')
    config.add_route(name='status', pattern='/status/*filename')

    # web routes
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')

    config.scan('.views')

    # ensure paths exist
    for name in ('workdir', 'statuspath', 'outputpath'):
        dirname = os.path.abspath(wpsconfig.get_config_value('server', name))
        if not os.path.exists(dirname):
            os.makedirs(dirname)

    # TODO: init swift container here?
    # initialize swift storage container if active
    if wpsconfig.get_config_value('server', 'storage') == 'SwiftStorage':
        from swiftclient.service import SwiftService, SwiftError
        swift = SwiftService()
        container = wpsconfig.get_config_value('SwiftStorage', 'container')
        try:
            stat = swift.stat(container)
        except SwiftError as e:
            # e.exception.http_status should be 404
            # create container
            res = swift.post(container)
            # res['success'] sholud be True
            stat = swift.stat(container)
        # we sholud have stat for container now
        from ecocloud_wps_demo.pywps.swiftstorage import get_temp_url_key
        cur_key = stat['headers'].get('x-container-meta-temp-url-key')
        temp_url_key = get_temp_url_key()
        if cur_key != temp_url_key:
            # setting temp_url_key
            res = swift.post(container, options={'meta': {'temp-url-key': temp_url_key}})
            # res['success'] == True

    return config.make_wsgi_app()
