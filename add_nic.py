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
from tools import cli, pchelper, service_instance

vmList = []                             # List all the VM's where you wanna add nic 
vcs = ''                                # Give the IP Address of VCenter 
vCenterUser = ""                        # VCenter automation user
vCenterPass = ""                        # VCenter automation password

###################### vCenter Login Function ######################
def vCenterConnet(vcs):
    s=ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    s.verify_mode=ssl.CERT_NONE
    si= SmartConnect(host=vcs, user=vCenterUser, pwd=vCenterPass,sslContext=s)
    content=si.content
    return content

###################### Esxi Objects Function ######################
def vSphereObjects(vcs, vimtype):
    content = vCenterConnet(vcs)
    container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
    objectContent = container.view
    return objectContent

###################### Create New Nic ######################
def createnicspec(nicname, netname):
    nicspec = vim.vm.device.VirtualDeviceSpec()
    nicspec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
    nic = vim.vm.device.VirtualVmxnet3()
    desc = vim.Description()
    desc.label = nicname
    nicbacking = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
    desc.summary = netname
    nicbacking.deviceName = netname
    nic.backing = nicbacking
    # nic.key = 0
    nic.deviceInfo = desc
    nic.addressType = 'generated'
    nicspec.device = nic
    return nicspec
    
network ='n'

###################### Main Function to find the Object in VCenter ######################
def Main():
    vimtype = [vim.VirtualMachine]
    contentObject = vSphereObjects(vcs, vimtype)
    for vm in vmList:
        for vmObject in contentObject:
            if vm in vmObject.name:
                spec = vim.vmObject.ConfigSpec()
                nicnumber = len([dev for dev in vmObject.config.hardware.device if "addressType" in dir(dev)])
                nicname = 'Network adapter %d' % (nicnumber + 1)
                nicspec = createnicspec(nicname, network)
                nic_changes = [nicspec]
                spec.deviceChange = nic_changes
                t = vm.ReconfigVM_Task(spec=spec)
                WaitForTask(t)
                return {'result': 'success'}

if __name__ == "__main__":
    Main()