import csv
import datetime
import logging
import os

from pydap.client import open_url
import numpy as np

from pywps import Process
from pywps import ComplexInput, ComplexOutput, Format
from pywps.validator.mode import MODE

#from netCDF4 import Dataset


# Process instances need to be picklable, because they are deep copied for execution.
# Ideally we don't need deepcopy, but for now this is what pywps does.
# if necessary see https://docs.python.org/3/library/pickle.html#handling-stateful-objects
# to make a class picklable or see copyreg module.
class SpatialSubset(Process):
    def __init__(self):
        inputs = [
            ComplexInput(
                'dataset', 'NetCDF Dataset',
                supported_formats=[Format('application/x-ogc-dods')],
                min_occurs=0, max_occurs=1,
                # TODO: MODE.STRICT (or better anything greater than MODE.NONE may trigger a file download)
                mode=MODE.STRICT
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

        super(SpatialSubset, self).__init__(
            self._handler,
            identifier='spatial_subset',
            title='NetCDF data spatial subset',
            abstract="Subsets a given NetCDF dataset with given spatial data/geometry",
            version='1',
            metadata=[],
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=False)

    def _handler(self, request, response):
        # import pdb; pdb.set_trace()
        # Get the NetCDF file
        log = logging.getLogger("__name__")
        dataset_input = request.inputs['dataset'][0]  # Note that all input parameters require index access
        dataset_csv = request.inputs['csv'][0]

        csv_fp = open(dataset_csv.file, 'r')
        csv_reader = csv.reader(csv_fp)
        csv_header = next(csv_reader)
        csv_header_idx = {col: csv_header.index(col) for col in csv_header}
        if any(col not in csv_header for col in ('lat', 'lon', 'date')):
            raise Exception('Bad trait data: Missing lat/lon/date column')

        # open opendap dataset
        dataset = open_url(dataset_input.url)
        # fetch indices
        # TODO: go through dataset.keys() and inspect children attributes to identify
        #       variables and data
        #       e.g. data['lat'].attributes = {'standard_name': 'latitude'}
        lats = dataset['lat'][:].data
        lons = dataset['lon'][:].data
        times = dataset['time'][:].data
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

        # this is a GridType ... it has an array and mapping
        # e.g. rainfall['lwe_thickness_of_precipitation_amount'] or rainfall.array
        #      rainfall.maps .. ordered dict of coordinates ('time', 'lat', 'lon')
        #      or rainfall.dimensions as a short tuple
        rainfall = dataset['lwe_thickness_of_precipitation_amount']
        rainfall_data = rainfall['lwe_thickness_of_precipitation_amount']
        # append rainfall column
        csv_header.append('rainfall')

        # produce output file
        with open(os.path.join(self.workdir, 'out.csv'), 'w') as fp:
            csv_writer = csv.writer(fp)
            csv_writer.writerow(csv_header)
            # iterate through input csv
            for row in csv_reader:
                try:
                    edate = datetime.datetime.strptime(row[csv_header_idx['date']].strip(), '%d/%m/%Y').timestamp()
                    lat = float(row[csv_header_idx['lat']])
                    lon = float(row[csv_header_idx['lon']])
                    # TODO: should allow little buffer with cellsize to filter lat/lon
                    if lat < lat_min or lat > lat_max:
                        raise Exception('lat outside data area')
                    if lon < lon_min or lon > lon_max:
                        raise Exception('lon outside data area')
                    if edate < time_min or edate > time_max:
                        raise Exception('time outside data area')
                    # find data indices
                    edate_idx = int(np.abs(times - edate).argmin())
                    lat_idx = int(np.abs(lats - lat).argmin())
                    lon_idx = int(np.abs(lons - lon).argmin())
                    value = rainfall_data[edate_idx, lat_idx, lon_idx].data[0][0][0]
                    row.append(value)
                except Exception as e:
                    log.warn('Skipping Row: {}'.format(e))
                    continue
                csv_writer.writerow(row)
            response.outputs['output'].file = fp.name
        return response
