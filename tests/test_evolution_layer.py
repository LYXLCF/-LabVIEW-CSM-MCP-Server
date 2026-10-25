import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tools")))
from csm_tools import CSMTools

def run_evolution_tests():
    print("==================================================")
    print("CSM 演进能力扩展自动化测试 (工程树挂载 + 消息脚本校验)")
    print("==================================================")

    tools = CSMTools()
    workspace_dir = r"c:\Users\ASUS\Desktop\CSM"
    proj_path = os.path.join(workspace_dir, r"CSM_AI\Test Control\Test Control.lvproj")
    visa_vi = os.path.join(workspace_dir, r"CSM_AI\Test Control\VISA\VISA.vi")

    # ----------------------------------------------------
    # 测试 1: 验证 csm_add_to_project 幂等挂载
    # ----------------------------------------------------
    print("\n[Test 1] 正在测试 csm_add_to_project (将 VISA.vi 挂载到工程树 'VISA' 文件夹)...")
    res_mount = tools.csm_add_to_project(proj_path, visa_vi, "VISA")
    print(f"  -> 挂载结果: {res_mount.get('success')}")
    print(f"  -> 状态反馈: {res_mount.get('status')}")
    assert res_mount["success"] is True, "工程树挂载测试失败！"

    # ----------------------------------------------------
    # 测试 2: 验证 P0 红线物理拦截 (严禁挂载系统盘工程)
    # ----------------------------------------------------
    print("\n[Test 2] 正在测试 P0 级最高红线拦截 (试图篡改 C 盘系统目录)...")
    fake_sys_proj = r"C:\Program Files (x86)\National Instruments\System.lvproj"
    res_p0 = tools.csm_add_to_project(fake_sys_proj, visa_vi, "TEST")
    print(f"  -> P0 拦截结果 success: {res_p0.get('success')}")
    print(f"  -> 错误类型: {res_p0.get('error_type')}")
    assert res_p0["success"] is False, "P0 物理拦截失效！"
    assert res_p0["error_type"] == "SecurityViolationError", "未触发 SecurityViolationError！"

    # ----------------------------------------------------
    # 测试 3: 验证 csm_set_state_script 语法守门人拦截 (输入野符号 -->)
    # ----------------------------------------------------
    print("\n[Test 3] 正在测试 csm_set_state_script 语法守门人 (输入非法野符号 '-->')...")
    bad_script = "API: Start --> TargetModule\n// 注释"
    res_bad = tools.csm_set_state_script(visa_vi, "API: Start", bad_script)
    print(f"  -> 拦截结果 success: {res_bad.get('success')}")
    print(f"  -> 错误类型: {res_bad.get('error_type')}")
    print(f"  -> 语法错误清单: {res_bad.get('syntax_errors')}")
    assert res_bad["success"] is False, "语法守门人未能成功拦截野符号！"
    assert res_bad["error_type"] == "StateScriptSyntaxError", "拦截错误类型不匹配！"

    # ----------------------------------------------------
    # 测试 4: 验证 csm_set_state_script 合规正统 CSM 语法写入
    # ----------------------------------------------------
    print("\n[Test 4] 正在测试 csm_set_state_script 合规官方语法写入...")
    valid_script = (
        "// 初始化完成，启动硬件并广播状态\n"
        "API: Start -> CAN\n"
        "API: Configure >> BaudRate=9600 -@ VISA\n"
        "Ready -><status>"
    )
    res_valid = tools.csm_set_state_script(visa_vi, "Macro: Initialize", valid_script)
    print(f"  -> 合规注入结果 success: {res_valid.get('success')}")
    print(f"  -> 注入行数: {res_valid.get('script_lines_count')}")
    print(f"  -> 语法验证结论: {res_valid.get('dsl_validation')}")
    assert res_valid["success"] is True, "合规语法注入失败！"

    print("\n==================================================")
    print("[PASS] 演进扩展能力全部验收通过！工程树联动与脚本注入 100% 达标！")
    print("==================================================")

if __name__ == "__main__":
    run_evolution_tests()
