#!/usr/bin/env python3

import sys
import os
import subprocess
import signal
import tempfile
import atexit
import shutil
import readline
import glob as globmod
import yaml

BASE_DIR = '/usr/local/bin/BastionPlayHub'
CONFIG_FILE = os.path.join(BASE_DIR, 'config', 'servers.yml')
PLAYBOOK_DIR = '/data/playbooks'

SESSION_DIR = tempfile.mkdtemp(prefix='bastion_session_')
HOST_FILE = os.path.join(SESSION_DIR, 'host')
HOSTS_FILE = os.path.join(SESSION_DIR, 'hosts')


def cleanup_session():
    try:
        if os.path.isdir(SESSION_DIR):
            shutil.rmtree(SESSION_DIR)
    except Exception:
        pass


atexit.register(cleanup_session)


def load_servers():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config.get('servers', [])
    except Exception as e:
        print(f"[错误] 无法加载服务器配置: {e}")
        return []


def find_servers(prefix):
    servers = load_servers()
    matched = []
    for s in servers:
        if (s.get('ip', '').startswith(prefix) or
            s.get('name', '').startswith(prefix) or
            s.get('public_ip', '').startswith(prefix)):
            matched.append(s)
    return matched


def str_width(s):
    import unicodedata
    w = 0
    for ch in s:
        if unicodedata.east_asian_width(ch) in ('W', 'F'):
            w += 2
        else:
            w += 1
    return w


def pad_str(s, width):
    return s + ' ' * (width - str_width(s))


def display_servers_table(servers):
    if not servers:
        print("无可用服务器。")
        return

    has_public = any(s.get('public_ip') for s in servers)

    h_name = "主机名"
    h_ip = "内网IP"
    h_pub = "公网IP"

    name_width = max(str_width(h_name), max(str_width(s.get('name', '')) for s in servers))
    ip_width = max(str_width(h_ip), max(str_width(s.get('ip', '')) for s in servers))

    if has_public:
        pub_width = max(str_width(h_pub), max(str_width(s.get('public_ip', '') or '') for s in servers))

    if has_public:
        top = f"┌─{'─' * name_width}─┬─{'─' * ip_width}─┬─{'─' * pub_width}─┐"
        sep = f"├─{'─' * name_width}─┼─{'─' * ip_width}─┼─{'─' * pub_width}─┤"
        bot = f"└─{'─' * name_width}─┴─{'─' * ip_width}─┴─{'─' * pub_width}─┘"
        header = f"│ {pad_str(h_name, name_width)} │ {pad_str(h_ip, ip_width)} │ {pad_str(h_pub, pub_width)} │"
    else:
        top = f"┌─{'─' * name_width}─┬─{'─' * ip_width}─┐"
        sep = f"├─{'─' * name_width}─┼─{'─' * ip_width}─┤"
        bot = f"└─{'─' * name_width}─┴─{'─' * ip_width}─┘"
        header = f"│ {pad_str(h_name, name_width)} │ {pad_str(h_ip, ip_width)} │"

    print(top)
    print(header)
    print(sep)
    for s in servers:
        name = pad_str(s.get('name', ''), name_width)
        ip = pad_str(s.get('ip', ''), ip_width)
        if has_public:
            pub = pad_str(s.get('public_ip', '') or '', pub_width)
            print(f"│ {name} │ {ip} │ {pub} │")
        else:
            print(f"│ {name} │ {ip} │")
    print(bot)


def connect_server(target):
    servers = load_servers()

    exact = None
    for s in servers:
        if s.get('ip') == target or s.get('name') == target or s.get('public_ip') == target:
            exact = s
            break

    if exact:
        ip = exact['ip']
        print(f"正在连接 {exact['name']} ({ip}) ...")
        os.system(f'ssh -o StrictHostKeyChecking=no root@{ip}')
        return

    matched = find_servers(target)
    if not matched:
        print("未找到匹配的主机。")
    elif len(matched) == 1:
        s = matched[0]
        print(f"正在连接 {s['name']} ({s['ip']}) ...")
        os.system(f"ssh -o StrictHostKeyChecking=no root@{s['ip']}")
    else:
        print("匹配到多台主机，请补全输入：")
        display_servers_table(matched)


