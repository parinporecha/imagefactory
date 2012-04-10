import BaseImage
import TargetImage
import ProviderImage
from PersistentImageManager import PersistentImageManager
from ImageFactoryException import ImageFactoryException

def retrieve_image_from_pim(image_id):
    pim = PersistentImageManager()
    print "Retrieving image (%s) from pim" % (image_id)
    ( metadata, bodyfile ) = pim.get_image_with_id(image_id)
    if not 'type' in metadata:
        raise ImageFactoryException("Retrieved persistent image with id (%s) has no 'type' meatdata key" % (image_id) )

    fio = None

    image_type = metadata['type']
    image_id = metadata['identifier']

    if image_type == "base_image":
        fio = BaseImage.BaseImage(identifier = image_id)
    elif image_type == "target_image":
        fio = TargetImage.TargetImage(identifier = image_id)
    elif image_type == "provider_image":
        fio = ProviderImage.ProviderImage(identifier = image_id)
    else:
        raise ImageFactoryException("Unknown persistent image type (%s)" % metadata['type'])

    fio.bodyfile = bodyfile
    fio.restore_from_persistent_metadata(metadata)

    return fio

