from pyramid.view import view_config
from pyramid.wsgi import wsgiapp2

from pywps import Service

from ecocloud_wps_demo.processes.anuclim_daily_extract import ANUClimDailyExtract
from ecocloud_wps_demo.processes.anuclim_daily_extract_netcdf4 import ANUClimDailyExtractNetCDF4
from ecocloud_wps_demo.processes.spatial_subset_geotiff import SpatialSubsetGeotiff
from ecocloud_wps_demo.processes.spatial_subset_netcdf import SpatialSubsetNetcdf
from ecocloud_wps_demo.processes.exploratory_data_box import ExploratoryDataBox
from ecocloud_wps_demo.processes.exploratory_data_histogram import ExploratoryDataHistogram


processes = [
    ANUClimDailyExtract(),
    ANUClimDailyExtractNetCDF4(),
    SpatialSubsetGeotiff(),
    SpatialSubsetNetcdf(),
    ExploratoryDataBox(),
    ExploratoryDataHistogram(),
]


service = Service(processes, ['/etc/ecocloud/pywps.cfg'])


@view_config(route_name='wps')
@wsgiapp2
def wps_app(environ, start_response):
    response = service(environ, start_response)
    return response
