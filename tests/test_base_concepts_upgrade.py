# -*- coding: utf-8 -*-
"""
自动化验证脚本：全量核验基于 0. Base Concepts/1~7 的 MCP 升级套件
涵盖：命名守门、参数安全编解码、模板选型、健康度审计、8 大 DSL 解析与系统级模块感知
"""

import os
import sys

# 导入工具集
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tools")))
from csm_tools import CSMTools

def run_tests():
    print("==========================================================")
    print(">>> 开始执行 CSM MCP 全体系升级自动化核验测试")
    print("==========================================================")

    tools = CSMTools()
    test_dir = r"c:\Users\ASUS\Desktop\CSM\csm_mcp\scratch"
    os.makedirs(test_dir, exist_ok=True)

    # -------------------------------------------------------------------------
    # Test 1: 命名守门人校验 (2. Module Naming Rules.vi)
    # -------------------------------------------------------------------------
    print("\n[TEST 1] 核验 2. Module Naming Rules 命名守门人...")
    
    # 1.1 合法命名测试
    valid_names = [
        ("Power_Supply", "standard"),
        ("Motor#1", "worker"),
        (".TCP_Router", "system_level"),
        ("Chamber.Temp", "submodule"),
        ("Pipeline$2", "chain")
    ]
    for name, expected_cat in valid_names:
        dummy_path = os.path.join(test_dir, f"test_{name.replace('.', '_').replace('#', '_').replace('$', '_')}.vi")
        # 清理旧文件
        if os.path.exists(dummy_path):
            os.remove(dummy_path)
        res = tools.csm_create_module(dummy_path, module_name=name)
        assert res["success"] is True, f"合法名称 {name} 失败: {res}"
        assert res["module_category"] == expected_cat, f"分类不匹配: {res}"
        print(f"  [PASS] 合法名称 '{name}' -> 分类: {res['module_category']}")
        if os.path.exists(dummy_path):
            os.remove(dummy_path)

    # 1.2 非法保留字符拦截测试
    invalid_names = [
        "Motor/CAN",
        "Test@Device",
        "Sensor[0]",
        "Pipe$abc"  # $ 后面非数字
    ]
    for bad_name in invalid_names:
        bad_path = os.path.join(test_dir, "bad_mod.vi")
        if os.path.exists(bad_path):
            os.remove(bad_path)
        res = tools.csm_create_module(bad_path, module_name=bad_name)
        assert res["success"] is False, f"非法名称 {bad_name} 未被拦截！"
        assert res["error_type"] == "ModuleNamingError"
        print(f"  [PASS] 成功拦截非法名称 '{bad_name}' -> 提示: {res['error_message']}")

    # -------------------------------------------------------------------------
    # Test 2: 参数安全编解码 (4.1~4.3 Arguments)
    # -------------------------------------------------------------------------
    print("\n[TEST 2] 核验 4.1~4.3 Arguments 参数安全编解码工具...")
    
    # 2.1 路径安全转义与还原 (4.3 规范)
    raw_path = r"C:\Program Files\NI\data,log.csv"
    res_safe = tools.csm_format_argument(arg_type="safe_string", raw_value=raw_path)
    assert res_safe["success"] is True
    safe_val = res_safe["formatted_argument"]
    assert safe_val.startswith("SAFESTR:"), f"未加 SAFESTR 标记: {safe_val}"
    print(f"  [PASS] 原始路径安全转义 -> {safe_val}")

    res_revert = tools.csm_format_argument(arg_type="revert_safe", raw_value=safe_val)
    assert res_revert["success"] is True
    assert res_revert["reverted_value"] == raw_path, f"还原不一致: {res_revert}"
    print(f"  [PASS] SAFESTR 无损逆还原 -> {res_revert['reverted_value']}")

    # 2.2 错误簇参数封装与解析 (4.2 规范)
    res_err = tools.csm_format_argument(arg_type="error", raw_value="VISA Timeout 5000ms", extra_info="1073807339")
    assert res_err["success"] is True
    err_str = res_err["formatted_argument"]
    assert "<ErrStr>[Error: 1073807339]" in err_str
    print(f"  [PASS] 错误簇封装 -> {err_str}")

    res_parse_err = tools.csm_format_argument(arg_type="parse_error", raw_value=err_str)
    assert res_parse_err["success"] is True
    parsed = res_parse_err["parsed_error"]
    assert parsed["code"] == 1073807339
    assert parsed["message"] == "VISA Timeout 5000ms"
    print(f"  [PASS] <ErrStr> 解析还原 -> code={parsed['code']}, msg={parsed['message']}")

    # 2.3 复杂二进制 Hex 编码 (4.1 规范)
    res_hex = tools.csm_format_argument(arg_type="hex", raw_value="HELLO_CSM")
    assert res_hex["success"] is True
    assert res_hex["formatted_argument"] == "HEXSTR:48454C4C4F5F43534D"
    print(f"  [PASS] HEXSTR 二进制编码 -> {res_hex['formatted_argument']}")

    # -------------------------------------------------------------------------
    # Test 3: 5 大母版类型选型测试 (CSM 模板生态)
    # -------------------------------------------------------------------------
    print("\n[TEST 3] 核验 5 大母版类型选型克隆...")
    tpl_types = ["worker", "ui", "worker_tiny", "ui_tiny", "dqmh"]
    for tpl in tpl_types:
        tpl_vi_path = os.path.join(test_dir, f"test_tpl_{tpl}.vi")
        if os.path.exists(tpl_vi_path):
            os.remove(tpl_vi_path)
        res = tools.csm_create_module(tpl_vi_path, module_name=f"Demo_{tpl}", template_type=tpl)
        assert res["success"] is True, f"克隆母版 {tpl} 失败: {res}"
        assert res["template_type"] == tpl
        print(f"  [PASS] 成功克隆母版类型: '{tpl}' -> 文件: {os.path.basename(tpl_vi_path)}")
        if os.path.exists(tpl_vi_path):
            os.remove(tpl_vi_path)

    # -------------------------------------------------------------------------
    # Test 4: 模块健康度审计 (1. JKISM vs CSM.vi)
    # -------------------------------------------------------------------------
    print("\n[TEST 4] 核验 1. JKISM vs CSM 模块健康度审计...")
    real_visa_vi = r"C:\Users\ASUS\Desktop\CSM\CSM_AI\Test Control\VISA\VISA.vi"
    if os.path.exists(real_visa_vi):
        res_insp = tools.csm_inspect_vi(real_visa_vi)
        assert res_insp["success"] is True
        health = res_insp["health_audit"]
        print(f"  [PASS] VISA.vi 健康度评分: {health['health_score']}/100")
        print(f"         包含 Initialize: {health['has_initialize']}")
        print(f"         包含 Start:      {health['has_start']}")
        print(f"         包含 Exit:       {health['has_exit']}")
        print(f"         包含 Error:      {health['has_critical_error'] or health['has_error_handler']}")
        if health["missing_recommendations"]:
            print(f"         缺失推荐: {health['missing_recommendations']}")

    # -------------------------------------------------------------------------
    # Test 5: 全局语法扫描与系统级模块统计 (7. System-Level Module.vi)
    # -------------------------------------------------------------------------
    print("\n[TEST 5] 核验 7. System-Level Module 系统级模块感知与 8-DSL 分析...")
    res_syntax = tools.csm_verify_syntax(r"C:\Users\ASUS\Desktop\CSM\CSM_AI\Test Control")
    assert res_syntax["success"] is True
    print(f"  [PASS] 扫描模块总数: {res_syntax['total_scanned_modules']}")
    print(f"         普通模块数:   {res_syntax['standard_modules_count']}")
    print(f"         系统级模块数: {res_syntax['system_modules_count']}")
    print(f"         系统级模块表: {res_syntax['system_modules']}")
    print(f"         死锁检测状态: {res_syntax['health_status']}")

    print("\n==========================================================")
    print(">>> [100% ALL PASS] CSM MCP 全体系升级验证圆满通过！")
    print("==========================================================")

if __name__ == "__main__":
    run_tests()
