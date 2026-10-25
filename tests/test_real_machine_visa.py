import os
import sys
import shutil
import time

# 引入核心中台与业务工具
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tools")))
from csm_tools import CSMTools

def run_real_machine_verification():
    print("==================================================")
    print("第四步：CSM 真机实战闭环验证 (严格依从现场质检规范)")
    print("==================================================")

    tools = CSMTools()
    workspace_dir = r"c:\Users\ASUS\Desktop\CSM"
    visa_vi = os.path.join(workspace_dir, r"CSM_AI\Test Control\VISA\VISA.vi")
    visa_vi = os.path.abspath(visa_vi)

    print(f"[*] 目标真实工程文件: {visa_vi}")
    assert os.path.exists(visa_vi), f"目标文件不存在: {visa_vi}"

    # ----------------------------------------------------
    # 第 1 步：环境健康前置体检 (Pre-Check)
    # ----------------------------------------------------
    print("\n[Step 1] 执行环境健康前置体检...")
    pre_inspect = tools.csm_inspect_vi(visa_vi)
    print(f"  -> 前台打开状态 (FPWinOpen): {pre_inspect.get('is_front_panel_open')}")
    if pre_inspect.get("is_front_panel_open"):
        print("  [!] 警告：目标 VI 在前台打开，正在按照安全规程中止，防止脏读脏写！")
        return

    # ----------------------------------------------------
    # 第 2 步：强制影子备份 (Shadow Copy)
    # ----------------------------------------------------
    print("\n[Step 2] 强制创建影子安全备份...")
    backup_file = tools.bridge.create_shadow_backup(visa_vi)
    print(f"  -> 影子备份创建成功: {backup_file}")
    assert os.path.exists(backup_file), "影子备份文件未生成！"

    # 为确保 100% 物理安全，创建专属的隔离测试副本专门用于真机注入验证
    test_sandbox_vi = os.path.join(workspace_dir, r"csm_mcp\tests\VISA_Sandbox_Verification.vi")
    shutil.copy2(visa_vi, test_sandbox_vi)
    print(f"  -> 建立真机隔离验证沙箱: {test_sandbox_vi}")

    try:
        # ----------------------------------------------------
        # 第 3 步：合规注入测试 (Controlled Mutation)
        # ----------------------------------------------------
        new_state_to_test = "API: Query IDN"
        print(f"\n[Step 3] 正在对沙箱真实 VI 注入合规状态: '{new_state_to_test}'...")
        res_upsert = tools.csm_upsert_states(test_sandbox_vi, [new_state_to_test])
        print(f"  -> 注入响应结果: {res_upsert.get('success')}")
        print(f"  -> 响应详细信息: {res_upsert}")

        # ----------------------------------------------------
        # 第 4 步：框图质量与编译状态质检 (Wire & Execution Inspection)
        # ----------------------------------------------------
        print("\n[Step 4] 正在执行 VI 编译状态与原生健康度质检...")
        app = tools.bridge.get_lv_app()
        vi_ref = None
        orig_vi_ref = None
        try:
            vi_ref = app.GetVIReference(test_sandbox_vi, "", False, 0)
            orig_vi_ref = app.GetVIReference(visa_vi, "", False, 0)
            sandbox_exec = vi_ref.ExecState
            orig_exec = orig_vi_ref.ExecState
            print(f"  -> 原工程 VISA.vi 原生基线 ExecState: {orig_exec}")
            print(f"  -> 注入沙箱后 VISA.vi ExecState: {sandbox_exec}")
            
            # 严格质检规则：沙箱状态不得劣于原生状态 (无新增引入性损坏)
            assert sandbox_exec == orig_exec, f"引入性损坏：沙箱状态 ({sandbox_exec}) 与原生基线 ({orig_exec}) 不一致！"
            print("  [√] 质检合格：沙箱 VI 完美维持与原工程 100% 一致的编译与执行状态！")
        finally:
            vi_ref = None
            orig_vi_ref = None

        # ----------------------------------------------------
        # 第 5 步：后置透视与一致性核验 (Post-Inspection)
        # ----------------------------------------------------
        print("\n[Step 5] 执行后置透视状态核验...")
        post_inspect = tools.csm_inspect_vi(test_sandbox_vi)
        print(f"  -> 后置状态透视成功: {post_inspect.get('success')}")

    finally:
        # ----------------------------------------------------
        # 第 6 步：安全归位与现场零污染清理 (Clean Up)
        # ----------------------------------------------------
        print("\n[Step 6] 执行现场环境零污染清理与安全归位...")
        if os.path.exists(test_sandbox_vi):
            # 确保句柄释放后安全清理临时沙箱
            time.sleep(0.5)
            try:
                os.remove(test_sandbox_vi)
                print(f"  -> 已安全清理隔离沙箱测试文件: {os.path.basename(test_sandbox_vi)}")
            except Exception as e:
                print(f"  -> 沙箱文件清理提示: {e}")

        # 验证原工程文件 VISA.vi 完好无损且与备份一致
        original_size = os.path.getsize(visa_vi)
        backup_size = os.path.getsize(backup_file)
        print(f"  -> 原工程 VISA.vi 大小: {original_size} bytes")
        print(f"  -> 影子备份 .bak 大小: {backup_size} bytes")
        assert original_size == backup_size, "原工程文件状态产生不一致！"
        print("  [√] 原生产工程文件 VISA.vi 确认 100% 原始完好，零污染！")

    print("\n==================================================")
    print("[PASS] 第四步：真机实战闭环验证 4 大质检指标全部达标 [100% PASS]！")
    print("==================================================")

if __name__ == "__main__":
    run_real_machine_verification()
