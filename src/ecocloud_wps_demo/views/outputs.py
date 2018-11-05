import os.path

from pyramid.view import view_config
from pyramid.response import FileResponse


@view_config(route_name='outputs')
def outputs(request):
    path = os.path.join('/tmp/', '/'.join(request.matchdict['filename']))
    response = FileResponse(path, request)
    return response
