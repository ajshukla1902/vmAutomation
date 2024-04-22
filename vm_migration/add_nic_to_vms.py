from pyVmomi import vim
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

def get_network_by_name(si, network_name):
    """
    Get the network object by its name.
    """
    content = si.RetrieveContent()
    for network in content.viewManager.NetworkView:
        if network.name == network_name:
            return network
    print(f"Network '{network_name}' not found.")
    return None

def add_nic_to_vm(si, vm, network_name):
    """
    Add a NIC to the specified virtual machine.
    """
    spec = vim.vm.ConfigSpec()
    nic_spec = create_nic_spec(si, network_name)
    if nic_spec:
        spec.deviceChange = [nic_spec]
        vm.ReconfigVM_Task(spec=spec)
        print("NIC CARD ADDED")
    else:
        print("Failed to create NIC specification.")

def create_nic_spec(si, network_name):
    """
    Create a NIC specification for the given network name.
    """
    nic_spec = vim.vm.device.VirtualDeviceSpec()
    nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
    nic_spec.device = vim.vm.device.VirtualVmxnet3()
    nic_spec.device.deviceInfo = vim.Description()
    nic_spec.device.deviceInfo.summary = 'vCenter API test'

    network = get_network_by_name(si, network_name)
    if network:
        if isinstance(network, vim.OpaqueNetwork):
            nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.OpaqueNetworkBackingInfo()
            nic_spec.device.backing.opaqueNetworkType = network.summary.opaqueNetworkType
            nic_spec.device.backing.opaqueNetworkId = network.summary.opaqueNetworkId
        else:
            nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
            nic_spec.device.backing.useAutoDetect = False
            nic_spec.device.backing.deviceName = network_name

        nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
        nic_spec.device.connectable.startConnected = True
        nic_spec.device.connectable.allowGuestControl = True
        nic_spec.device.connectable.connected = False
        nic_spec.device.connectable.status = 'untried'
        nic_spec.device.wakeOnLanEnabled = True
        nic_spec.device.addressType = 'assigned'

        return nic_spec
    else:
        return None

def main():
    """
    Sample for adding a NIC to a virtual machine.
    """
    parser = argparse.ArgumentParser(description="Add a NIC to a virtual machine")
    parser.add_argument("-vc", "--vcenter", help="vCenter Host", required=True)
    parser.add_argument("-u", "--user", help="vCenter User", required=True)
    parser.add_argument("-p", "--password", help="vCenter Password", required=True)
    parser.add_argument("-vm", "--vmname", help="Name of the Virtual Machine", required=True)
    parser.add_argument("-n", "--network", help="Name of the Network", required=True)
    args = parser.parse_args()

    si = connect_vcenter(args.vcenter, args.user, args.password)
    if not si:
        return

    content = si.RetrieveContent()
    vm = None
    for vm_obj in content.rootFolder.childEntity[0].vmFolder.childEntity:
        if vm_obj.name == args.vmname:
            vm = vm_obj
            break

    if vm:
        add_nic_to_vm(si, vm, args.network)
    else:
        print("Virtual Machine not found.")

if __name__ == "__main__":
    main()
