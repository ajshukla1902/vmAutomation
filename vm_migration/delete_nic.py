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


def delete_virtual_nic(si, vm, nic_number):
    """
    Delete a virtual NIC from the specified virtual machine based on the NIC number.
    """
    nic_label = f'Network adapter {nic_number}'
    virtual_nic_device = None
    for dev in vm.config.hardware.device:
        if isinstance(dev, vim.vm.device.VirtualEthernetCard) and dev.deviceInfo.label == nic_label:
            virtual_nic_device = dev

    if not virtual_nic_device:
        raise RuntimeError(f'Virtual {nic_label} could not be found.')

    virtual_nic_spec = vim.vm.device.VirtualDeviceSpec()
    virtual_nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.remove
    virtual_nic_spec.device = virtual_nic_device

    spec = vim.vm.ConfigSpec()
    spec.deviceChange = [virtual_nic_spec]
    task = vm.ReconfigVM_Task(spec=spec)
    tasks.wait_for_tasks(si, [task])
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", help="vCenter Host", required=True)
    parser.add_argument("-u", "--user", help="vCenter User", required=True)
    parser.add_argument("-p", "--password", help="vCenter Password", required=True)
    parser.add_argument("--vmname", help="Name of the Virtual Machine", required=True)
    parser.add_argument("--unit-number", help="Unit Number of the NIC to delete", required=True, type=int)
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
        if delete_virtual_nic(si, vm, args.unit_number):
            print("Successfully deleted NIC CARD")
    else:
        print("VM not found")


if __name__ == "__main__":
    main()
