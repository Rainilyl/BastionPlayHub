import paramiko

def upload_file(server_ip, local_file, remote_path):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(server_ip, username='your_username')
    
    sftp = ssh.open_sftp()
    sftp.put(local_file, remote_path)
    sftp.close()
    ssh.close()