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

from props import prop
import uuid
import logging
from Notification import Notification
from NotificationCenter import NotificationCenter
from PersistentImageManager import PersistentImageManager

STATUS_STRINGS = ('NEW','PENDING', 'COMPLETE', 'FAILED')
NOTIFICATIONS = ('image.status', 'image.percentage')


class FactoryImage(object):
    """ TODO: Docstring for FactoryImage  """

##### PROPERTIES
    pim = prop("_pim")
    pi = prop("_pi")
    identifier = prop("_identifier")
    data = prop("_data")
    icicle = prop("_icicle")
    status_detail = prop("_status_detail")

    def status():
        doc = "A string value."
        def fget(self):
            return self._status

        def fset(self, value):
            value = value.upper()
            if(value in STATUS_STRINGS):
                old_value = self._status
                self._status = value
                notification = Notification(message=NOTIFICATIONS[0],
                                            sender=self,
                                            user_info=dict(old_status=old_value, new_status=value))
                self.notification_center.post_notification(notification)
            else:
                raise KeyError('Status (%s) unknown. Use one of %s.' % (value, STATUS_STRINGS))

        return locals()
    status = property(**status())

    def percent_complete():
        doc = "The percentage through an operation."
        def fget(self):
            return self._percent_complete

        def fset(self, value):
            old_value = self._percent_complete
            self._percent_complete = value
            notification = Notification(message=NOTIFICATIONS[1],
                                        sender=self,
                                        user_info=dict(old_percentage=old_value, new_percentage=value))
            self.notification_center.post_notification(notification)

        return locals()
    percent_complete = property(**percent_complete())
##### End PROPERTIES


    def create_from_pim(self, identifier):
        self._pi = self._pim.get_image( { 'id':identifier } )[0]
        if not self._pi:
            raise ImageFactoryException("Could not find image with identifier (%s) in persistent image store" % (identifier))

        self.identifier = identifier
        self._status = "NEW"

        # Set any of our persist_properties that exist in the external metadata
        # Warn on external props that are not in persist_properties
        for key in self._pi.meta:
            if key in self.persist_properties:
                setattr(self, key, self._pi.meta[key])
            else:
                self.log.warn("Ignoring persistent image property (%s)" % (key))

        # Look for any of our persist_properties that were _not_ set above
        # If we find any, warn
        for pprop in self.persist_properties:
            if not getattr(self, pprop, None):
                self.log.warn("Property (%s) was not retrieved from persisten image - setting to None" % (pprop))
                setattr(self, pprop, None)

        # Finally, set our copy of the location of the body
        # TODO: Decide if we want to support changing this in our FactoryImage objects
        #       If we do, decide what that means and what the convention is for updating the persistent image
        self.datafile = self._pi.body

    def update_pim_metadata(self):
        # Update all persisten_properties in our PersistentImage object, then flush them to stable storage
        for pprop in self.persist_properties:
            self._pi.meta[pprop] = getattr(self, pprop, None)
        self._pi.update_metadata()


    def __init__(self, persist = True):
        """ TODO: Fill me in
        
        @param template TODO
        """
        self.notification_center = NotificationCenter()
        self._pim = PersistentImageManager()
        self.log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))

