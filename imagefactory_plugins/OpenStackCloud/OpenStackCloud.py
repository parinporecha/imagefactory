#!/usr/bin/python
#
#   Copyright 2012 Red Hat, Inc.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import logging
import zope
import libxml2
import json
import os
import struct
from xml.etree.ElementTree import fromstring
from imgfac.Template import Template
from imgfac.ApplicationConfiguration import ApplicationConfiguration
from imgfac.BuildDispatcher import BuildDispatcher
from imgfac.ImageFactoryException import ImageFactoryException
from imgfac.CloudDelegate import CloudDelegate
from imgfac.FactoryUtils import launch_inspect_and_mount, shutdown_and_close, remove_net_persist, create_cloud_info
from glanceclient import client as glance_client
from keystoneclient.v2_0 import client as keystone_client
from cinderclient import client as cinder_client
from novaclient.v1_1 import client as nova_client
from time import sleep

def glance_upload(image_filename, creds = {'auth_url': None, 'password': None, 'strategy': 'noauth', 'tenant': None, 'username': None},
                  host = "0.0.0.0", port = "9292", token = None, name = 'Factory Test Image', disk_format = 'raw'):


    k = keystone_client.Client(username=creds['username'], password=creds['password'], tenant_name=creds['tenant'], auth_url=creds['auth_url'])

    os_image_endpoint = "http://" + host + ":" + str(port)
    if (k.authenticate()):
        #Connect to glance to upload the image
        glance = glance_client.Client("1", endpoint=os_image_endpoint, token=k.auth_token)
        image_filename = "/root/RHEL5.qcow2"
        disk_format = "qcow2"
        image_data = open(image_filename, "r")
        #Connect to cinder so we can create a volume from an image in glance
        #TODO change tenant name to something other then username, might be 
        #different in future
        cinder = cinder_client.Client('1', creds['username'], creds['password'], creds['username'], creds['auth_url'])
        #Connect to nova to start an instance with the volume we created in cinder
        nova = nova_client.Client(creds['username'], creds['password'], creds['username'],
                auth_url=creds['auth_url'], insecure=True)
        import pdb;pdb.set_trace()
        image_meta = {'container_format': 'bare',
         'disk_format': disk_format,
         'is_public': True,
         'min_disk': 0,
         'min_ram': 0,
         'name': name,
         'data': image_data,
         'properties': {'distro': 'rhel'}}
        try:
            image = glance.images.create(name="My Test Image")
            print "Uploading to Glance"
	    image.update(**image_meta)
            import pdb;pdb.set_trace()
            print "Starting asyncronous copying to Cinder"
            volume = cinder.volumes.create(10, imageRef=image.id)
            #check if volume finished creating
            volume_status = cinder.volumes.get(volume.id).status
            while (volume_status != 'available'):
                print "Waiting for volume to be ready ... "
                sleep(5)
                volume_status = cinder.volumes.get(volume.id).status
                if (volume_status == 'error'):
                    raise Exception('Error converting image to volume')
            #instance = nova.create
            block_device_mapping = {'vda': volume.id + ":::0"} 

            instance = nova.servers.create(name, None, 2, meta={}, block_device_mapping=block_device_mapping)
            import pdb;pdb.set_trace()

        except Exception, e:
            print e
        finally:
            image_data.close()
            import pdb;pdb.set_trace()
            return image.id
    else:
        #TODO: Raise an exception
	return None

