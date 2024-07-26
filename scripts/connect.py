import yaml
import paramiko

def load_servers():
    with open('/etc/BastionPlayHub/servers.yml', 'r') as file:
        servers = yaml.safe_load(file)['servers']
    return servers

def filter_servers(prefix):
    servers = load_servers()
    return [server for server in servers if server['name'].startswith(prefix)]

def connect_to_server(server_name):
    servers = load_servers()
    server = next((s for s in servers if s['name'] == server_name), None)
    if server:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server['ip'], username='your_username')
        ssh.invoke_shell()
    else:
        print("Server not found")