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
import sys
from xml.etree.ElementTree import fromstring
from glanceclient import client as glance_client
from keystoneclient.v2_0 import client as keystone_client
from cinderclient import client as cinder_client
from novaclient.v1_1 import client as nova_client
from time import sleep, gmtime, strftime

def glance_upload_launch(image_filename, creds = {'auth_url': None, 'password': None, 'strategy': 'noauth', 'tenant': None, 'username': None},
                         host = "0.0.0.0", port = "9292", token = None, name = 'Factory Test Image', disk_format = 'raw'):


    k = keystone_client.Client(username=creds['username'], password=creds['password'], tenant_name=creds['tenant'], auth_url=creds['auth_url'])

    os_image_endpoint = "http://" + host + ":" + str(port)
    if (k.authenticate()):
        #Connect to glance to upload the image
        glance = glance_client.Client("1", endpoint=os_image_endpoint, token=k.auth_token)
        #image_filename = "/root/F17.qcow2"
        #disk_format = "qcow2"
        image_data = open(image_filename, "r")
        #Connect to cinder so we can create a volume from an image in glance
        cinder = cinder_client.Client('2', creds['username'], creds['password'], creds['tenant'], creds['auth_url'])
        #Connect to nova to start an instance with the volume we created in cinder
        nova = nova_client.Client(creds['username'], creds['password'], creds['tenant'],
                auth_url=creds['auth_url'], insecure=True)
        image_meta = {'container_format': 'bare',
         'disk_format': disk_format,
         'is_public': True,
         'min_disk': 0,
         'min_ram': 0,
         'name': name,
         'data': image_data,
         'properties': {'distro': 'rhel'}}
        try:
            image = glance.images.create(name=name)
            print "Uploading to Glance"
	    image.update(**image_meta)
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

            instance = nova.servers.create('test2', None, 2, meta={}, block_device_mapping=block_device_mapping)
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

glance_host = "10.16.17.5"
glance_port = 9292

creds = { 'auth_url': 'http://10.16.17.4:5000/v2.0', 'password': 'imcleod', 'strategy': 'keystone', 'tenant': 'imcleod', 'username': 'imcleod' }

filename = sys.argv[1]


glance_upload_launch(filename, creds = creds, host = glance_host, port = glance_port, token = None,
                     name = 'Upload - %s - %s' % ( filename, strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime()) ), 
                      disk_format = 'qcow2')
