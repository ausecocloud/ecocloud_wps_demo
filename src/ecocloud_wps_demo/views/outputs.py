import os
import os.path

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from swiftclient.utils import generate_temp_url
from pywps import configuration as config


@view_config(route_name='outputs')
def outputs(request):
    # TODO: maybe use server:outputpath here?
    container = config.get_config_value('SwiftStorage', 'container')
    # TODO: TEM_PURL_KEY not needed in pywps
    temp_url_key = config.get_config_value('SwiftStorage', 'TEMP_URL_KEY')

    path_prefix = '/v1/AUTH_{}/{}/'.format(os.environ['OS_PROJECT_ID'], container)
    temp_url = generate_temp_url(
        path=path_prefix + '/'.join(request.matchdict['filename']),
        seconds=60 * 60 * 24,  # temp url valid for 24hrs
        key=temp_url_key,
        method='GET',
        # prefix=True,
        # iso8601=True,
        # ip_range=???
    )
    return HTTPFound(location='https://swift.rc.nectar.org.au' + temp_url)
