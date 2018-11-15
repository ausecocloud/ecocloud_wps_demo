from pywps.processing import Processing


class ThreadProcessing(Processing):
    """
    :class:`MultiProcessing` is the default implementation to run jobs using the
    :module:`multiprocessing` module.
    """

    def start(self):
        import multiprocessing.dummy as multiprocessing
        process = multiprocessing.Process(
            target=getattr(self.job.process, self.job.method),
            args=(self.job.wps_request, self.job.wps_response)
        )
        process.start()
