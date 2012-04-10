# Persistent Image Manager
# Simple persistence layer
# This is a stub
# TO be replaced with something more sensible
# TODO: Thread safe updates
# TODO: Scalable metadata storage

from imgfac.Singleton import Singleton
from imgfac.ImageFactoryException import ImageFactoryException
import logging
import os
import uuid
import json

storage_location = "/var/lib/imagefactory/storage"

class PersistentImageManager(Singleton):

    # So, the body is guaranteed to be available locally as a file
    # Users have the right to replace the file
    # We might also want to offer the ability to 
    # Metadata must always be drawn, read and written through the class

    def _singleton_init(self):
        self.log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
        if not os.path.exists(storage_location):
            self.log.debug("Creating directory (%s) for persistent storage" % (storage_location))
            os.makedirs(storage_location)
        elif not os.path.isdir(storage_location):
            raise ImageFactoryException("Storage location (%s) already exists and is not a directory - cannot init persistence" % (storage_location))
        else:
            # TODO: verify that we can write to this location
            pass
        self.storage_location = storage_location

    def get_image_with_id(self, image_id):
        
        basename = self.storage_location + "/" + image_id
        metadatafile = basename + ".meta"
        bodyfile = basename + ".body"

        if not os.path.exists(metadatafile):
            return None

        metadata = json.load(open(metadatafile,"r"))

        if not os.path.exists(bodyfile):
            bodyfile = None

        return ( metadata, bodyfile )
        

    def create_image(self, meta = { }):
        # Create an empty object - used to reserve a UUID and a filesystem location
        # Allow users to pass in a pre-existing ID
        # TODO: verify that ID is unique and has valid structure
        if not 'identifier' in meta:
            meta['identifier'] = str(uuid.uuid4())
        image_uuid = meta['identifier']
        basename = self.storage_location + "/" + str(image_uuid)
        metadatafile = basename + ".meta"
        bodyfile = basename + ".body"

        mdf = open(metadatafile,"w")
        json.dump(meta, mdf)
        mdf.close()
        open(bodyfile, 'w').close()
        self.log.debug("Created new image object with id (%s)" % (str(image_uuid)))
        return ( meta, bodyfile )

    def set_image_metadata(self, object_id, meta):
        basename = self.storage_location + "/" + str(object_id)
        metadatafile = basename + ".meta"
        if not os.path.isfile(metadatafile):
            raise ImageFactoryException("Asked to set metadata for non-existent object id (%s)" % object_id)
        mdf = open(metadatafile,"w")
        json.dump(meta, mdf)
        mdf.close()
        self.log.debug("Updated metadata for object id (%s) to be: (%s)" % (object_id, meta))

    def delete_image(self, object_id):
        # delete object from stable store
        pass

    def replace_image_body(object_id, file_type_object):
        pass
        # Replace the body of object_id
        # For users who don't want to operate directly on filenames