def edit_file(filepath):
    if not os.path.exists(filepath):
        open(filepath, 'w').close()
    os.system(f'vi {filepath}')


def read_host_file(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    hosts = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            hosts.append(line)
    return hosts


def list_playbooks(subdir=''):
    search_dir = os.path.join(PLAYBOOK_DIR, subdir) if subdir else PLAYBOOK_DIR
    if not os.path.isdir(search_dir):
        print(f"[错误] 仓库目录不存在: {search_dir}")
        print("请确认 Playbook 目录已配置且包含 .yml/.yaml 文件")
        return []

    playbooks = []
    for root, dirs, files in os.walk(search_dir):
        for f in files:
            if f.endswith(('.yml', '.yaml')):
                rel_path = os.path.relpath(os.path.join(root, f), PLAYBOOK_DIR)
                playbooks.append(rel_path)
    return sorted(playbooks)


def execute_playbook(hosts, playbook_name):
    playbook_path = os.path.join(PLAYBOOK_DIR, playbook_name)

    if not os.path.isfile(playbook_path):
        available = list_playbooks()
        matched = [p for p in available if playbook_name in p]
        if not matched:
            print(f"[错误] Playbook 不存在: {playbook_name}")
            print("可用的 Playbook:")
            for p in available[:20]:
                print(f"  {p}")
            if len(available) > 20:
                print(f"  ... 共 {len(available)} 个")
            return
        elif len(matched) == 1:
            playbook_path = os.path.join(PLAYBOOK_DIR, matched[0])
            print(f"匹配到: {matched[0]}")
        else:
            print("匹配到多个 Playbook：")
            for i, p in enumerate(matched, 1):
                print(f"  {i}. {p}")
            try:
                choice = input("请选择序号 (直接回车取消): ").strip()
                if choice.isdigit() and 1 <= int(choice) <= len(matched):
                    playbook_path = os.path.join(PLAYBOOK_DIR, matched[int(choice) - 1])
                else:
                    return
            except (EOFError, KeyboardInterrupt):
                print()
                return

    if not hosts:
        print("[错误] 目标主机列表为空，请先用 'vi host' 或 'vi hosts' 编辑目标主机。")
        return

    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False, prefix='bastion_inv_') as inv:
        inv.write("[targets]\n")
        for h in hosts:
            inv.write(f"{h} ansible_user=root\n")
        inv_path = inv.name

    try:
        print(f"执行 Playbook: {os.path.relpath(playbook_path, PLAYBOOK_DIR)}")
        print(f"目标主机: {', '.join(hosts)}")
        print("-" * 50)

        cmd = [
            'ansible-playbook',
            '-i', inv_path,
            playbook_path
        ]
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print(f"\n[警告] Playbook 执行返回码: {result.returncode}")
    except FileNotFoundError:
        print("[错误] 未找到 ansible-playbook 命令，请确认已安装 Ansible。")
    except Exception as e:
        print(f"[错误] 执行失败: {e}")
    finally:
        os.unlink(inv_path)


def resolve_target(target):
    if target == 'hosts':
        hosts = read_host_file(HOSTS_FILE)
        if not hosts:
            print("[错误] hosts 文件为空，请先用 'vi hosts' 编辑。")
        return hosts
    elif target == 'host':
        hosts = read_host_file(HOST_FILE)
        if not hosts:
            print("[错误] host 文件为空，请先用 'vi host' 编辑。")
        return hosts
    else:
        servers = load_servers()
        for s in servers:
            if s.get('ip') == target or s.get('name') == target:
                return [s['ip']]
        return [target]


