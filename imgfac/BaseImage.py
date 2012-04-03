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

from FactoryImage import FactoryImage
from props import prop
import uuid

class BaseImage(FactoryImage):
    """ TODO: Docstring for BaseImage  """

    persist_properties = [ 'identifier', 'type', 'data', 'status', 
                           'status_details', 'template', 'icicle', 'parameters' ]

    def __init__(self, identifier = None, data = None, status = "NEW", status_details = None,
                 template = None, icicle = None, parameters = None):
        """ TODO: Fill me in
        
        @param template TODO
        """
        super(BaseImage, self).__init__()
        if identifier:
            self.create_from_pim(identifier)
        else:            
            self.identifier = str(uuid.uuid4())
            self.type = "base_image"
            self.data = data
            self._status = status
            self.status_details = status_details
            self.template = template
            self.icicle = icicle
            self.parameters = parameters
            self._pi = self._pim.create_image(meta = { 'id':self.identifier } )
            self.update_pim_metadata()
            self.datafile = self._pi.body
