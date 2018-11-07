import csv
import datetime
import logging
import os

from pydap.client import open_url
import numpy as np

from pywps import Process
from pywps import ComplexInput, ComplexOutput, LiteralInput, Format
from pywps.validator.mode import MODE

#from netCDF4 import Dataset

data = {
    'rainfall': {
        'url': 'http://dapds00.nci.org.au/thredds/dodsC/rr9/eMAST_data/ANUClimate/ANUClimate_v1-0_rainfall_daily_0-01deg_1970-2014',
        'variable' : 'lwe_thickness_of_precipitation_amount',
    },
    'temp_max': {
        'url': 'http://dapds00.nci.org.au/thredds/dodsC/rr9/eMAST_data/ANUClimate/ANUClimate_v1-1_temperature-max_daily_0-01deg_1970-2014',
        'variable': 'air_temperature',
    },
    'temp_min': {
        'url': 'http://dapds00.nci.org.au/thredds/dodsC/rr9/eMAST_data/ANUClimate/ANUClimate_v1-1_temperature-min_daily_0-01deg_1970-2014',
        'variable': 'air_temperature',
    },
    'vapour_pressure_mean': {
        'url': 'http://dapds00.nci.org.au/thredds/dodsC/rr9/eMAST_data/ANUClimate/ANUClimate_v1-1_vapour-pressure_daily_0-01deg_1970-2014',
        'variable': 'vapour_pressure',
    },
    'solar_radiation_mean': {
        'url': 'http://dapds00.nci.org.au/thredds/dodsC/rr9/eMAST_data/ANUClimate/ANUClimate_v1-1_solar-radiation_daily_0-01deg_1970-2014',
        'variable': 'solar_radiation',
    }
}


# Process instances need to be picklable, because they are deep copied for execution.
# Ideally we don't need deepcopy, but for now this is what pywps does.
# if necessary see https://docs.python.org/3/library/pickle.html#handling-stateful-objects
# to make a class picklable or see copyreg module.
class ANUClimDailyExtract(Process):
    def __init__(self):
        inputs = [
            LiteralInput(
                'variables', 'Variables to extract',
                data_type='string', min_occurs=1, max_occurs=len(data),
                mode=MODE.SIMPLE, allowed_values=list(data.keys()),
            ),
            ComplexInput(
                'csv', 'CSV occurrences with date',
                supported_formats=[Format('text/csv')],
                min_occurs=1, max_occurs=1,
                # There is no CSV validator, so we have to use None
                mode=MODE.NONE
            ),
        ]

        outputs = [
            ComplexOutput('output', 'Metadata',
                          as_reference=True,
                          supported_formats=[Format('text/csv')]),
        ]

        super(ANUClimDailyExtract, self).__init__(
            self._handler,
            identifier='anuclim_daily_extract',
            title='ANUClim daily climate data extract.',
            abstract="Extracts env variables at specific location and time from ANUClimate daily climate grids.",
            version='1',
            metadata=[],
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            # TODO: birdy does not handle this? .. or rather if async call,
            #       birdy asks for status, but pywps process says no to it and fails the request
            status_supported=True)

    def _handler(self, request, response):
        # import pdb; pdb.set_trace()
        # Get the NetCDF file
        log = logging.getLogger(__name__)
        variables = [v.data for v in request.inputs['variables']]  # Note that all input parameters require index access
        dataset_csv = request.inputs['csv'][0]

        csv_fp = open(dataset_csv.file, 'r')
        csv_reader = csv.reader(csv_fp)
        csv_header = next(csv_reader)
        csv_header_idx = {col: csv_header.index(col) for col in csv_header}
        if any(col not in csv_header for col in ('lat', 'lon', 'date')):
            raise Exception('Bad trait data: Missing lat/lon/date column')

        # open opendap dataset
        datasets = {}
        for var in variables:
            # open dataset
            ds = open_url(data[var]['url'])
            # fetch index arrays and get min/max
            lats = ds['lat'][:].data
            lons = ds['lon'][:].data
            times = ds['time'][:].data
            lat_min = lats[0]
            lat_max = lats[-1]
            if lat_min > lat_max:
                lat_min, lat_max = lat_max, lat_min
            lon_min = lons[0]
            lon_max = lons[-1]
            if lon_min > lon_max:
                lon_min, lon_max = lon_max, lon_min
            time_min = times[0]
            time_max = times[-1]
            # get grid data
            grid = ds[data[var]['variable']]
            # TODO: could als use grid.array?
            #       also check grid.maps, and grid.dimensions to get axis order
            #          e.g. ('time', 'lat', 'lon')
            grid_data = grid[data[var]['variable']]
            # store data
            datasets[var] = {
              'ds': ds,
              'data': grid_data,
              'var': data[var]['variable'],
              'lats': lats,
              'lons': lons,
              'times': times,
              'lon_min': lon_min, 'lon_max': lon_max,
              'lat_min': lat_min, 'lat_max': lat_max,
              'time_min': time_min, 'time_max': time_max,
            }

        # append variables to csv header
        for var in variables:
            csv_header.append(var)

        # produce output file
        with open(os.path.join(self.workdir, 'out.csv'), 'w') as fp:
            csv_writer = csv.writer(fp)
            csv_writer.writerow(csv_header)
            # iterate through input csv
            for row in csv_reader:
                try:
                    # get coordinates from csv
                    edate = datetime.datetime.strptime(row[csv_header_idx['date']].strip(), '%Y-%m-%d').timestamp()
                    lat = float(row[csv_header_idx['lat']])
                    lon = float(row[csv_header_idx['lon']])
                    # TODO: should allow little buffer with cellsize to filter lat/lon
                    # FIXME: this check lat/lon min/max against last processed dataset
                    #        not a problem right now, because all variables have the same shape, but not ideal
                    if lat < lat_min or lat > lat_max:
                        raise Exception('lat outside data area')
                    if lon < lon_min or lon > lon_max:
                        raise Exception('lon outside data area')
                    if edate < time_min or edate > time_max:
                        raise Exception('time outside data area')
                    # find data indices
                    # FIXME: this get's data indices from last processed dataset
                    #        not a problem right now, because all variables have the same shape, but not ideal
                    edate_idx = int(np.abs(times - edate).argmin())
                    lat_idx = int(np.abs(lats - lat).argmin())
                    lon_idx = int(np.abs(lons - lon).argmin())
                    # extract data
                    for var in variables:
                        value = datasets[var]['data'][edate_idx, lat_idx, lon_idx]
                        row.append(value.data[0][0][0])
                except Exception as e:
                    log.warn('Filling Row with empty values: {}'.format(e))
                    for var in variables:
                        row.append('')
                csv_writer.writerow(row)
            # response.outputs['output'].file = fp.name
        response.outputs['output'].data = open(os.path.join(self.workdir, 'out.csv'), 'r').read()
        return response
