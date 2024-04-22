from pyVmomi import vim, vmodl
from pyVim.connect import SmartConnect, Disconnect
import ssl
import argparse


def connect_vcenter(host, user, password):
    """
    Connect to vCenter server and return the service instance.
    """
    try:
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        context.verify_mode = ssl.CERT_NONE
        si = SmartConnect(host=host, user=user, pwd=password, sslContext=context)
        return si
    except Exception as e:
        print(f"Error connecting to vCenter: {e}")
        return None


def change_vm_nic_network(si, vm, unit_number, network_name, is_vds):
    """
    Change the NIC of the specified virtual machine.
    """
    device_change = []
    for device in vm.config.hardware.device:
        if isinstance(device, vim.vm.device.VirtualEthernetCard) and str(unit_number) in device.deviceInfo.label:
            nicspec = vim.vm.device.VirtualDeviceSpec()
            nicspec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
            nicspec.device = device
            nicspec.device.wakeOnLanEnabled = True

            if not is_vds:
                nicspec.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
                nicspec.device.backing.network = get_network_by_name(si, network_name)
                nicspec.device.backing.deviceName = network_name
            else:
                network = get_network_by_name(si, network_name)
                if isinstance(network, vim.dvs.DistributedVirtualPortgroup):
                    dvs_port_connection = vim.dvs.PortConnection()
                    dvs_port_connection.portgroupKey = network.key
                    dvs_port_connection.switchUuid = network.config.distributedVirtualSwitch.uuid
                    nicspec.device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
                    nicspec.device.backing.port = dvs_port_connection

            nicspec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
            nicspec.device.connectable.startConnected = True
            nicspec.device.connectable.allowGuestControl = True
            device_change.append(nicspec)
            break

    config_spec = vim.vm.ConfigSpec(deviceChange=device_change)
    task = vm.ReconfigVM_Task(config_spec)
    return task


def get_network_by_name(si, network_name):
    """
    Get the network object by its name.
    """
    content = si.RetrieveContent()
    for network in content.rootFolder.childEntity[0].networkFolder.childEntity:
        if isinstance(network, vim.Network) and network.name == network_name:
            return network
    print(f"Network '{network_name}' not found.")
    return None


def main():
    """
    Simple command-line program for changing network virtual machine NIC.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", help="vCenter Host", required=True)
    parser.add_argument("-u", "--user", help="vCenter User", required=True)
    parser.add_argument("-p", "--password", help="vCenter Password", required=True)
    parser.add_argument("--vmname", help="Name of the Virtual Machine", required=True)
    parser.add_argument("--unitnumber", help="NIC number", type=int, required=True)
    parser.add_argument("--network", help="Name of the Network", required=True)
    parser.add_argument("--is_vds", help="Is the network in VDS or VSS", action="store_true")
    args = parser.parse_args()

    si = connect_vcenter(args.host, args.user, args.password)
    if not si:
        return

    content = si.RetrieveContent()
    vm = None
    for vm_obj in content.rootFolder.childEntity[0].vmFolder.childEntity:
        if vm_obj.name == args.vmname:
            vm = vm_obj
            break

    if vm:
        task = change_vm_nic_network(si, vm, args.unitnumber, args.network, args.is_vds)
        print(f"Successfully started changing NIC for VM '{args.vmname}'. Task: {task}")
    else:
        print("Virtual Machine not found.")


# Start program
if __name__ == "__main__":
    main()
