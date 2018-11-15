import os
import os.path

from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config
from pyramid.response import FileResponse

from pywps import configuration as config


@view_config(route_name='status')
def status(request):
    statuspath = os.path.abspath(config.get_config_value('server', 'statuspath'))
    filepath = os.path.abspath(os.path.join(statuspath, '/'.join(request.matchdict['filename'])))
    if not (filepath.startswith(statuspath) and os.path.exists(filepath)):
        raise HTTPNotFound()
    # serve status.xml
    response = FileResponse(filepath, request)
    return response
