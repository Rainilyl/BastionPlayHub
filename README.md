# BastionPlayHub

[中文](README.md) | [English](README.en.md)

轻量级终端堡垒机。SSH 登录即进入受限 Shell，通过预定义命令管理服务器、执行 Playbook、传输文件。

## 特性

- 受限 Shell，无法执行任意命令
- IP / 主机名前缀匹配快速连接
- 单台或批量执行 Ansible Playbook
- ZMODEM 直传文件，不落盘堡垒机
- 多用户会话隔离，退出自动清理
- 支持远程代码仓库同步或本地 Playbook

## 架构

```
![架构图](./docs/architecture.png)
```

## 部署

```bash
git clone git@github.com:Rainilyl/BastionPlayHub.git
cd BastionPlayHub
sudo bash setup/deploy.sh [用户名]    # 默认 bastion_user
```

## 部署后配置

部署完成后根据终端提示完成以下配置：

**必选**

1. 编辑服务器列表
2. 分发密钥到服务器（免密连接）
3. 配置用户登录堡垒机认证

**可选**

- 配置远程代码仓库同步 Playbook（如 GitLab）
- 修改 Playbook 存储路径

## 使用

```bash
ssh bastion_user@<堡垒机IP>
```

| 命令 | 说明 |
|------|------|
| `c` | 显示所有服务器 |
| `c <IP\|主机名>` | 连接服务器（前缀匹配） |
| `vi host` / `vi hosts` | 编辑目标主机 |
| `as host <playbook>` | 单台执行 Playbook |
| `as hosts <playbook>` | 批量执行 Playbook |
| `ls playbook` | 列出可用 Playbook |
| `upload <IP\|hosts>` | 上传文件 |
| `download <IP\|host>` | 下载文件 |
| `clear` | 清屏 |
| `exit` | 退出 |
