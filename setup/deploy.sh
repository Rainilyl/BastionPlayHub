#!/bin/bash

if [[ $EUID -ne 0 ]]; then
   echo "Please run this script as root."
   exit 1
fi

DEFAULT_USERNAME="bastion_user"
USERNAME=${1:-$DEFAULT_USERNAME}

if ! command -v python3 &> /dev/null
then
    echo "Python 3 not found, installing Python 3..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y python3
    elif command -v yum &> /dev/null; then
        sudo yum install -y python3
    else
        echo "Cannot automatically install Python 3, please install it manually."
        exit 1
    fi
fi

if ! command -v pip3 &> /dev/null
then
    echo "pip3 not found, installing pip3..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get install -y python3-pip
    elif command -v yum &> /dev/null; then
        sudo yum install -y python3-pip
    else
        echo "Cannot automatically install pip3, please install it manually."
        exit 1
    fi
fi

pip3 install --upgrade pip
pip3 install setuptools_rust

if command -v apt-get &> /dev/null; then
    sudo apt-get install -y libffi-dev python3-dev
elif command -v yum &> /dev/null; then
    sudo yum install -y libffi-devel python3-devel
else
    echo "Cannot automatically install libffi-dev and python3-dev, please install these dependencies manually."
    exit 1
fi

if ! command -v gcc &> /dev/null
then
    echo "gcc not found, installing gcc..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get install -y gcc
    elif command -v yum &> /dev/null; then
        sudo yum install -y gcc
    else
        echo "Cannot automatically install gcc, please install it manually."
        exit 1
    fi
fi

pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Failed to install Python dependencies, please check the issue and try again."
    exit 1
fi

if [ -d "/usr/local/bin/BastionPlayHub" ]; then
    cp -rf * /usr/local/bin/BastionPlayHub/
else
    mkdir -p /usr/local/bin/BastionPlayHub
    cp -rf * /usr/local/bin/BastionPlayHub/
fi

cp restricted_shell.py /usr/local/bin/restricted_shell.py
chmod +x /usr/local/bin/restricted_shell.py

if id "$USERNAME" &>/dev/null; then
    echo "User $USERNAME already exists."
else
    useradd -m -s /usr/local/bin/restricted_shell.py $USERNAME
    adduser --disabled-password --gecos "" $USERNAME
    echo "User $USERNAME created."
fi

if [ ! -f /home/$USERNAME/.ssh/id_rsa ]; then
    echo "Generating SSH key pair..."
    sudo -u $USERNAME ssh-keygen -t rsa -b 2048 -f /home/$USERNAME/.ssh/id_rsa -N ""
fi

if [ -f /home/$USERNAME/.ssh/id_rsa.pub ]; then
    echo "Configuring SSH public key..."
    mkdir -p /home/$USERNAME/.ssh
    cat /home/$USERNAME/.ssh/id_rsa.pub >> /home/$USERNAME/.ssh/authorized_keys
    chmod 700 /home/$USERNAME/.ssh
    chmod 600 /home/$USERNAME/.ssh/authorized_keys
    chown -R $USERNAME:$USERNAME /home/$USERNAME/.ssh
else
    echo "SSH public key file does not exist, please check the key generation process."
    exit 1
fi

echo "Deployment completed."