import logging
import os

from pywps import Process
from pywps import ComplexInput, LiteralInput, ComplexOutput, Format
from pywps.validator.mode import MODE

import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

class ExploratoryDataCorrelation(Process):
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
                data_type='string', min_occurs=2, max_occurs=4,
                mode=MODE.SIMPLE
            ),
            LiteralInput(
                'title', 'Title of plot',
                data_type='string', min_occurs=0, max_occurs=1,
                mode=MODE.SIMPLE
            ),
        ]

        outputs = [
            ComplexOutput('output', 'Output data',
                          as_reference=True,
                          supported_formats=[Format('image/png')]),
        ]

        super(ExploratoryDataCorrelation, self).__init__(
            self._handler,
            identifier='exploratory_data_correlation',
            title='Exploratory data: Correlation plot',
            abstract='Generates correlation pair plots from one or more variables in the provided CSV dataset',
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

        try:
            title = request.inputs['title'][0].data
        except:
            title = None

        # Read only the columns we need from the CSV
        csv_df = pd.read_csv(csv_filepath, usecols=variables).apply(
            pd.to_numeric, errors='coerce')

        # Generating a pair plot through `seaborn`
        pairplot = sns.pairplot(csv_df)
        figure = pairplot.fig

        # Set title where provided
        if title is not None:
            figure.suptitle(title)

        # Write the overall figure with subplots into output file
        output_path = os.path.join(self.workdir, "output.png")
        figure.savefig(output_path)

        # Finish up by providing the path to the file
        response.outputs['output'].file = output_path

        return response
