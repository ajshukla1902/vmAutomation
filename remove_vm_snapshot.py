#!/usr/bin/env python

from pyVmomi import vim
import ssl
from pyVim.connect import SmartConnect, Disconnect
from pyVim.task import WaitForTask
import argparse

def vCenterConnect(vcs, user, pwd):
    s = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    s.verify_mode = ssl.CERT_NONE
    try:
        si = SmartConnect(host=vcs, user=user, pwd=pwd, sslContext=s)
        return si.content
    except Exception as e:
        print(f"Error connecting to vCenter: {e}")
        return None

def get_vms_from_file(file_path):
    with open(file_path, 'r') as f:
        return [line.strip() for line in f.readlines()]

def get_snapshots_by_name_recursively(snapshots, snap_obj):
    for snapshot in snapshots:
        snap_obj.append(snapshot)
    return snap_obj

def main():
    parser = argparse.ArgumentParser(description="Delete a snapshot of the VM based on Check_MK Event Handler")
    parser.add_argument("-vc", "--vcs", help="vCenter Name", required=True)
    parser.add_argument("-u", "--user", help="vCenter User", required=True)
    parser.add_argument("-p", "--pwd", help="vCenter Password", required=True)
    parser.add_argument("-f", "--file", help="List of VMs", required=True)
    args = parser.parse_args()

    vcs = args.vcs
    user = args.user
    pwd = args.pwd
    vm_list_file = args.file

    content = vCenterConnect(vcs, user, pwd)
    if not content:
        return

    vms = get_vms_from_file(vm_list_file)

    for vm_name in vms:
        vm = next((vm for vm in content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True).view if vm_name in vm.name), None)
        if vm:
            snap_obj = get_snapshots_by_name_recursively(vm.snapshot.rootSnapshotList, [])
            if len(snap_obj) == 1:
                snap_object = snap_obj[0].snapshot
                WaitForTask(snap_object.RemoveSnapshot_Task(True))
                print(f"Snapshot for VM '{vm.name}' removed successfully.")
        else:
            print(f"VM '{vm_name}' not found.")

if __name__ == "__main__":
    main()
