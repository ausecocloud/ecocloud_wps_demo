import logging
import os
import os.path
import uuid

from pywps import configuration as config
from pywps.inout.storage import CachedStorage

from swiftclient.service import SwiftService, SwiftUploadObject


def get_temp_url_key():
    # TODO: we could just read temp_url_key from container as well
    #       swift.stat(container)['headers']['x-container-meta-temp-url-key']
    return (
        config.get_config_value('SwiftStorage', 'temp_url_key')
        or os.environ['TEMP_URL_KEY']
    )


class SwiftStorage(CachedStorage):

    def __init__(self):
        """
        """
        super().__init__()
        self.output_url = config.get_config_value('server', 'outputurl')
        self.temp_url_key = get_temp_url_key()
        self.container = config.get_config_value('SwiftStorage', 'container')
        # storage timeout etc...

    def _do_store(self, output):
        log = logging.getLogger(__name__)
        file_name = output.file
        request_uuid = str(output.uuid or uuid.uuid1())

        # build output name
        (prefix, suffix) = os.path.splitext(file_name)
        if not suffix:
            suffix = output.data_format.extension
        (file_dir, file_name) = os.path.split(prefix)
        output_name = file_name + suffix

        swift = SwiftService({'use_slo': True, 'segment_size': 5 * 1024 * 1024 * 1024})
        object_name = '/'.join((request_uuid, output_name))
        upload = SwiftUploadObject(
            output.file,
            object_name,
            options={
                'header': {
                    'X-Delete-After': str(60 * 60 * 24 * 7)  # 7 days
                }
            }
        )
        log.info('Storing file output to %s', object_name)
        response = swift.upload(self.container, [upload])
        # We have to consume the reponse otherwise the object won't get uploaded
        for res in response:
            if res['success']:
                # res['action'] = ('create_container', 'upload_object')
                continue
            log.error('FAIL: %s', res)

        return (10, object_name, self.output_url.rstrip('/') + '/' + object_name)
