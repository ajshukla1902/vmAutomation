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


def update_virtual_nic_state(si, vm_obj, nic_number, new_nic_state):
    """
    Update the state of a virtual NIC for the specified virtual machine.
    """
    nic_label = f'Network adapter {nic_number}'
    virtual_nic_device = None
    for dev in vm_obj.config.hardware.device:
        if isinstance(dev, vim.vm.device.VirtualEthernetCard) and dev.deviceInfo.label == nic_label:
            virtual_nic_device = dev
            break

    if not virtual_nic_device:
        raise RuntimeError(f'Virtual {nic_label} could not be found.')

    virtual_nic_spec = vim.vm.device.VirtualDeviceSpec()
    virtual_nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.remove if new_nic_state == 'delete' else vim.vm.device.VirtualDeviceSpec.Operation.edit
    virtual_nic_spec.device = virtual_nic_device
    virtual_nic_spec.device.key = virtual_nic_device.key
    virtual_nic_spec.device.macAddress = virtual_nic_device.macAddress
    virtual_nic_spec.device.backing = virtual_nic_device.backing
    virtual_nic_spec.device.wakeOnLanEnabled = virtual_nic_device.wakeOnLanEnabled

    connectable = vim.vm.device.VirtualDevice.ConnectInfo()
    if new_nic_state == 'connect':
        connectable.connected = True
        connectable.startConnected = True
    elif new_nic_state == 'disconnect':
        connectable.connected = False
        connectable.startConnected = False
    else:
        connectable = virtual_nic_device.connectable

    virtual_nic_spec.device.connectable = connectable
    dev_changes = [virtual_nic_spec]
    spec = vim.vm.ConfigSpec()
    spec.deviceChange = dev_changes

    task = vm_obj.ReconfigVM_Task(spec=spec)
    tasks.wait_for_tasks(si, [task])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", help="vCenter Host", required=True)
    parser.add_argument("-u", "--user", help="vCenter User", required=True)
    parser.add_argument("-p", "--password", help="vCenter Password", required=True)
    parser.add_argument("--vmname", help="Name of the Virtual Machine", required=True)
    parser.add_argument("--nic_state", help="New state for the NIC (connect, disconnect, delete)", required=True)
    parser.add_argument("--unitnumber", help="NIC number", type=int, required=True)
    args = parser.parse_args()

    si = connect_vcenter(args.host, args.user, args.password)
    if not si:
        return

    content = si.RetrieveContent()
    print(f"Searching for VM {args.vmname}")
    vm_obj = None
    for vm in content.rootFolder.childEntity[0].vmFolder.childEntity:
        if vm.name == args.vmname:
            vm_obj = vm
            break

    if vm_obj:
        update_virtual_nic_state(si, vm_obj, args.unitnumber, args.nic_state)
        print(f"VM NIC {args.unitnumber} successfully state changed to {args.nic_state}")
    else:
        print("VM not found")


if __name__ == "__main__":
    main()
