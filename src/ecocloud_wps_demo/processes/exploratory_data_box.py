import logging
import os
from glob import glob
from zipfile import ZipFile

from pywps import Process
from pywps import ComplexInput, LiteralInput, ComplexOutput, Format
from pywps.validator.mode import MODE

import pandas as pd
import matplotlib
import matplotlib.pyplot as plt


class ExploratoryDataBox(Process):
    def __init__(self):
        inputs = [
            ComplexInput(
                'csv', 'Data in CSV format, with variables in the first row',
                supported_formats=[Format('text/csv')],
                min_occurs=1, max_occurs=1,
                # There is no CSV validator, so we have to use None
                mode=MODE.NONE
            ),
            LiteralInput(
                'variable', 'Variable to plot',
                data_type='string', min_occurs=1, max_occurs=4,
                mode=MODE.SIMPLE
            ),
        ]

        outputs = [
            ComplexOutput('output', 'Output data',
                          as_reference=True,
                          supported_formats=[Format('image/png')]),
        ]

        super(ExploratoryDataBox, self).__init__(
            self._handler,
            identifier='exploratory_data_box',
            title='Exploratory data: Box plot',
            abstract='Generates box plots from one or more variables in the provided CSV dataset',
            version='1',
            metadata=[],
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True)

    def _handler(self, request, response):
        # Extract inputs
        csv_filepath = request.inputs['csv'][0].file
        variables = [v.data for v in request.inputs['variable']]
        variables_count = len(variables)

        # Plot into subplots, one per variable
        figure = plt.figure()

        # Read only the columns we need from the CSV
        csv_df = pd.read_csv(csv_filepath, usecols=variables).apply(
            pd.to_numeric, errors='coerce')

        for idx, var in enumerate(variables):
            # Drop NA/NaNs which poison the plot or cause it to throw
            column_data = csv_df[var].dropna()

            # TODO: Calculate best arrangement
            axes = figure.add_subplot(1, variables_count, idx + 1)
            axes.boxplot(column_data)

        # Write the overall figure with subplots into output file
        output_path = os.path.join(self.workdir, "output.png")
        figure.savefig(output_path)

        # Finish up by providing the path to the file
        response.outputs['output'].file = output_path

        return response
