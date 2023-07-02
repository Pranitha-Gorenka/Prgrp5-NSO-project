#!/usr/bin/env python3

from dotenv import load_dotenv
import os
import sys
import subprocess
import re
import socket
import datetime
import requests
import ast
import json

# Function to get the current formatted time
def get_formatted_time():
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_time

# Extract command-line arguments
openrc_file = sys.argv[1]
tag = sys.argv[2]
ssh_key = sys.argv[3]

# Check if the provided files exist
if not os.path.isfile(openrc_file):
    print(f"Error: File '{openrc_file}' does not exist.")
    sys.exit(1)

if not os.path.isfile(ssh_key):
    print(f"Error: File '{ssh_key}' does not exist.")
    sys.exit(1)
    
# Load environment variables from the OpenRC file
load_dotenv(openrc_file)

# Access the environment variables
username = os.getenv("OS_USERNAME")
password = os.getenv("OS_PASSWORD")
auth_url = os.getenv("OS_AUTH_URL")
# ... and so on
print(f"{get_formatted_time()}: Starting deployment of {tag} using {openrc_file} for credentials. ")
# Define server names
server_names = [f"{tag}_node1", f"{tag}_node2", f"{tag}_node3", f"{tag}_proxy2", f"{tag}_proxy1", f"{tag}_bastion" ]
    
network_list = "openstack network list"
network_name = subprocess.run(network_list, shell=True, capture_output=True, text=True).stdout

print(f"{get_formatted_time()}: checking for {tag}_network in the OpenStack project..")
# Check if network exists
if f"{tag}_network" in network_name:
    network_name = f"{tag}_network"
    print(f"{get_formatted_time()}: Network found")
