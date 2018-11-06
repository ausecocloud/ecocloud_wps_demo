from pyramid.view import view_config
from pyramid.wsgi import wsgiapp2

from pywps import Service

from ecocloud_wps_demo.processes.csv_spatial_extract import CSVSpatialExtract
from ecocloud_wps_demo.processes.spatial_subset import SpatialSubset


processes = [
    CSVSpatialExtract(),
    SpatialSubset(),
]


service = Service(processes, ['/etc/ecocloud/pywps.cfg'])


@view_config(route_name='wps')
@wsgiapp2
def wps_app(environ, start_response):
    response = service(environ, start_response)
    return response
