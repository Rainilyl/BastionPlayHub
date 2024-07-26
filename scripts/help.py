def show_help():
    help_text = """
    Available commands:
    1. help - Show available commands and their functions
    2. c <prefix> - Connect to a server via the BastionPlayHub, supports filtering by hostname
    3. as hosts <path_to_yaml> - Execute Ansible playbook from GitHub repository
    4. upload <local_file> <remote_path> - Upload file to target server
    5. download <remote_file> <local_path> - Download file to BastionPlayHub
    """
    print(help_text)