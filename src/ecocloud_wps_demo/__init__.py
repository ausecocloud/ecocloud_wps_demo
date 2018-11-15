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

    return config.make_wsgi_app()