def do_upload(target):
    hosts = resolve_target(target)
    if not hosts:
        return

    try:
        remote_path = input("远程目标路径: ").strip()
        if not remote_path:
            print("[错误] 远程路径不能为空。")
            return
    except (EOFError, KeyboardInterrupt):
        print()
        return

    upload_tmp = os.path.join(SESSION_DIR, 'upload')
    os.makedirs(upload_tmp, exist_ok=True)

    print("请在终端中选择要上传的文件 (ZMODEM)...")
    ret = os.system(f'cd {upload_tmp} && rz -be 2>/dev/null')
    if ret != 0:
        print("[提示] 文件接收取消或失败，请确认终端支持 ZMODEM。")
        return

    received_files = os.listdir(upload_tmp)
    if not received_files:
        print("[提示] 未接收到文件。")
        return

    for fname in received_files:
        local_tmp_path = os.path.join(upload_tmp, fname)
        for host in hosts:
            print(f"传输 {fname} → {host}:{remote_path} ...")
            ret = os.system(
                f"scp -o StrictHostKeyChecking=no '{local_tmp_path}' root@{host}:'{remote_path}' 2>/dev/null"
            )
            if ret == 0:
                print(f"  ✓ {host} 上传成功")
            else:
                print(f"  ✗ {host} 上传失败")
        os.unlink(local_tmp_path)


def do_download(target):
    hosts = resolve_target(target)
    if not hosts:
        return

    if len(hosts) > 1:
        print("下载只支持单台主机，将使用第一个目标。")

    host = hosts[0]
    try:
        remote_path = input("远程文件路径: ").strip()
        if not remote_path:
            print("[错误] 远程路径不能为空。")
            return
    except (EOFError, KeyboardInterrupt):
        print()
        return

    download_tmp = os.path.join(SESSION_DIR, 'download')
    os.makedirs(download_tmp, exist_ok=True)
    filename = os.path.basename(remote_path)
    local_tmp_path = os.path.join(download_tmp, filename)

    print(f"从 {host} 获取 {remote_path} ...")
    ret = os.system(
        f"scp -o StrictHostKeyChecking=no root@{host}:'{remote_path}' '{local_tmp_path}' 2>/dev/null"
    )
    if ret != 0:
        print("✗ 获取文件失败，请确认文件路径正确且有权限。")
        return

    print("正在发送文件到本地 (ZMODEM)...")
    ret = os.system(f"sz -be '{local_tmp_path}' 2>/dev/null")

    if os.path.exists(local_tmp_path):
        os.unlink(local_tmp_path)

    if ret == 0:
        print(f"✓ 下载成功: {filename}")
    else:
        print("✗ 发送到本地取消或失败，请确认终端支持 ZMODEM。")


