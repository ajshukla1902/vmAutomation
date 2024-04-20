#!/usr/bin/env python

###########################################
#       Original add_nic.py V1 is:        #
#       Created By Aditya Shukla          #
#       Date : 20th-April-2024            #
#       DO NOT CHANGE THE FILE            #
###########################################


from pyVmomi import vim
import ssl
from pyVim.connect import SmartConnect, Disconnect
from pyVim.task import WaitForTask

# Define global variables
VM_LIST = []  # List of VMs where NICs will be added
VCENTER_HOST = ''  # VCenter IP address
VCENTER_USER = ''  # VCenter automation user
VCENTER_PASS = ''  # VCenter automation password
NETWORK_NAME = 'n'  # Network name to attach NICs

# Disable SSL verification (for testing purposes, improve security in production)
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
ssl_context.verify_mode = ssl.CERT_NONE

def connect_to_vcenter():
    """Establish a connection to vCenter."""
    try:
        si = SmartConnect(host=VCENTER_HOST, user=VCENTER_USER, pwd=VCENTER_PASS, sslContext=ssl_context)
        return si.content
    except Exception as e:
        print(f"Failed to connect to vCenter: {e}")
        return None

def get_vm_objects(vimtype):
    """Retrieve objects of a specific vimtype from vCenter."""
    content = connect_to_vcenter()
    if content:
        container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
        return container.view
    else:
        return None

def create_nic_spec(nicname, netname):
    """Create a NIC specification."""
    nicspec = vim.vm.device.VirtualDeviceSpec()
    nicspec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
    nic = vim.vm.device.VirtualVmxnet3()
    desc = vim.Description()
    desc.label = nicname
    desc.summary = netname
    nicbacking = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
    nicbacking.deviceName = netname
    nic.backing = nicbacking
    nic.deviceInfo = desc
    nic.addressType = 'generated'
    nicspec.device = nic
    return nicspec

def add_nic_to_vm(vm_object):
    """Add a NIC to the specified VM."""
    spec = vim.vm.ConfigSpec()
    nicnumber = len([dev for dev in vm_object.config.hardware.device if "addressType" in dir(dev)])
    nicname = f'Network adapter {nicnumber + 1}'
    nicspec = create_nic_spec(nicname, NETWORK_NAME)
    spec.deviceChange = [nicspec]
    try:
        task = vm_object.ReconfigVM_Task(spec=spec)
        WaitForTask(task)
        return {'result': 'success'}
    except Exception as e:
        print(f"Failed to add NIC to VM: {e}")
        return {'result': 'failure'}

def main():
    vimtype = [vim.VirtualMachine]
    vm_objects = get_vm_objects(vimtype)
    if vm_objects:
        for vm_name in VM_LIST:
            for vm_obj in vm_objects:
                if vm_name in vm_obj.name:
                    result = add_nic_to_vm(vm_obj)
                    print(result)
                    return

if __name__ == "__main__":
    main()
