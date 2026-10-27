# -*- coding: utf-8 -*-
"""
LabVIEW CSM 本地离线控制台中枢 (Local Offline CLI)
无需任何网络连接，无需大模型，在终端即可独立执行 CSM 模块透视、生成、穿线切削与工程挂载。
"""
import os
import sys
import argparse
import json

# 确保引入 tools 目录
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "tools")))
from csm_tools import CSMTools

def print_banner():
    print("=" * 65)
    print("   ⚡ LabVIEW CSM 专有离线工业控制台中枢 (Local Engine)")
    print("   100% 本地物理运行 | 零网络依赖 | 零断线安全切削")
    print("=" * 65)

def interactive_mode():
    tools = CSMTools()
    while True:
        print_banner()
        print(" [1] 🔍 透视目标 VI 状态流转结构与健康度 (Inspect VI)")
        print(" [2] 📦 基于官方母版新建模块脚手架 (Create Module)")
        print(" [3] ⚡ 安全注入状态分支 (自动穿线+前面板自文档化) (Upsert States)")
        print(" [4] 🧭 全工程拓扑死锁图与孤立状态扫描 (Verify Syntax)")
        print(" [5] 🌲 将 VI 模块自动挂载点亮至 .lvproj 工程树 (Add to Project)")
        print(" [6] 🛡️ 复杂消息参数安全转义编解码 (Format Argument)")
        print(" [0] 🚪 退出控制台")
        print("-" * 65)
        
        choice = input("请选择操作编号 [0-6]: ").strip()
        if choice == "0":
            print("\n已退出 CSM 本地控制台。祝工程顺利！")
            break
        elif choice == "1":
            vi_path = input("\n请输入目标 CSM .vi 的绝对路径: ").strip().strip('"').strip("'")
            if not vi_path or not os.path.exists(vi_path):
                print("❌ 错误：文件不存在或路径无效！\n")
                continue
            print("正在透视框图与运行状态...")
            res = tools.csm_inspect_vi(vi_path)
            print(json.dumps(res, ensure_ascii=False, indent=2))
        elif choice == "2":
            target_path = input("\n请输入新模块的保存绝对路径 (如 C:\\test\\Motor#1.vi): ").strip().strip('"').strip("'")
            mod_name = input("请输入模块规范名称 (留空则根据文件名自动推断): ").strip()
            print("可选母版: auto(默认自适应), worker, ui, worker_tiny, ui_tiny, worker_config, ui_config, dqmh, reuse")
            tpl = input("母版类型 [默认 auto]: ").strip() or "auto"
            print("正在克隆出厂母版并配置...")
            res = tools.csm_create_module(target_path, mod_name, tpl)
            print(json.dumps(res, ensure_ascii=False, indent=2))
        elif choice == "3":
            vi_path = input("\n请输入目标 CSM .vi 的绝对路径: ").strip().strip('"').strip("'")
            if not vi_path or not os.path.exists(vi_path):
                print("❌ 错误：文件不存在或路径无效！\n")
                continue
            raw_states = input("请输入需新增的状态分支 (多个状态用逗号隔开，如 'API: Start, API: Stop'): ").strip()
            states = [s.strip() for s in raw_states.split(",") if s.strip()]
            if not states:
                print("❌ 错误：状态名称不能为空！\n")
                continue
            print(f"正在向 {os.path.basename(vi_path)} 注入 {len(states)} 个状态分支，执行自动穿线...")
            res = tools.csm_upsert_states(vi_path, states)
            print(json.dumps(res, ensure_ascii=False, indent=2))
        elif choice == "4":
            proj_dir = input("\n请输入 LabVIEW 项目所在目录绝对路径: ").strip().strip('"').strip("'")
            if not proj_dir or not os.path.isdir(proj_dir):
                print("❌ 错误：目录不存在！\n")
                continue
            print("正在进行纯 Python 全工程拓扑死锁扫描与无 .lvcsm 兜底嗅探...")
            res = tools.csm_verify_syntax(proj_dir)
            print(json.dumps(res, ensure_ascii=False, indent=2))
        elif choice == "5":
            proj_path = input("\n请输入 .lvproj 文件的绝对路径: ").strip().strip('"').strip("'")
            vi_path = input("请输入需挂载的 .vi 绝对路径: ").strip().strip('"').strip("'")
            folder = input("挂载到哪个工程虚拟文件夹 [可留空]: ").strip()
            print("正在解析 .lvproj XML 树并原子追加节点...")
            res = tools.csm_add_to_project(proj_path, vi_path, folder)
            print(json.dumps(res, ensure_ascii=False, indent=2))
        elif choice == "6":
            arg_type = input("\n参数类型 (safe / error / hex) [默认 safe]: ").strip() or "safe"
            raw_val = input("原始数据串 (如文件路径、URL或普通文本): ").strip()
            res = tools.csm_format_argument(arg_type, raw_val)
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            print("❌ 无效选项，请重新输入。")
        
        input("\n按 Enter 键继续...")

def main():
    parser = argparse.ArgumentParser(description="LabVIEW CSM 专有本地离线控制台中枢")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # inspect
    p_inspect = subparsers.add_parser("inspect", help="透视目标 VI 状态")
    p_inspect.add_argument("vi_path", help="目标 VI 绝对路径")

    # create
    p_create = subparsers.add_parser("create", help="新建 CSM 模块")
    p_create.add_argument("target_path", help="新模块保存路径")
    p_create.add_argument("--name", default="", help="模块规范名称")
    p_create.add_argument("--template", default="auto", help="母版类型 (auto/worker/ui/...)")

    # add-state
    p_add = subparsers.add_parser("add-state", help="安全注入状态分支 (自动穿线)")
    p_add.add_argument("vi_path", help="目标 VI 绝对路径")
    p_add.add_argument("states", nargs="+", help="新增的状态分支名称列表 (如 'API: Start' 'API: Stop')")

    # verify
    p_verify = subparsers.add_parser("verify", help="扫描工程路由与拓扑死锁")
    p_verify.add_argument("project_dir", help="项目工程所在根目录")

    args = parser.parse_args()
    tools = CSMTools()

    if args.command == "inspect":
        res = tools.csm_inspect_vi(args.vi_path)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif args.command == "create":
        res = tools.csm_create_module(args.target_path, args.name, args.template)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif args.command == "add-state":
        res = tools.csm_upsert_states(args.vi_path, args.states)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif args.command == "verify":
        res = tools.csm_verify_syntax(args.project_dir)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        # 无参数时启动交互式菜单
        interactive_mode()

if __name__ == "__main__":
    main()
