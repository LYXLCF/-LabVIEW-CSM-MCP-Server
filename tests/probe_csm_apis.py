import os
import json
import win32com.client

# 目标测绘的核心特工 VI 清单（基于官方 _csmHelper 目录）
BASE_HELPER_DIR = r"C:\Program Files (x86)\National Instruments\LabVIEW 2025\user.lib\_NEVSTOP\Communicable State Machine(CSM)\_csmHelper"

TARGET_VIS = {
    "read_states": os.path.join(BASE_HELPER_DIR, r"API with lvcsm Support\Read CSM States By CSM-VI.vi"),
    "read_api": os.path.join(BASE_HELPER_DIR, r"API with lvcsm Support\Read CSM API By CSM-VI.vi"),
    "read_status": os.path.join(BASE_HELPER_DIR, r"API with lvcsm Support\Read CSM Status By CSM-VI.vi"),
    "create_from_vi": os.path.join(BASE_HELPER_DIR, r"API\Create From VI Reference.vi"),
    "add_state_frame": os.path.join(BASE_HELPER_DIR, r"API\Add State Frame.vi"),
    "destroy": os.path.join(BASE_HELPER_DIR, r"API\Destroy.vi")
}

def probe_vi(lv_app, vi_key, vi_path):
    print(f"\n==================================================")
    print(f"[*] 正在测绘特工 VI: {vi_key}")
    print(f"    路径: {vi_path}")
    
    if not os.path.exists(vi_path):
        print(f"[-] 文件不存在: {vi_path}")
        return {"exists": False, "error": "File not found"}
        
    spec = {
        "exists": True,
        "path": vi_path,
        "name": "",
        "terminals": []
    }
    
    vi = None
    try:
        # 只读方式获取 VI 引用
        vi = lv_app.GetVIReference(vi_path, "", False, 0)
        spec["name"] = vi.Name
        print(f"[+] 成功加载 VI: {vi.Name}")
        
        # 测绘常见候选端子名（纯只读探测，零副作用）
        candidate_terminals = [
            # 通用端子
            "CSM VI", "VI", "VI Path", "VI Reference", "VI Ref", "target", "path",
            "error in", "error out",
            # 状态与列表
            "Array", "States", "CSM States", "State Names", "API States", "Status States",
            "User-Defined States", "Essential States", "Items", "Names", "Strings", "output",
            # 面向对象 Class 端子
            "csmhelper in", "csmhelper out", "CSM-Helper in", "CSM-Helper out", 
            "csm-helper in", "csm-helper out", "CSMHelper", "CSM-Helper",
            # 加分支端子
            "State Name", "State", "New State", "State to Add", "Frame Name",
            "Case Name", "Frame", "index", "Duplicate Frame?"
        ]
        
        for term in candidate_terminals:
            try:
                # 尝试读取该端子的当前值
                val = vi.GetControlValue(term)
                # 能够成功 GetControlValue 说明该端子绝对存在于前面板上
                val_type = type(val).__name__
                spec["terminals"].append({
                    "terminal_name": term,
                    "type": val_type,
                    "default_value": str(val) if not isinstance(val, (list, tuple)) else f"List(len={len(val)})"
                })
                print(f"    [√ 发现有效端子] Label: '{term}' | 类型: {val_type}")
            except Exception:
                # 端子不存在于 Connector Pane / FrontPanel
                pass
                
    except Exception as e:
        print(f"[-] 测绘发生异常: {e}")
        spec["error"] = str(e)
    finally:
        # 安全规范：必须在 finally 中清理，不留内存句柄
        vi = None

    return spec

def main():
    print("==================================================")
    print("CSM 接口探针测绘启动 (遵循只读与零副作用安全规范)")
    print("==================================================")
    
    lv_app = win32com.client.Dispatch("Labview.Application")
    print(f"[+] 已连接 LabVIEW 进程: {lv_app.AppName} (版本: {lv_app.Version})")
    
    results = {}
    for key, path in TARGET_VIS.items():
        results[key] = probe_vi(lv_app, key, path)
        
    # 保存测绘字典到 core/api_specs.json
    out_dir = r"c:\Users\ASUS\Desktop\CSM\csm_mcp\core"
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "api_specs.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    print("\n==================================================")
    print(f"[+] 测绘完成！《特工 VI 接口规格映射字典》已保存至:")
    print(f"    {out_file}")
    print("==================================================")

if __name__ == "__main__":
    main()
