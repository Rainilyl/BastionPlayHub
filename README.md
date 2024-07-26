# BastionPlayHub

[中文](README.md) | [English](README.en.md)

BastionPlayHub 是一个终端堡垒机，具有以下功能：

- 批量查看和管理主机
- 自动同步更新主机列表信息（等待更新）
- 通过定义host或hosts，实现单个或批量执行playbook（功能验证中，等待更新）
- 上传和下载文件

## 特性

1. **远程控制**: 使用自定义指令远程操作单个或多个主机。
2. **执行 Playbook**: 在指定主机或主机组上运行自动化任务。
3. **文件传输**: 在本地和远程主机之间上传和下载文件。




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

## 安装

请按照以下步骤进行安装：

1. 克隆本仓库：
    ```bash
    git clone git@github.com:Rainilyl/BastionPlayHub.git
    ```
2. 进入项目目录：
    ```bash
    cd BastionPlayHub
    ```
3. 安装依赖：
    ```bash
    pip install -r requirements.txt
    ```

4. 部署
    ```bash
    sh setup/deploy.sh
    ```


## 使用

### 帮助

查看可执行的指令：

```bash
help
