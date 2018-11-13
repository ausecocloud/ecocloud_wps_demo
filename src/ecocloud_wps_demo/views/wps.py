from pyramid.view import view_config
from pyramid.wsgi import wsgiapp2

from pywps import Service

from ecocloud_wps_demo.processes.anuclim_daily_extract import ANUClimDailyExtract
from ecocloud_wps_demo.processes.spatial_subset_netcdf import SpatialSubsetNetcdf
from ecocloud_wps_demo.processes.spatial_subset_geotiff import SpatialSubsetGeotiff


processes = [
    ANUClimDailyExtract(),
    SpatialSubsetNetcdf(),
    SpatialSubsetGeotiff(),
]


service = Service(processes, ['/etc/ecocloud/pywps.cfg'])


@view_config(route_name='wps')
@wsgiapp2
def wps_app(environ, start_response):
    response = service(environ, start_response)
    return response
