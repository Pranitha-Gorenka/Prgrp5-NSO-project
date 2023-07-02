#!/usr/bin/env python3

from dotenv import load_dotenv
import os
import subprocess
import sys
import re
import datetime

# Get the current date and time
def get_formatted_time():
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_time

def run_command(command):
    subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def cleanup(openrc_file, ssh_key):
    # Load environment variables from the OpenRC file
    load_dotenv(openrc_file)
    print(f"{get_formatted_time()}: cleaning up {tag} using {openrc_file} ")
    # Server names
    server_names = [f"{tag}_proxy1",f"{tag}_proxy2",f"{tag}_bastion"]
    
    result = subprocess.run("openstack server list -c Name -f value", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    existing_nodes = re.findall(rf"^{tag}_node\d+", result.stdout, re.MULTILINE)

    print(f"{get_formatted_time()}: We have {len(existing_nodes)} nodes deleting them ")
    
    for i, node in enumerate(existing_nodes, start=1):
        run_command(f"openstack server delete {node}")
        print(f"{get_formatted_time()}: deleting {node} .. ")

    print(f"{get_formatted_time()}: Nodes are gone ") 
    # Delete servers
    for server_name in server_names:
        run_command(f"openstack server delete {server_name}")
        print(f"{get_formatted_time()}: deleting {server_name} .. ")
    # Delete port
    port_name = "{tag}_viprt"  
    run_command(f"openstack port delete {tag}_viprt")
    print(f"{get_formatted_time()}: deleting {tag}_viprt.. ")
   
    # List subnets and extract subnet IDs
    subnet_list_output = subprocess.check_output("openstack subnet list", shell=True)
    subnet_ids = re.findall(r"\|\s+(\w{8}-\w{4}-\w{4}-\w{4}-\w{12})\s+\|", subnet_list_output.decode())

    # Remove subnets from router and delete them
    router_name = f"{tag}_network-router"  # Replace with your router name
    for subnet_id in subnet_ids:
        run_command(f"openstack router remove subnet {router_name} {subnet_id}")
        run_command(f"openstack subnet delete {subnet_id}")
    print(f"{get_formatted_time()}: deleting subnet.. ")
    # Delete network
    network_name = "{tag}_network"  
    run_command(f"openstack network delete {tag}_network")
    print(f"{get_formatted_time()}: deleting network.. ")
    
    # Delete router
    run_command(f"openstack router delete {router_name}")
    print(f"{get_formatted_time()}: deleting router.. ")
    
    # Delete keypair
    keypair_name = f"{tag}_key"  
    run_command(f"openstack keypair delete {keypair_name}")
    print(f"{get_formatted_time()}: deleting keypair.. ")
    
    # Delete keypair
    securitygroup_name = f"{tag}_security-group"  
    run_command(f"openstack security group delete {tag}_security-group")
    print(f"{get_formatted_time()}: deleting security group.. ")
    
    # List floating IPs and extract floating IP IDs
#    floating_ip_list_output = subprocess.check_output("openstack floating ip list", shell=True)
#   floating_ip_ids = re.findall(r"\|\s+(\w{8}-\w{4}-\w{4}-\w{4}-\w{12})\s+\|", floating_ip_list_output.decode())

    # Delete floating IPs
#    for floating_ip_id in floating_ip_ids:
#       run_command(f"openstack floating ip delete {floating_ip_id}")
#       print(f"{get_formatted_time()}: deleting floating ips")

    # List volumes and extract volume IDs
    volume_list_output = subprocess.check_output("openstack volume list", shell=True)
    volume_ids = re.findall(r"\|\s+(\w{8}-\w{4}-\w{4}-\w{4}-\w{12})\s+\|", volume_list_output.decode())

    # Delete volumes
    for volume_id in volume_ids:
        run_command(f"openstack volume delete {volume_id}")
    
    print(f"{get_formatted_time()}: deleting volumes.. ")
     
    print(f"{get_formatted_time()}: Checking for {tag} in project..")
    
    # Check remaining servers
    remaining_servers_output = subprocess.check_output("openstack server list", shell=True)
    remaining_servers = re.findall(r"\|\s+(\w{8}-\w{4}-\w{4}-\w{4}-\w{12})\s+\|", remaining_servers_output.decode())
    print(f"{get_formatted_time()}: All servers deleted successfully")

   # Check remaining subnets
    remaining_subnets_output = subprocess.check_output("openstack subnet list", shell=True)
    remaining_subnets = re.findall(r"\|\s+(\w{8}-\w{4}-\w{4}-\w{4}-\w{12})\s+\|", remaining_subnets_output.decode())
    print(f"{get_formatted_time()}: All subnets deleted successfully")

    # Check remaining networks
    remaining_networks_output = subprocess.check_output("openstack network list", shell=True)
    remaining_networks = re.findall(r"\|\s+(\w{8}-\w{4}-\w{4}-\w{4}-\w{12})\s+\|", remaining_networks_output.decode())
    print(f"{get_formatted_time()}: All networks deleted successfully")

    # Check remaining routers
    remaining_routers_output = subprocess.check_output("openstack router list", shell=True)
    remaining_routers = re.findall(r"\|\s+(\w{8}-\w{4}-\w{4}-\w{4}-\w{12})\s+\|", remaining_routers_output.decode())
    print(f"{get_formatted_time()}: All routers deleted successfully")

    # Check remaining keypairs
    remaining_keypairs_output = subprocess.check_output("openstack keypair list", shell=True)
    remaining_keypairs = re.findall(r"\|\s+(\w{8}-\w{4}-\w{4}-\w{4}-\w{12})\s+\|", remaining_keypairs_output.decode())
    print(f"{get_formatted_time()}: All keypairs deleted successfully")

    # Check remaining security groups
    remaining_security_groups_output = subprocess.check_output("openstack security group list", shell=True)
    remaining_security_groups = re.findall(r"\|\s+(\w{8}-\w{4}-\w{4}-\w{4}-\w{12})\s+\|", remaining_security_groups_output.decode())
    print(f"{get_formatted_time()}: All security groups deleted successfully")

    # Check remaining volumes
    remaining_volumes_output = subprocess.check_output("openstack volume list", shell=True)
    remaining_volumes = re.findall(r"\|\s+(\w{8}-\w{4}-\w{4}-\w{4}-\w{12})\s+\|", remaining_volumes_output.decode())
    print(f"{get_formatted_time()}: All volumes deleted successfully")

    print(f"{get_formatted_time()}:cleaning done")    
    
    
if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(f"{get_formatted_time()}: Usage: python3 cleanup.py <openrc> <tag>")
        sys.exit(1)

    openrc_file = sys.argv[1]
    tag = sys.argv[2]
    
    if not os.path.isfile(openrc_file):
        print(f"Error: File '{openrc_file}' does not exist.")
        sys.exit(1)


    cleanup(openrc_file, tag)

