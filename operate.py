#!/usr/bin/env python3

from dotenv import load_dotenv
import os
import sys
import subprocess
import re
import time
import datetime
import requests

# Function to get the current formatted time
def get_formatted_time():
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_time

# Function to check if a server is running
def is_server_running(server_name):
    result = subprocess.run(f"openstack server show {server_name}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return "ACTIVE" in result.stdout

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

# Define server names
server_names = [f"{tag}_node{i+1}" for i in range(10)]

while True:
    # Read server.conf to get the required number of nodes
    with open('server.conf', 'r') as file:
        config_lines = file.readlines()

    # Extract the number of nodes required from server.conf
    num_nodes = None
    for line in config_lines:
        if "num_nodes =" in line:
            num_nodes_match = re.search(r'num_nodes = (\d+)', line)
            if num_nodes_match:
                num_nodes = int(num_nodes_match.group(1))
            break

    # Calculate the number of new nodes to create
    if num_nodes is None:
        print(f"{get_formatted_time()}: Unable to find the required number of nodes in server.conf.")
        sys.exit(1)

    print(f"{get_formatted_time()}: Reading server.conf, we need {num_nodes} nodes.")
    
    result = subprocess.run("openstack server list -c Name -f value", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    existing_nodes = re.findall(rf"^{tag}_node\d+", result.stdout, re.MULTILINE)
    print(f"{get_formatted_time()}: Checking solution, we have: {len(existing_nodes)} nodes.Sleeping..")
    time.sleep(30)
        
    if len(existing_nodes) == num_nodes:
        # Update the number of nodes in server.conf
        config_lines = [line.replace(f"num_nodes = {num_nodes}", f"num_nodes = {num_nodes + 1}") for line in config_lines]
        with open('server.conf', 'w') as file:
            file.writelines(config_lines)
        time.sleep(30)
    elif len(existing_nodes) > num_nodes:
        extra_nodes = len(existing_nodes) - num_nodes
        print(f"{get_formatted_time()}: we have {extra_nodes} extra nodes ")
        
        # Sort the existing nodes in descending order
        existing_nodes_sorted = sorted(existing_nodes, reverse=True)
    
        remove_count = 0  # Counter for removed nodes
    
        for node in existing_nodes_sorted:
            if remove_count >= extra_nodes:
                break  # Stop removing nodes once the extra nodes are removed
        
            run = subprocess.run(f"openstack server delete {node}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            time.sleep(20)
        
            if run.returncode == 0:
                remove_count += 1
                print(f"{get_formatted_time()}: deleting {node} .. ")
            else:
                print(f"{get_formatted_time()}: failed to delete {node}. Error: {run.stderr}")
            
    elif len(existing_nodes) < num_nodes:
        num_new_nodes = num_nodes - len(existing_nodes)
        
        # Get the missing server names
        missing_server_names = [name for name in server_names if name not in existing_nodes]
        
        if len(missing_server_names) > 0:
            for missing_server_name, _ in zip(missing_server_names, range(num_new_nodes)):
                print(f"{get_formatted_time()}: Detecting lost node: {missing_server_name}.")
                create_server = f"openstack server create --image 'Ubuntu 20.04 Focal Fossa x86_64' --key-name {tag}_key --flavor '1C-2GB-50GB' --network {tag}_network --security-group {tag}_security-group {missing_server_name}"
                create_server1 = subprocess.run(create_server, shell=True, stdout=subprocess.DEVNULL, stderr=True)
                existing_nodes.append(missing_server_name)
                if create_server1.returncode == 0:
                    print(f"{get_formatted_time()}: Created: {missing_server_name}")
                    time.sleep(10)
                else:
                    print(f"{get_formatted_time()}:{server_name} not created...")

        print(f"{get_formatted_time()}: Checking if servers are running...")

        # Check if all servers are running
        all_servers_running = all(is_server_running(server) for server in existing_nodes)

        if all_servers_running:
            print(f"{get_formatted_time()}: All servers are running.")
        else:
            non_running_servers = [server for server in existing_nodes if not is_server_running(server)]
            print(f"{get_formatted_time()}: {', '.join(non_running_servers)} are not running")

            # Attempt to start non-running servers
            for server in non_running_servers:
                print(f"{get_formatted_time()}: Attempting to start server {server}...")
                start_command = f"openstack server start {server}"
                start_result = subprocess.run(start_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
             
                if start_result.returncode == 0:
                    print(f"{get_formatted_time()}: Server {server} started successfully.")
                else:
                    print(f"{get_formatted_time()}: Failed to start server {server}. Error: {start_result.stderr}")
 
            print(f"{get_formatted_time()}: Waiting for 30 seconds...")
            time.sleep(30)

        # Check if bastion and proxy servers are active, and start them if not
        bastion_server_name = f"{tag}_bastion"
        proxy1_server_name = f"{tag}_proxy1"
        proxy2_server_name = f"{tag}_proxy2"

        if not is_server_running(bastion_server_name):
            start_result = subprocess.run(f"openstack server start {bastion_server_name}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if start_result.returncode == 0:
                print(f"{get_formatted_time()}: {bastion_server_name} are not running")
                print(f"{get_formatted_time()}: Bastion server {bastion_server_name} started successfully.")
            else:
                print(f"{get_formatted_time()}: Failed to start bastion server {bastion_server_name}. Error: {start_result.stderr}")

        if not is_server_running(proxy1_server_name):
            start_result = subprocess.run(f"openstack server start {proxy1_server_name}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if start_result.returncode == 0:
                print(f"{get_formatted_time()}: {proxy1_server_name} are not running")
                print(f"{get_formatted_time()}: Proxy server {proxy1_server_name} started successfully.")
            else:
                print(f"{get_formatted_time()}: Failed to start proxy server {proxy1_server_name}. Error: {start_result.stderr}")

        if not is_server_running(proxy2_server_name):
            start_result = subprocess.run(f"openstack server start {proxy2_server_name}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if start_result.returncode == 0:
                print(f"{get_formatted_time()}: {proxy2_server_name} are not running")
                print(f"{get_formatted_time()}: Proxy server {proxy2_server_name} started successfully.")
            else:
                print(f"{get_formatted_time()}: Failed to start proxy server {proxy2_server_name}. Error: {start_result.stderr}")

        
        #To fetch ipaddresses           
        command_show_server1 = f"openstack server show {tag}_proxy1 -c addresses"
        output_server1 = subprocess.check_output(command_show_server1, shell=True).decode().strip().split('\n')
        HAPfixedip = output_server1[3].split('=')[1].strip().rstrip('|')

        command_show_server2 = f"openstack server show {tag}_proxy2 -c addresses"
        output_server2 = subprocess.check_output(command_show_server2, shell=True).decode().strip().split('\n')
        HAPfixedip2 = output_server2[3].split('=')[1].strip().rstrip('|')
        
        command_show_server3 = f"openstack server show {tag}_bastion -c addresses"
        output_server3 = subprocess.check_output(command_show_server3, shell=True, stderr=subprocess.STDOUT, text=True)
        addresses = output_server3.strip().split('\n')[3].split('=')[1].rstrip('|').split(',')
        floating_ip = None

        for address in addresses:
            if '.' in address:
                floating_ip = address.strip()
        
        # Build SSH config file
        ssh_config_content = f"""Host {tag}_bastion
  HostName {floating_ip}
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
        """
        # Add node entries to SSH config file
 
        result1 = subprocess.run(f"openstack server list -c Name -f value", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        totalnodes = re.findall(rf"^{tag}_node\d+", result1.stdout, re.MULTILINE)
        loop = len(totalnodes) + 1
        for i in range(1, loop + 1):
            nodes_nam = f"{tag}_node{i}"

            try:
                ip_address = subprocess.check_output(f"openstack server list --name {nodes_nam} -c Networks -f value", shell=True).decode().strip()
                ip_match = re.search(r'\d+\.\d+\.\d+\.\d+', ip_address)
                if ip_match:
                    ip_address = ip_match.group(0)
                else:
                    config_complete = False
                    continue     
            except subprocess.CalledProcessError:
                print(f"{nodes_nam} doesn't exist.")
                continue
                
            ssh_config_content += f"""
Host {tag}_node{i}
  HostName {ip_address}
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
            result2 = subprocess.run("openstack server list -c Name -f value", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            totalnodes1 = re.findall(rf"^{tag}_node\d+", result2.stdout, re.MULTILINE)
            loop1 = len(totalnodes1) + 1
            for j in range(1, loop1 + 1):
                nodes_nam1 = f"{tag}_node{j}"

                try:
                    ip_address1 = subprocess.check_output(f"openstack server list --name {nodes_nam1} -c Networks -f value", shell=True).decode().strip()
                    ip_match1 = re.search(r'\d+\.\d+\.\d+\.\d+', ip_address1)
                    if ip_match1:
                        ip_address1 = ip_match1.group(0)
                    else:
                        config_complete = False
                        continue     
                except subprocess.CalledProcessError:
                    print(f"Node {nodes_nam1} doesn't exist.")
                    continue 
                
                hosts_file.write(f"{tag}_node{j}\n")
        
            hosts_file.write("\n[primary_proxy]\n")
            hosts_file.write(f"{tag}_proxy1\n")
    
            hosts_file.write("\n[backup_proxy]\n")
            hosts_file.write(f"{tag}_proxy2\n")
    
            hosts_file.write("\n[all:vars]\n")
            hosts_file.write("ansible_user=ubuntu\n")
            hosts_file.write("ansible_ssh_private_key_file=~/.ssh/id_rsa\n")
            hosts_file.write(f"ansible_ssh_common_args='-F {tag}_SSHconfig'\n")

  
        print(f"{get_formatted_time()}: Updated {tag}_SSHconfig") 
        
        # Run Ansible playbook for deployment
        print(f"{get_formatted_time()}: Running playbook")
        
        ansible_playbook = f"ansible-playbook -i hosts --ssh-common-args='-F./{tag}_SSHconfig' site1.yaml"
        playbook = subprocess.run(ansible_playbook, shell=True, stdout=subprocess.DEVNULL, stderr=True)
        if playbook.returncode == 0:
            print(f"{get_formatted_time()}: Done, solution has been deployed")
        else:
            print(f"{get_formatted_time()}: Error executing playbook so running again with output on terminal")
            ansible_playbook1 = f"ansible-playbook -i hosts site1.yaml"
            playbook_execution1 = subprocess.run(ansible_playbook1, shell=True)
            if playbook_execution1.returncode == 0:
                print(f"{get_formatted_time()}: OK")
            else:
                print(f"{get_formatted_time()}:Error in executing playbook")
        
        # Read the file and save the IP address
        with open('proxyip', 'r') as file:
            ip_address = file.read().strip()

        print(f"{get_formatted_time()}: Validates Operation")
       
        # Define the URL to browse
        url = "http://" + ip_address

        result = subprocess.run("openstack server list -c Name -f value ", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        existing_nodes_all = re.findall(rf"^{tag}_node\d+", result.stdout, re.MULTILINE)

        for i, node in enumerate(existing_nodes_all, start=0):
            response = requests.get(url, proxies={"http": ip_address, "https": ip_address})

            # Print the page content
            print(f"{get_formatted_time()}: Response {i+1}: {response.content.decode()}")

        print(f"{get_formatted_time()}: OK")

       

