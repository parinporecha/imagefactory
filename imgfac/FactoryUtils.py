#!/usr/bin/python

# A set of helpful utility functions
# Avoid imports that are too specific to a given cloud or OS
# We want to allow people to import all of these
# Add logging option

import guestfs

def inspect_and_mount(diskfile):
    g = guestfs.GuestFS()
    g.add_drive(diskfile)
    g.launch()
    inspection = g.inspect_os()
    if len(inspection) == 0:
        raise Exception("Unable to find an OS on disk image (%s)" % (diskfile))
    if len(inspection) > 1:
        raise Exception("Found multiple OSes on disk image (%s)" % (diskfile))
    filesystems = g.inspect_get_mountpoints(inspection[0])
    fhash = { }
    for filesystem in filesystems:
        fshash[filesystem[0]] = filesystem[1]
 
    mountpoints = fhash.keys()
    # per suggestion in libguestfs doc - sort the mount points on length
    # simple way to ensure that mount points are present before a mount is attempted
    mountpoints.sort(key=len)
    for mountpoint in mountpoints:
        g.mount_options("", fshash[mountpoint], mountpoint)
    return g

def sync_and_unmount(guestfs_handle):
    guestfs_handle.sync()
    guestfs_handle.umount_all()

def remove_net_persist(guestfs_handle):
    # In the cloud context we currently never need or want persistent net device names
    # This is known to break networking in RHEL/VMWare and could potentially do so elsewhere
    # Just delete the file to be safe
    g = guestfs_handle
    if g.is_file("/etc/udev/rules.d/70-persistent-net.rules"):
        g.rm("/etc/udev/rules.d/70-persistent-net.rules")

    # Also clear out the MAC address this image was bound to.
    g.aug_init("/", 0)
    g.aug_rm("/files/etc/sysconfig/network-scripts/ifcfg-eth0/HWADDR")
    g.aug_save()
    g.aug_close()

def create_cloud_info(guestfs_handle, target):
    tmpl = 'CLOUD_TYPE="%s"\n' % (target)
    guestfs_handle.write("/etc/sysconfig/cloud-info", tmpl)
