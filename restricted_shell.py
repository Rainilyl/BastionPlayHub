#!/usr/bin/env python3

import sys
import io
import os
import yaml
import subprocess

sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

scripts_dir = '/usr/local/bin/BastionPlayHub/scripts'
config_file_path = '/usr/local/bin/BastionPlayHub/config/servers.yml'

print(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")
print(f"BastionPlayHub directory: {os.path.dirname(os.path.abspath(__file__))}")
print(f"Scripts directory: {scripts_dir}")
print(f"Configuration file: {config_file_path}")

if not os.path.isdir(scripts_dir):
    print(f"Error: Directory {scripts_dir} does not exist.")
    sys.exit(1)

sys.path.insert(0, scripts_dir)

try:
    from help import show_help
except ImportError as e:
    print(f"Cannot import help module: {e}")
    sys.exit(1)

def load_servers():
    try:
        with open(config_file_path, 'r') as f:
            config = yaml.safe_load(f)
            return config.get('servers', [])
    except Exception as e:
        print(f"Cannot load configuration file: {e}")
        return []

def find_servers(prefix):
    servers = load_servers()
    matching_servers = [s for s in servers if prefix in s['name'] or prefix in s['ip']]
    return matching_servers

def connect_to_server(ip):
    try:
        print(f"Trying to connect to {ip}...")
        result = subprocess.run(['ssh', '-l', 'root', ip], check=True)
        print(f"Successfully connected to {ip}.")
    except subprocess.CalledProcessError as e:
        print(f"Connection failed: {e.stderr}")
    except Exception as e:
        print(f"Connection error: {e}")

def main():
    while True:
        try:
            command = input("Enter command: ").strip()
            if command == 'help':
                show_help()
            elif command.startswith('c '):
                prefix = command[2:].strip()
                if prefix:
                    servers = find_servers(prefix)
                    if len(servers) == 0:
                        print("No matching hosts found.")
                    else:
                        if any(ip == prefix for ip in [s['ip'] for s in servers]) or any(name == prefix for name in [s['name'] for s in servers]):
                            connect_to_server(prefix)
                        else:
                            for server in servers:
                                print(f"Hostname: {server['name']}, IP: {server['ip']}")
                else:
                    print("Please enter a hostname or IP prefix to connect to.")
            elif command == 'exit':
                break
            else:
                print(f"Unrecognized command: {command}")
        except UnicodeEncodeError:
            print("Encoding error, please ensure the terminal supports UTF-8 encoding.")



if __name__ == "__main__":
    main()