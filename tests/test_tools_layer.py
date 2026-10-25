import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tools")))
from csm_tools import CSMTools

def run_tools_validation():
    print("==================================================")
    print("CSM 业务工具层自动化测试与规范验收")
    print("==================================================")

    tools = CSMTools()
    workspace_dir = r"c:\Users\ASUS\Desktop\CSM"

    # 1. 验证 Tool 4: csm_verify_syntax (全局静态体检)
    print("\n[Test 1] 正在执行 Tool 4: csm_verify_syntax (全局死锁与语法扫描)...")
    res_verify = tools.csm_verify_syntax(workspace_dir)
    print(f"  -> 成功扫描模块数: {res_verify.get('total_scanned_modules')}")
    print(f"  -> 死锁数量: {res_verify.get('deadlock_count')}")
    print(f"  -> 健康评级: {res_verify.get('health_status')}")
    assert res_verify["success"] is True, "Tool 4 执行失败！"

    # 2. 验证 Tool 1: csm_inspect_vi (透视 VISA.vi)
    visa_vi = os.path.join(workspace_dir, r"CSM_AI\Test Control\VISA\VISA.vi")
    print(f"\n[Test 2] 正在执行 Tool 1: csm_inspect_vi (透视 {os.path.basename(visa_vi)})...")
    res_inspect = tools.csm_inspect_vi(visa_vi)
    print(f"  -> 是否前台打开: {res_inspect.get('is_front_panel_open')}")
    print(f"  -> 状态总数: {res_inspect.get('total_states')}")
    assert res_inspect["success"] is True, "Tool 1 执行失败！"

    # 3. 验证 Tool 3 语义守门人 (Semantic Gatekeeper 拦截野状态名)
    print("\n[Test 3] 正在验证 Tool 3 语义守门人安全拦截 (输入非法野状态名)...")
    illegal_states = ["State1", "aaa", "temp"]
    res_gatekeeper = tools.csm_upsert_states(visa_vi, illegal_states)
    print(f"  -> 拦截结果 success: {res_gatekeeper['success']}")
    print(f"  -> 错误类型: {res_gatekeeper.get('error_type')}")
    print(f"  -> 拦截提示: {res_gatekeeper.get('error_message')}")
    assert res_gatekeeper["success"] is False, "语义守门人未能成功拦截野状态名！"
    assert res_gatekeeper["error_type"] == "StateSyntaxError", "拦截类型不匹配！"

    # 4. 验证 P0 级最高红线拦截 (试图向 C 盘底层库写入)
    print("\n[Test 4] 正在验证 P0 级最高红线物理阻断 (试图向 C 盘系统目录写文件)...")
    forbidden_target = r"C:\Program Files (x86)\National Instruments\LabVIEW 2025\vi.lib\Hacked.vi"
    res_p0 = tools.csm_create_module(forbidden_target, "Hacked")
    print(f"  -> 拦截结果 success: {res_p0['success']}")
    print(f"  -> 错误类型: {res_p0.get('error_type')}")
    print(f"  -> 拦截提示: {res_p0.get('error_message')}")
    assert res_p0["success"] is False, "P0 级最高红线物理阻断失效！"
    assert res_p0["error_type"] == "SecurityViolationError", "未触发 SecurityViolationError！"

    # 5. 验证 Tool 2: csm_create_module (在工作区安全生成新模块脚手架)
    test_new_mod = os.path.join(workspace_dir, r"csm_mcp\tests\Test_Generated_Module.vi")
    if os.path.exists(test_new_mod):
        os.remove(test_new_mod)
    print(f"\n[Test 5] 正在执行 Tool 2: csm_create_module (在工作区安全克隆脚手架)...")
    res_create = tools.csm_create_module(test_new_mod, "Test_Generated_Module")
    print(f"  -> 生成结果 success: {res_create['success']}")
    print(f"  -> 生成路径: {res_create.get('created_path')}")
    print(f"  -> 所用母版: {res_create.get('template_used')}")
    assert res_create["success"] is True, "Tool 2 脚手架生成失败！"
    assert os.path.exists(test_new_mod), "生成的物理文件未找到！"

    print("\n==================================================")
    print("[√] 第三步：四大核心 Tool 业务功能封装与全部安全护栏 100% 验收通过！")
    print("==================================================")

if __name__ == "__main__":
    run_tools_validation()
