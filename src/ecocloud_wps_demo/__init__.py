from pyramid.config import Configurator


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)

    # app specific stuff
    config.add_route(name='wps', pattern='/wps')
    config.add_route(name='outputs', pattern='/outputs/*filename')

    # web routes
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')

    config.scan('.views')
    return config.make_wsgi_app()
