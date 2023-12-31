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
        execution1 = subprocess.run(f"openstack server delete {server_name}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if execution1.returncode == 0:
            print(f"{get_formatted_time()}: deleting {server_name} ..")
        else:
            print(f"{get_formatted_time()}: {server_name} does not exists! or already deleted.. ")
    # Delete port
    port_name = "{tag}_viprt"  
    execution2 = subprocess.run(f"openstack port delete {tag}_viprt", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if execution2.returncode == 0:
        print(f"{get_formatted_time()}: deleting {tag}_viprt.. ")
    else:
        print(f"{get_formatted_time()}: {tag}_viprt does not exists! or already deleted.. ")
        
    # List subnets and extract subnet IDs
    subnet_ids = subprocess.run("openstack subnet list", shell=True, capture_output=True, text=True).stdout
    
    # Remove subnets from router and delete them
    router_name = f"{tag}_network-router"  
    subnet_id = f"{tag}_network-subnet"
    if subnet_id in subnet_ids:
        run_command(f"openstack router remove subnet {router_name} {subnet_id}")
        run_command(f"openstack subnet delete {subnet_id}")
        print(f"{get_formatted_time()}: deleting subnet.. ")
    else: 
        print(f"{get_formatted_time()}: {tag}_network-subnet does not exists! or already deleted.. ")
    # Delete network
    execution3 = subprocess.run(f"openstack network delete {tag}_network", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if execution3.returncode == 0:
        print(f"{get_formatted_time()}: deleting network.. ")
    else:
        print(f"{get_formatted_time()}: {tag}_network does not exists! or already deleted.. ")
    
    # Delete router
    execution4 = subprocess.run(f"openstack router delete {tag}_network-router", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if execution4.returncode == 0:
        print(f"{get_formatted_time()}: deleting {tag}_network-router.. ")
    else:
            print(f"{get_formatted_time()}: {tag}_network-router does not exists! or already deleted.. ")
    
    # Delete keypair
    keypair_name = f"{tag}_key"  
    execution5 = subprocess.run(f"openstack keypair delete {keypair_name}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if execution5.returncode == 0:
        print(f"{get_formatted_time()}: deleting {keypair_name}.. ")
    else:
            print(f"{get_formatted_time()}: {keypair_name} does not exists! or already deleted.. ")
    
    # Delete securitygroup
    securitygroup_name = f"{tag}_security-group"
    execution6 = subprocess.run(f"openstack security group delete {tag}_security-group", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if execution6.returncode == 0:
        print(f"{get_formatted_time()}: deleting {securitygroup_name}.. ")
    else:
            print(f"{get_formatted_time()}: {securitygroup_name} does not exists! or already deleted.. ")
    
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
     
    print(f"{get_formatted_time()}: Checking for {tag} in project..")
    
    # Check remaining servers
    remaining_servers = subprocess.run("openstack server list", shell=True, capture_output=True, text=True).stdout
    if any(f"{tag}_" in server for server in remaining_servers):
        print(f"{get_formatted_time()}: Some servers with {tag}_ prefix still remain,deleting")
        run_command(f"openstack server delete {remaining_servers}")
    else:
        print(f"{get_formatted_time()}: All servers with {tag}_ prefix deleted successfully")

    # Check remaining subnets
    remaining_subnets = subprocess.run("openstack subnet list", shell=True, capture_output=True, text=True).stdout
    if f"{tag}_network-subnet" in remaining_subnets:
        print(f"{get_formatted_time()}: subnet with {tag}_ prefix still remain,deleting")
        run_command(f"openstack router remove subnet {tag}_network-router {tag}_network-subnet")
        run_command(f"openstack subnet delete {tag}_network-subnet")
    else:
        print(f"{get_formatted_time()}: All subnets with {tag}_ prefix deleted successfully")

    # Check remaining networks
    remaining_networks = subprocess.run("openstack network list", shell=True, capture_output=True, text=True).stdout
    if f"{tag}_network" in remaining_networks:
        print(f"{get_formatted_time()}: networks with {tag}_ prefix still remain,deleting")
        run_command(f"openstack network delete {tag}_network")
    else:
        print(f"{get_formatted_time()}: All networks with {tag}_ prefix deleted successfully")

    # Check remaining routers
    remaining_routers = subprocess.run("openstack router list", shell=True, capture_output=True, text=True).stdout
    if f"{tag}_network-router" in  remaining_routers:
        print(f"{get_formatted_time()}:routers with {tag}_ prefix still remain,deleting")
        run_command(f"openstack router delete {tag}_network-router")
    else:
        print(f"{get_formatted_time()}: All routers with {tag}_ prefix deleted successfully")

    # Check remaining keypairs
    remaining_keypairs = subprocess.run("openstack keypair list", shell=True, capture_output=True, text=True).stdout
    if f"{tag}_key" in  remaining_keypairs:
        print(f"{get_formatted_time()}:keypairs with {tag}_ prefix still remain,deleting")
        run_command(f"openstack keypair delete {tag}_key")
    else:
        print(f"{get_formatted_time()}: All keypairs with {tag}_ prefix deleted successfully")

    # Check remaining security groups
    remaining_security_groups = subprocess.run("openstack security group list", shell=True, capture_output=True, text=True).stdout
    if f"{tag}_security-group" in remaining_security_groups:
        print(f"{get_formatted_time()}:security groups with {tag}_ prefix still remain,deleting")
        run_command(f"openstack security group delete {tag}_security-group")
    else:
        print(f"{get_formatted_time()}: All security groups with {tag}_ prefix deleted successfully")

    
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