else:
    # Create network
    create_network = f"openstack network create {tag}_network"
    execution1 = subprocess.run(create_network, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if execution1.returncode == 0:
        print(f"{get_formatted_time()}: network {tag}_network does not exists! creating a network..")
    else: 
        print(f"{get_formatted_time()}: {tag}_network not created..")
        sys.exit(1)
    
    # Create subnet
    create_subnet = f"openstack subnet create {tag}_network-subnet --network {tag}_network --subnet-range 10.0.1.0/27"
    execution2 = subprocess.run(create_subnet, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if execution2.returncode == 0:
        print(f"{get_formatted_time()}: creating a {tag}_network-subnet for {tag}_network..")
    else:
        print(f"{get_formatted_time()}: {tag}_network-subnet  not created..")
        sys.exit(1)
        
    # Create router
    create_router = f"openstack router create {tag}_network-router"
    execution3 = subprocess.run(create_router, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if execution3.returncode == 0:
        print(f"{get_formatted_time()}: creating a router..")
    else:
        print(f"{get_formatted_time()}: {tag}_router  not created..")
        sys.exit(1)
        
    # Set external gateway for the router
    create_ext = f"openstack router set {tag}_network-router --external-gateway ext-net"
    execution4 = subprocess.run(create_ext, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if execution4.returncode == 0:
        print(f"{get_formatted_time()}: creating a external gateway for router..")
    else:
        print(f"{get_formatted_time()}: external gateway not created..")
        sys.exit(1)
        
    # Connect subnet to router
    connect = f"openstack router add subnet {tag}_network-router {tag}_network-subnet"
    execution5 = subprocess.run(connect, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if execution5.returncode == 0:
        print(f"{get_formatted_time()}: adding router to subnet..")
    else:
        print(f"{get_formatted_time()}: router not added to subnet..")
        sys.exit(1)

#create a key
key_pair = "openstack keypair list"
key_pair_name = subprocess.run(key_pair, shell=True, capture_output=True, text=True).stdout
print(f"{get_formatted_time()}: checking for {tag}_key in the OpenStack project..")
       
if f"{tag}_key" in key_pair_name:
    key_pair_name = f"{tag}_key"
    print(f"{get_formatted_time()}: keypair found")
else:
    create_key=f"openstack keypair create --public-key {ssh_key} {tag}_key"
    execution6 = subprocess.run(create_key, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if execution6.returncode == 0:
        print(f"{get_formatted_time()}: creating a {tag}_key..")
    else:
        print(f"{get_formatted_time()}: {tag}_key not created..")
        sys.exit(1)  


# Create a new security group
security_group = "openstack security group list"
security_group_name = subprocess.run(security_group, shell=True, capture_output=True, text=True).stdout

print(f"{get_formatted_time()}: checking for {tag}_security-group in the OpenStack project..")
        
if f"{tag}_security-group" in security_group_name:
    security_group_name = f"{tag}_security-group"
    print(f"{get_formatted_time()}: {tag}_security-group found")
else:
    create_security_group = f"openstack security group create {tag}_security-group"
    execution7 = subprocess.run(create_security_group, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Add the required rules to the new security group
    create_ssh_rule = f"openstack security group rule create --protocol tcp --dst-port 22 {tag}_security-group"
    create_http_rule = f"openstack security group rule create --protocol tcp --dst-port 80 {tag}_security-group"
    create_https_rule = f"openstack security group rule create --protocol tcp --dst-port 443 {tag}_security-group"
    create_flask_rule = f"openstack security group rule create --protocol tcp --dst-port 5000 {tag}_security-group" 
    create_snmp_rule = f"openstack security group rule create --protocol udp --dst-port 6000 {tag}_security-group"
    create_snmpd_rule = f"openstack security group rule create --protocol udp --dst-port 161 {tag}_security-group"
    create_icmp_rule = f"openstack security group rule create --protocol icmp --dst-port 80 {tag}_security-group"
    create_rule1=f"openstack security group rule create --protocol tcp --dst-port 9090 {tag}_security-group"
    create_rule2=f"openstack security group rule create --protocol tcp --dst-port 9100 {tag}_security-group"
    create_rule3=f"openstack security group rule create --protocol tcp --dst-port 3000 {tag}_security-group"
    create_rule4=f"openstack security group rule create --protocol tcp --dst-port 8080 {tag}_security-group"
    create_rule5=f"openstack security group rule create --protocol 112 {tag}_security-group"

    subprocess.run(create_ssh_rule, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(create_http_rule, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(create_https_rule, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(create_flask_rule, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(create_snmp_rule, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(create_snmpd_rule, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(create_icmp_rule, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(create_rule1, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(create_rule2, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(create_rule3, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(create_rule4, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(create_rule5, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    if execution7.returncode == 0:
        print(f"{get_formatted_time()}: Created a  {tag}_security-group and added the required rules.")
    else:
        print(f"{get_formatted_time()}: {tag}_security-group not created..")
        sys.exit(1)  
    

# Create servers

for server_name in server_names:
    check_server = f"openstack server show {server_name}"
    result = subprocess.run(check_server, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode == 0:
        # Server with the same name already exists
        print(f"{get_formatted_time()}: Server '{server_name}' already exists.")
        continue  # Skip creating the server
    else:
        create_server = f"openstack server create --image 'Ubuntu 20.04 Focal Fossa x86_64' --key-name {tag}_key --flavor '1C-2GB-50GB' --network {tag}_network --security-group {tag}_security-group {server_name}"
        create_server1=subprocess.run(create_server, shell=True, stdout=subprocess.DEVNULL, stderr=True)
        if create_server1.returncode == 0:
            print(f"{get_formatted_time()}: Creating server {server_name}...")
        else:
            print(f"{get_formatted_time()}: {server_name} not created...")
            exit(1)
            
# Fetch the IP addresses of the created servers
node_ips = []
for server_name in server_names:
    fetch_ip_command = f"openstack server show -f value -c addresses {server_name}"
    ip_address_output = subprocess.run(fetch_ip_command, shell=True, capture_output=True, text=True).stdout.strip()

    # Extract the IP address from the output using regex
    ip_address = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', ip_address_output)[0]

    # Append the IP address to the node_ips list
    node_ips.append(ip_address)

# Fetch the fixed IP address for proxy1
fetch_ip_command = f"openstack server show -f value -c addresses {tag}_proxy1"
ip_address_output = subprocess.run(fetch_ip_command, shell=True, capture_output=True, text=True).stdout.strip()
ip_address = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', ip_address_output)[0]
node_ips.append(ip_address)
      
# Creating floating ip
floating_present = subprocess.check_output(['openstack', 'floating', 'ip', 'list', '-c', 'Floating IP Address', '-f', 'value']).decode().strip().split('\n')

if len(floating_present) == 0:
    print(f'{get_formatted_time()}: No floating IPs are present')
    print(f'{get_formatted_time()}: Creating 2 floating IPs')
    create_floating_ip1 = subprocess.check_output(['openstack', 'floating', 'ip', 'create', 'ext-net', '-f', 'value', '--column', 'floating_ip_address']).decode().strip()
    create_floating_ip2 = subprocess.check_output(['openstack', 'floating', 'ip', 'create', 'ext-net', '-f', 'value', '--column', 'floating_ip_address']).decode().strip()
    f1 = create_floating_ip1
    f2 = create_floating_ip2
    print(f'{get_formatted_time()}: {f1} created for bastion')
    print(f'{get_formatted_time()}: {f2} created for HAproxys')
elif len(floating_present) == 1:
    print(f'{get_formatted_time()}: Only 1 floating IP is present')
    print(f'{get_formatted_time()}: Creating another floating IP and using the available floating IP')
    index = 1
    create_floating_ip2 = subprocess.check_output(['openstack', 'floating', 'ip', 'create', 'ext-net', '-f', 'value', '--column', 'floating_ip_address']).decode().strip()
    f1 = floating_present[0]
    f2 = create_floating_ip2
    print(f'{get_formatted_time()}: {f1} created for bastion')
    print(f'{get_formatted_time()}: {f2} created for HAproxys')
else:
    print(f'{get_formatted_time()}: Floating IPs are available')
    index = 1
    f1 = floating_present[0]
    f2 = floating_present[1]
    print(f'{get_formatted_time()}: Floating IP {index}: {f1} saved to floating{index}')
    index += 1
    print(f'{get_formatted_time()}: Floating IP {index}: {f2} saved to floating{index}')

print(f'{get_formatted_time()}: {f1} for bastion')
print(f'{get_formatted_time()}: {f2} for HAproxies')

# Write Haproxies floatingip to file 
with open('proxyip', 'w') as file:
    file.write(f2 + '\n')


#Checking and Creating Virtual Port
port_list = "openstack port show {tag}_viprt"
port_name = subprocess.run(port_list, shell=True, capture_output=True, text=True).stdout

print(f"{get_formatted_time()}: checking for {tag}_viprt in the OpenStack project..")

if f"{tag}_viprt" in port_name:
    port_name = f"{tag}_viprt"
    print(f"{get_formatted_time()}: {tag}_viprt found")
else:
    print(f'{get_formatted_time()}: Creating a virtual port')
    command1 = f"openstack port create --network={tag}_network --fixed-ip subnet={tag}_network-subnet --security-group {tag}_security-group {tag}_viprt"
    subprocess.run(command1, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
 
    # Execute add_vip_fip command
    add_vip_fip = f"openstack floating ip set --port {tag}_viprt {f2}"
    subprocess.run(add_vip_fip, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Extract fixed IP of the virtual port
    print(f'{get_formatted_time()}: Extracting ip of a virtual port')
    command_show_port =f"openstack port show {tag}_viprt -f value -c fixed_ips"
    output = subprocess.check_output(command_show_port, shell=True).decode().strip()

    # Convert the output string to a Python list using ast.literal_eval()
    port_info = ast.literal_eval(output)

    # Extract the IP address from the first dictionary in the list
    addrvip = port_info[0]['ip_address']
 
    # Write addrvip to file vipaddr
    with open('vipaddr', 'w') as file:
        file.write(addrvip + '\n')

    # Update the virtual port
    prtupdt = f"openstack port set --allowed-address ip-address={f2} {tag}_viprt"
    subprocess.run(prtupdt, shell=True)

    # Extract fixed IPs of the proxy servers
    command_show_server1 = f"openstack server show {tag}_proxy1 -c addresses"
    output_server1 = subprocess.check_output(command_show_server1, shell=True).decode().strip().split('\n')
    HAPfixedip = output_server1[3].split('=')[1].strip().rstrip('|')

    command_show_server2 = f"openstack server show {tag}_proxy2 -c addresses"
    output_server2 = subprocess.check_output(command_show_server2, shell=True).decode().strip().split('\n')
    HAPfixedip2 = output_server2[3].split('=')[1].strip().rstrip('|')
    print(f'{get_formatted_time()}: {HAPfixedip} -> proxy1')
    print(f'{get_formatted_time()}: {HAPfixedip2} -> proxy2')
    # Update ports
    print(f'{get_formatted_time()}: Updating ports')
    # Command 1
    command1 = ["/usr/bin/openstack", "port", "list", "--fixed-ip", f"ip-address={HAPfixedip}", "-c", "ID", "-f", "value"]
    output1 = subprocess.check_output(command1, shell=False, encoding="utf-8").strip()
    pid_HA1 = output1 
    # Command 2
    command2 = ["/usr/bin/openstack", "port", "list", "--fixed-ip", f"ip-address={HAPfixedip2}", "-c", "ID", "-f", "value"]
    output2 = subprocess.check_output(command2, shell=False, encoding="utf-8").strip()
    pid_HA2 = output2 
    print(f'{get_formatted_time()}: {pid_HA1} -> proxy1')
    print(f'{get_formatted_time()}: {pid_HA2} -> proxy2')
    # Check if port IDs are found
    if not pid_HA1:
        print("Error: Port ID 1 not found.")
        exit(1)
    if not pid_HA2:
        print("Error: Port ID 2 not found.")
        exit(1)

    update_port1 = ["/usr/bin/openstack", "port", "set", pid_HA1, "--allowed-address", f"ip-address={addrvip}"]
    update_port2 = ["/usr/bin/openstack", "port", "set", pid_HA2, "--allowed-address", f"ip-address={addrvip}"]

    try:
        subprocess.run(update_port1, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command 1: {e}")
    
    try:
        subprocess.run(update_port2, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command 2: {e}")


 # Assign floating IP to bastion
assign_floating_ip_bastion = f"openstack server add floating ip {tag}_bastion {f1}"
subprocess.run(assign_floating_ip_bastion, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
 
print(f"{get_formatted_time()}: Assigned floating IP to bastion")

print(f"{get_formatted_time()}: all nodes are done..")

# Build SSH config file
ssh_config_content = f"""Host {tag}_bastion
  HostName {f1}
  User ubuntu
  IdentityFile ~/.ssh/id_rsa
  UserKnownHostsFile=/dev/null
  StrictHostKeyChecking no
  PasswordAuthentication no

Host {tag}_proxy1
  HostName {HAPfixedip}
  User ubuntu
  IdentityFile ~/.ssh/id_rsa
  UserKnownHostsFile=~/dev/null
  StrictHostKeyChecking no
  PasswordAuthentication no
  ProxyJump {tag}_bastion

Host {tag}_proxy2
  HostName {HAPfixedip2}
  User ubuntu
  IdentityFile ~/.ssh/id_rsa
  UserKnownHostsFile=~/dev/null
  StrictHostKeyChecking no
  PasswordAuthentication no
  ProxyJump {tag}_bastion

Host {tag}_node1
  HostName {node_ips[0]}
  User ubuntu
  IdentityFile ~/.ssh/id_rsa
  UserKnownHostsFile=~/dev/null
  StrictHostKeyChecking no
  PasswordAuthentication no
  ProxyJump {tag}_bastion

Host {tag}_node2
  HostName {node_ips[1]}
  User ubuntu
  IdentityFile ~/.ssh/id_rsa
  UserKnownHostsFile=~/dev/null
  StrictHostKeyChecking no
  PasswordAuthentication no
  ProxyJump {tag}_bastion

Host {tag}_node3
  HostName {node_ips[2]}
  User ubuntu
  IdentityFile ~/.ssh/id_rsa
  UserKnownHostsFile=~/dev/null
  StrictHostKeyChecking no
  PasswordAuthentication no 
  ProxyJump {tag}_bastion  
"""

ssh_config_file_path = f"{tag}_SSHconfig"  # Path to the SSH config file
with open(ssh_config_file_path, "w") as ssh_config_file:
    ssh_config_file.write(ssh_config_content)

print(f"{get_formatted_time()}: Building base SSH config file, saved to {tag}_SSHconfig in the current folder")

# Build hosts file
hosts_file_path = "hosts"
with open(hosts_file_path, "w") as hosts_file:
    hosts_file.write("[Bastion]\n")
    hosts_file.write(f"{tag}_bastion \n")

    hosts_file.write("\n[HAproxy]\n")
    hosts_file.write(f"{tag}_proxy1 \n")
    hosts_file.write(f"{tag}_proxy2 \n")
    hosts_file.write("\n")
    
    hosts_file.write("[webservers]\n")
    hosts_file.write(f"{tag}_node1\n")
    hosts_file.write(f"{tag}_node2\n")
    hosts_file.write(f"{tag}_node3\n")
    
    hosts_file.write("\n[primary_proxy]\n")
    hosts_file.write(f"{tag}_proxy1 \n")
    
    hosts_file.write(f"\n[backup_proxy]\n")
    hosts_file.write(f"{tag}_proxy2\n")
    hosts_file.write("\n[all:vars]\nansible_user=ubuntu \n")
    hosts_file.write("ansible_ssh_private_key_file=~/.ssh/id_rsa \n")
    hosts_file.write(f"ansible_ssh_common_args=' -F {tag}_SSHconfig ' \n")

# Run Ansible playbook for deplyoment
print(f"{get_formatted_time()}: Running playbook")
ansible_playbook = f"ansible-playbook -i hosts --ssh-common-args='-F./{tag}_SSHconfig' site.yaml"
playbook_execution = subprocess.run(ansible_playbook, shell=True,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if playbook_execution.returncode == 0:
    print(f"{get_formatted_time()}: Done, solution has been deployed")
else:
    print(f"{get_formatted_time()}: Error executing playbook so running again with output on terminal")
    ansible_playbook1 = f"ansible-playbook -i hosts site.yaml"
    playbook_execution1 = subprocess.run(ansible_playbook1, shell=True)
    if playbook_execution1.returncode == 0:
        print(f"{get_formatted_time()}: OK")
    else: 
        print(f"{get_formatted_time()}: Error executing playbook.") 
        exit(1)   
        
# Define the URL to browse
url = "http://" + f2

result = subprocess.run("openstack server list -c Name -f value", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
existing_nodes = re.findall(rf"^{tag}_node\d+", result.stdout, re.MULTILINE)

for i, node in enumerate(existing_nodes, start=1):
    response = requests.get(url, proxies={"http": f2, "https": f2})

    # Print the page content
    print(f"{get_formatted_time()}: Response {i}: {response.content.decode()}")

print(f"{get_formatted_time()}: OK")

