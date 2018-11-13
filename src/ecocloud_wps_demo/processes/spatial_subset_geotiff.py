import logging
import os
from glob import glob
from zipfile import ZipFile

from pywps import Process
from pywps import ComplexInput, LiteralInput, ComplexOutput, Format
from pywps.validator.mode import MODE

import fiona
import rasterio
import rasterio.mask

class SpatialSubsetGeotiff(Process):
    def __init__(self):
        inputs = [
            ComplexInput('file', 'GeoTIFF file',
                         supported_formats=[Format('image/tiff')],
                         min_occurs=0, max_occurs=1,
                         # NOTE: Can't validate GeoTIFFs at the moment
                         mode=MODE.NONE),
            ComplexInput('shapefile', '.zip file representing ESRI Shapefile of geometry to use for subset',
                         supported_formats=[Format('application/zip')],
                         min_occurs=0, max_occurs=1,
                         # NOTE: No validator for ZIP files
                         mode=MODE.NONE),
        ]

        outputs = [
            ComplexOutput('output', 'Metadata',
                          as_reference=True,
                          supported_formats=[Format('text/plain')]),
        ]

        super(SpatialSubsetGeotiff, self).__init__(
            self._handler,
            identifier='spatial_subset_geotiff',
            title='GeoTIFF data spatial subset',
            abstract="Subsets a given GeoTIFF file with given spatial data/geometry",
            version='1',
            metadata=[],
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True)

    def _handler(self, request, response):
        # Get the GeoTIFF file
        # Note that all input parameters require index access
        file_input = request.inputs['file'][0]

        # Subset geometry
        geometry_zip_input = request.inputs['shapefile'][0]
        geometry_zip = ZipFile(geometry_zip_input.file)

        # Extract to subdirectory, pick out the SHP file
        geometry_dir = os.path.join(self.workdir, '_geometry')
        geometry_zip.extractall(path=geometry_dir)

        geometry_shp_file = glob(os.path.join(geometry_dir, '*.shp'))[0]

        # Use shapefile to mask (subset) GeoTIFF file
        # Most of this is from https://rasterio.readthedocs.io/en/latest/topics/masking-by-shapefile.html
        with fiona.open(geometry_shp_file, "r") as shapefile:
            features = [feature["geometry"] for feature in shapefile]
        
        with rasterio.open(file_input.file) as src:
            out_image, out_transform = rasterio.mask.mask(src, features, crop=True)
            out_meta = src.meta.copy()

        # Adjust metadata accordingly
        out_meta.update({
            "driver": "GTiff",
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform,
        })

        # Write output GeoTIFF file
        output_path = os.path.join(self.workdir, "subset.tif")

        with rasterio.open(output_path, "w", **out_meta) as dest:
            dest.write(out_image)

        # Finish up by providing the path to the subsetted file
        response.outputs['output'].file = output_path

        return response
