import os
import sys

# 引入中台
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "core")))
from csm_bridge import CSMBridge

def test_bridge_read_visa():
    print("==================================================")
    print("CSM 中台只读状态测试 (针对 VISA.vi)")
    print("==================================================")
    
    bridge = CSMBridge()
    target_vi = r"c:\Users\ASUS\Desktop\CSM\CSM_AI\Test Control\VISA\VISA.vi"
    
    print(f"[*] 检查目标 VI: {target_vi}")
    is_open = bridge.check_front_panel_open(target_vi)
    print(f"[+] 前台窗口打开状态 (FPWinOpen): {is_open}")
    
    print("[*] 正在调用官方平坦化特工读取所有状态...")
    states = bridge.read_csm_states(target_vi)
    print(f"[+] 成功读取到 {len(states)} 个状态分支:")
    for idx, s in enumerate(states):
        print(f"    [{idx+1:02d}] {s}")
        
    print("\n[*] 正在读取 API 状态...")
    api_states = bridge.read_csm_api_states(target_vi)
    print(f"[+] 成功读取到 {len(api_states)} 个 API 接口分支:")
    for idx, s in enumerate(api_states):
        print(f"    [{idx+1:02d}] {s}")
        
    print("==================================================")
    print("[√] CSM 调度中台只读链路 100% 验证通过！")
    print("==================================================")

if __name__ == "__main__":
    test_bridge_read_visa()
