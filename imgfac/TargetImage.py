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

from BaseImage import BaseImage
from props import prop

class TargetImage(BaseImage):
    """ TODO: Docstring for TargetImage  """

    factory_image = prop("_factory_image")
    target = prop("_target")
    parameters = prop("_parameters")

    def __init__(self, factory_image, target, parameters):
        """ TODO: Fill me in
        
        @param template TODO
        @param target TODO
        @param parameters TODO
        """
        super(TargetImage, self).init()
        self.factory_image = factory_image
        self.target = target
        self.parameters = parameters