class OpenStackCloud(object):
    zope.interface.implements(CloudDelegate)

    def __init__(self):
        # Note that we are now missing ( template, target, config_block = None):
        super(OpenStackCloud, self).__init__()
        self.app_config = ApplicationConfiguration().configuration
        self.log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))

    def activity(self, activity):
        # Simple helper function
        # Activity should be a one line human-readable string indicating the task in progress
        # We log it at DEBUG and also set it as the status_detail on our active image
        self.log.debug(activity)
        self.active_image.status_detail['activity'] = activity

    def push_image_to_provider(self, builder, provider, credentials, target, target_image, parameters):
        # Our target_image is already a raw KVM image.  All we need to do is upload to glance
        self.builder = builder
        self.active_image = self.builder.provider_image
        self.openstack_decode_credentials(credentials)

        provider_data = self.get_dynamic_provider_data(provider)
        if provider_data is None:
            raise ImageFactoryException("OpenStack KVM instance not found in XML or JSON provided")

        # Image is always here and it is the target_image datafile
        input_image = self.builder.target_image.data

        # If the template species a name, use that, otherwise create a name
        # using provider_image.identifier.
        template = Template(self.builder.provider_image.template)
        if template.name:
            image_name = template.name
        else:
            image_name = 'ImageFactory created image - %s' % (self.builder.provider_image.identifier)

        if self.check_qcow_size(input_image):
            self.log.debug("Uploading image to glance, detected qcow format")
            disk_format='qcow2'
        else:
            self.log.debug("Uploading image to glance, assuming raw format")
            disk_format='raw'
        image_id = glance_upload(input_image, creds = self.credentials_dict, token = self.credentials_token,
                                 host=provider_data['glance-host'], port=provider_data['glance-port'],
                                 name=image_name, disk_format=disk_format)

        self.builder.provider_image.identifier_on_provider = image_id
        if 'username' in self.credentials_dict:
            self.builder.provider_image.provider_account_identifier = self.credentials_dict['username']
        self.percent_complete=100

    def openstack_decode_credentials(self, credentials):
        self.activity("Preparing OpenStack credentials")
        # TODO: Validate these - in particular, ensure that if some nodes are missing at least
        #       a minimal acceptable set of auth is present
        doc = libxml2.parseDoc(credentials)

        self.credentials_dict = { }
        for authprop in [ 'auth_url', 'password', 'strategy', 'tenant', 'username']:
            self.credentials_dict[authprop] = self._get_xml_node(doc, authprop)
        self.credentials_token = self._get_xml_node(doc, 'token')

    def _get_xml_node(self, doc, credtype):
        nodes = doc.xpathEval("//provider_credentials/openstack_credentials/%s" % (credtype))
        # OpenStack supports multiple auth schemes so not all nodes are required
        if len(nodes) < 1:
            return None

        return nodes[0].content

    def snapshot_image_on_provider(self, builder, provider, credentials, template, parameters):
        # TODO: Implement snapshot builds
        raise ImageFactoryException("Snapshot builds not currently supported on OpenStack KVM")

    def builder_should_create_target_image(self, builder, target, image_id, template, parameters):
        return True

    def builder_will_create_target_image(self, builder, target, image_id, template, parameters):
        pass

    def builder_did_create_target_image(self, builder, target, image_id, template, parameters):
        self.target=target
        self.builder=builder 
        self.modify_oz_filesystem()

        # OS plugin has already provided the initial file for us to work with
        # which we can currently assume is a raw image
        input_image = builder.target_image.data

        # Support conversion to alternate preferred image format
        # Currently only handle qcow2, but the size reduction of
        # using this avoids the performance penalty of uploading
        # (and launching) raw disk images on slow storage
        if self.app_config.get('openstack_image_format', 'raw') == 'qcow2':
            self.log.debug("Converting RAW image to compressed qcow2 format")
            rc = os.system("qemu-img convert -c -O qcow2 %s %s" %
                            (input_image, input_image + ".tmp.qcow2"))
            if rc == 0:
                os.unlink(input_image)
                os.rename(input_image + ".tmp.qcow2", input_image)
            else:
                raise ImageFactoryException("qemu-img convert failed!")

    def modify_oz_filesystem(self):
        self.log.debug("Doing further Factory specific modification of Oz image")
        guestfs_handle = launch_inspect_and_mount(self.builder.target_image.data)
        remove_net_persist(guestfs_handle)
        create_cloud_info(guestfs_handle, self.target)
        shutdown_and_close(guestfs_handle)

    def get_dynamic_provider_data(self, provider):
        try:
            xml_et = fromstring(provider)
            return xml_et.attrib
        except Exception as e:
            self.log.debug('Testing provider for XML: %s' % e)
            pass

        try:
            jload = json.loads(provider)
            return jload
        except ValueError as e:
            self.log.debug('Testing provider for JSON: %s' % e)
            pass

        return None

    # FIXME : cut/paste from RHEVMHelper.py, should refactor into a common utility class
    def check_qcow_size(self, filename):
        # Detect if an image is in qcow format
        # If it is, return the size of the underlying disk image
        # If it isn't, return None

        # For interested parties, this is the QCOW header struct in C
        # struct qcow_header {
        #    uint32_t magic;
        #    uint32_t version;
        #    uint64_t backing_file_offset;
        #    uint32_t backing_file_size;
        #    uint32_t cluster_bits;
        #    uint64_t size; /* in bytes */
        #    uint32_t crypt_method;
        #    uint32_t l1_size;
        #    uint64_t l1_table_offset;
        #    uint64_t refcount_table_offset;
        #    uint32_t refcount_table_clusters;
        #    uint32_t nb_snapshots;
        #    uint64_t snapshots_offset;
        # };

        # And in Python struct format string-ese
        qcow_struct=">IIQIIQIIQQIIQ" # > means big-endian
        qcow_magic = 0x514649FB # 'Q' 'F' 'I' 0xFB

        f = open(filename,"r")
        pack = f.read(struct.calcsize(qcow_struct))
        f.close()

        unpack = struct.unpack(qcow_struct, pack)

        if unpack[0] == qcow_magic:
            return unpack[5]
        else:
            return None
