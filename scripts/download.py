import paramiko

def download_file(server_ip, remote_file, local_path):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(server_ip, username='your_username')
    
    sftp = ssh.open_sftp()
    sftp.get(remote_file, local_path)
    sftp.close()
    ssh.close()