def show_help():
    help_text = """
╔══════════════════════════════════════════════════════════════╗
║                  BastionPlayHub 堡垒机                       ║
╠══════════════════════════════════════════════════════════════╣
║ 连接服务器:                                                  ║
║   c                   显示所有服务器列表                       ║
║   c <IP或主机名>      连接服务器 (支持前缀补全)               ║
║                                                              ║
║ 编辑目标主机:                                                ║
║   vi host             编辑单台目标主机                        ║
║   vi hosts            编辑多台目标主机列表                    ║
║   cat host            查看当前 host 文件                      ║
║   cat hosts           查看当前 hosts 文件                     ║
║                                                              ║
║ 执行 Playbook:                                               ║
║   as host <playbook>  对 host 中的主机执行 playbook           ║
║   as hosts <playbook> 对 hosts 中的所有主机执行 playbook      ║
║   ls playbook         列出可用的 playbook                     ║
║                                                              ║
║ 文件传输 (ZMODEM, 本地直传目标服务器):                        ║
║   upload <IP>         本地文件 → 指定服务器                   ║
║   upload hosts        本地文件 → hosts 中所有主机批量上传     ║
║   download <IP>       指定服务器 → 本地                       ║
║   download host       host 中的主机 → 本地                    ║
║                                                              ║
║ 其他:                                                        ║
║   clear               清空终端屏幕                            ║
║   help                显示此帮助信息                          ║
║   exit                退出堡垒机                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(help_text)


def handle_sigint(sig, frame):
    print("\n使用 'exit' 退出堡垒机。")


def handle_exit_signal(sig, frame):
    cleanup_session()
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, handle_sigint)
    signal.signal(signal.SIGTERM, handle_exit_signal)
    if hasattr(signal, 'SIGHUP'):
        signal.signal(signal.SIGHUP, handle_exit_signal)

    history_file = os.path.join(SESSION_DIR, '.history')
    readline.set_history_length(500)
    try:
        readline.read_history_file(history_file)
    except FileNotFoundError:
        pass

    atexit.register(lambda: readline.write_history_file(history_file))

    print("\n欢迎使用 BastionPlayHub 堡垒机")
    print("输入 'help' 查看可用命令\n")

    while True:
        try:
            command = input("\033[1;32mbastion>\033[0m ").strip()

            if not command:
                continue

            elif command == 'help':
                show_help()

            elif command in ('exit', 'quit', 'logout'):
                print("再见。")
                break

            elif command == 'clear':
                os.system('clear')

            elif command == 'c':
                servers = load_servers()
                if servers:
                    display_servers_table(servers)
                else:
                    print("服务器列表为空。")
            elif command.startswith('c '):
                target = command[2:].strip()
                if target:
                    connect_server(target)
                else:
                    servers = load_servers()
                    if servers:
                        display_servers_table(servers)
                    else:
                        print("服务器列表为空。")

            elif command in ('vi host', 'vim host'):
                edit_file(HOST_FILE)
            elif command in ('vi hosts', 'vim hosts'):
                edit_file(HOSTS_FILE)

            elif command == 'cat host':
                hosts = read_host_file(HOST_FILE)
                if hosts:
                    print("当前 host 文件内容:")
                    for h in hosts:
                        print(f"  {h}")
                else:
                    print("host 文件为空，请用 'vi host' 编辑。")
            elif command == 'cat hosts':
                hosts = read_host_file(HOSTS_FILE)
                if hosts:
                    print("当前 hosts 文件内容:")
                    for h in hosts:
                        print(f"  {h}")
                else:
                    print("hosts 文件为空，请用 'vi hosts' 编辑。")

            elif command.startswith('as host '):
                playbook = command[8:].strip()
                if not playbook:
                    print("用法: as host <playbook路径>")
                    continue
                hosts = read_host_file(HOST_FILE)
                if not hosts:
                    print("[错误] host 文件为空，请先用 'vi host' 编辑目标主机。")
                    continue
                execute_playbook(hosts[:1], playbook)

            elif command.startswith('as hosts '):
                playbook = command[9:].strip()
                if not playbook:
                    print("用法: as hosts <playbook路径>")
                    continue
                hosts = read_host_file(HOSTS_FILE)
                if not hosts:
                    print("[错误] hosts 文件为空，请先用 'vi hosts' 编辑目标主机列表。")
                    continue
                execute_playbook(hosts, playbook)

            elif command in ('ls playbook', 'ls playbooks'):
                playbooks = list_playbooks()
                if playbooks:
                    print("可用的 Playbook:")
                    for p in playbooks:
                        print(f"  {p}")
                else:
                    print("未找到 Playbook，请确认 Playbook 目录已配置。")

            elif command.startswith('upload '):
                target = command[7:].strip()
                if target:
                    do_upload(target)
                else:
                    print("用法: upload <IP|host|hosts>")
            elif command == 'upload':
                print("用法: upload <IP|host|hosts>")

            elif command.startswith('download '):
                target = command[9:].strip()
                if target:
                    do_download(target)
                else:
                    print("用法: download <IP|host|hosts>")
            elif command == 'download':
                print("用法: download <IP|host|hosts>")

            else:
                print(f"未知命令: {command}")
                print("输入 'help' 查看可用命令。")

        except EOFError:
            print("\n再见。")
            break
        except KeyboardInterrupt:
            print("\n使用 'exit' 退出堡垒机。")
        except Exception as e:
            print(f"[错误] {e}")


if __name__ == "__main__":
    main()
