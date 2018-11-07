import logging
import os
from glob import glob
from zipfile import ZipFile

from pywps import Process
from pywps import ComplexInput, LiteralInput, ComplexOutput, Format
from pywps.validator.mode import MODE

import ocgis

class SpatialSubset(Process):
    def __init__(self):
        inputs = [
            ComplexInput('dataset', 'NetCDF Dataset',
                         supported_formats=[Format('application/x-netcdf')],
                         min_occurs=0, max_occurs=1,
                         mode=MODE.STRICT),
            ComplexInput('shapefile', '.zip file representing ESRI Shapefile of geometry to use for subset',
                         supported_formats=[Format('application/zip')],
                         min_occurs=0, max_occurs=1,
                         # NOTE: No validator for ZIP files
                         mode=MODE.NONE),
            LiteralInput('variable', 'Variable to subset',
                         data_type='string'),
        ]

        outputs = [
            ComplexOutput('output', 'Metadata',
                          as_reference=True,
                          supported_formats=[Format('text/plain')]),
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
            status_supported=True)

    def _handler(self, request, response):
        # Get the NetCDF file
        # Note that all input parameters require index access
        dataset_input = request.inputs['dataset'][0]

        # Subset geometry
        geometry_zip_input = request.inputs['shapefile'][0]
        geometry_zip = ZipFile(geometry_zip_input.file)

        # Extract to subdirectory, pick out the SHP file
        geometry_dir = os.path.join(self.workdir, '_geometry')
        geometry_zip.extractall(path=geometry_dir)

        geometry_shp_file = glob(os.path.join(geometry_dir, '*.shp'))[0]

        # Name of the variable to subset
        data_variable = request.inputs['variable'][0].data

        # Use the given NetCDF file
        rd = ocgis.RequestDataset(dataset_input.file, data_variable)

        # Execute subset
        result = ocgis.OcgOperations(
            dataset=rd,
            geom=geometry_shp_file,
            output_format='nc',     # Outputs only NetCDF
            dir_output=self.workdir,
        ).execute()

        # Finish up by providing the path to the subsetted file
        response.outputs['output'].file = result

        return response
