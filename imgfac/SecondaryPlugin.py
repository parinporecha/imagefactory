#!/usr/bin/python
from time import *
from imgfac.ApplicationConfiguration import ApplicationConfiguration
from imgfac.ImageFactoryException import ImageFactoryException
from imgfac.CloudDelegate import CloudDelegate


# TODO: Perhaps tune this down a bit
REMOTE_TIMEOUT = 7200

class SecondaryPlugin(object):
    # The primary-side code for pushing/uploading via a secondary factory need only implement
    # the provider_image creation methods from the Cloud delegate interface.
    # So, we are treating it like a special purpose always-available Cloud plugin.
    zope.interface.implements(CloudDelegate)
    
    def __init__(self, helper):
        super(SecondaryPlugin, self).__init__()
        self.log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
        self.helper = helper


    def _metadata_dict(self, image, remove_data = True):
        return_dict = { }
        for key in image.metadata():
            value = getattr(image, key, None)
            if value:
                return_dict[key] = value
        if remove_data and 'data' in return_dict:
            del return_dict['data']
        return return_dict

    def _wait_for_final_status(self, image_path, local_image = None):
        full_path = "/imagefactory/%s" % image_path  
        for i in range(int(REMOTE_TIMEOUT/10 + 1)):
            remote_image = self.helper._http_get(full_path)
            if local_image:
                local_image.status = remote_image.status
                local_image.percent_complete = remote_image.percent_complete
                # TODO: Perhaps annotate the local copy to indicate this is a remote image
                local_image.status_detail = remote_image.status_detail
            if remote_image.status in [ 'COMPLETE', 'FAILED', 'DELETEFAILED' ]:
                return True
            sleep(10)
        # Timeout - calling function must set terminal status correctly based on what is happening
        return False
            
    def delete_from_provider(self, builder, provider, credentials, target, parameters):
        raise Exception("Delete not yet implemented for secondary factories")

    def push_image_to_provider(self, builder, provider, credentials, target, target_image, parameters):
        # Execute creation POST on secondary
        clone_path = "/imagefactory/target_images/%s" % builder.target_image.identifier
        clone_body = self._metadata_dict(builder.target_image)
        clone_response = self.helper._post(clone_path, body = clone_body, content_type='application/json')
        if not 'target_image' in clone_response:
            raise Exception("Failed to verify that target_image (%s) exists on secondary" % (builder.target_image.identifier))

        # If given an upload ID, upload to the URI
        if 'upload_id' in clone_response:
            upload_path = "/imagefactory/image_body_upload/%s" % clone_response['upload_id']
            upload_file = { 'image_body': open(builder.target_image.body, "rb") }
            upload_response = self.helper._http_post_file(upload_path, files = upload_file )

        # Wait <timeout> for remote target_image to become COMPLETE
        # NOTE: It is entirely possible that the target_image was present and COMPLETE
        #       at the time of the PUSH call.
        remote_image_path = "/imagefactory/target_images/%s" % clone_response.target_image['id']
        remote_result = self._wait_for_final_status(remote_image_path)

        if not remote_result:
            raise Exception("Timeout while waiting for secondary target_image clone to complete or fail")
  
        # Execute push POST for the original push request on the secondary
        provider_image_path = "/imagefactory/provider_images/%s" % builder.provider_image.identifier
        push_body = { 'provider': provider, 'credentials': credentials, 'target': target, 'target_image': target_image,
                      'parameters': parameters }
        push_response = self.helper._post(provider_image_path, body=push_body, content_type='application/json')

        # Wait <timeout> for remote provder_image to become COMPLETE
        remote_result = self._wait_for_final_status(provider_image_path, builder.provider_image)        
        if not remote_result:
            raise Exception("Timeout while waiting for secondary provider_image creation to complete or fail")

        if remote_result.status != "COMPLETE":
            raise Exception("Remote provider_image status is (%s) - Expecting COMPLETE" % remote_result.status)

    def snapshot_image_on_provider(self, builder, provider, credentials, target, template, parameters):
        # Execute push POST on the secondary
        provider_image_path = "/imagefactory/provider_images/%s" % builder.provider_image.identifier
        push_body =  { 'provider': provider, 'credentials': credentials, 'target': target, 'template': template,
                      'parameters': parameters }
        push_response = self.helper._post(provider_image_path, body=push_body, content_type='application/json')

        # Wait <timeout> fpr remote provider_image to become COMPLETE
        remote_result = self._wait_for_final_status(provider_image_path, builder.provider_image)
        if not remote_result:
            raise Exception("Timeout while waiting for secondary provider_image creation to complete or fail")
        
        if remote_result.status != "COMPLETE":
            raise Exception("Remote provider_image status is (%s) - Expecting COMPLETE" % remote_result.status)
 
