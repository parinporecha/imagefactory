# encoding: utf-8

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

import FactoryImage
from props import prop
import uuid

class ProviderImage(FactoryImage.FactoryImage):
    """ TODO: Docstring for ProviderImage  """

    persist_properties = [ 'identifier', 'type', 'data', 'status',
                           'status_details', 'template', 'icicle',
                           'target', 'target_image', 'provider', 'parameters',
                           'snapshot' ]


    target_image = prop("_target_image")
    provider = prop("_provider")
    credentials = prop("_credentials")
    parameters = prop("_parameters")

    def __init__(self, identifier = None, data = None, status = "NEW", status_details = None,
                 template = None, icicle = None, target_image = None, target = None, provider = None,
                 credentials = None, parameters = None):
        """ TODO: Fill me in
        
        @param template TODO
        @param target_img_id TODO
        """
        super(ProviderImage, self).__init__(identifier=identifier)
        self.type = "provider_image"
        self.data = data
        self._status = status
        self.status_details = status_details
        self.template = template
        self.icicle = icicle
        self.target_image = target_image
        self.target = target
        self.provider = provider
        self.credentials = credentials
        self.parameters = parameters
