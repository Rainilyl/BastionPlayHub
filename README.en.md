# BastionPlayHub

[中文](README.md) | [English](README.en.md)

BastionPlayHub is a terminal bastion host, more than just a traditional bastion host, currently in its early stages with ongoing updates to its features. Presently, it includes the following functionalities:

- Batch viewing and management of hosts
- Automatic synchronization and updating of host list information (coming soon)
- Execution of playbooks on individual or multiple hosts defined by `host` or `hosts` (functionality under verification, coming soon)
- File upload and download capabilities

## Features

1. **Remote Control**: Remote operation of individual or multiple hosts using custom commands.
2. **Playbook Execution**: Execution of automated tasks on specified hosts or host groups.
3. **File Transfer**: Upload and download files between local and remote hosts.





项目结构：
BastionPlayHub
├── config
│   └── servers.yml
├── requirements.txt
├── restricted_shell.py
├── scripts
│   ├── connect.py
│   ├── download.py
│   ├── execute_ansible.py
│   ├── help.py
│   └── upload.py
└── setup
    └── deploy.sh


## Installation

Follow these steps to install:

1. Clone this repository:
    ```bash
    git clone git@github.com:Rainilyl/BastionPlayHub.git
    ```
2. Navigate to the project directory:
    ```bash
    cd BastionPlayHub
    ```
3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Deployment:
    ```bash
    sh setup/deploy.sh
    ```

## Usage

### Help

To view available commands, run:

```bash
help
