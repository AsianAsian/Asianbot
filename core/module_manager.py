import os
import importlib
from pathlib import Path

def load_modules(application):
    """动态加载所有模块，排除filter模块"""
    modules_dir = Path(__file__).parent.parent / "modules"
    
    # 遍历模块目录，排除filter模块
    for item in modules_dir.iterdir():
        if item.is_dir() and item.name != "filter":  # 排除filter模块
            try:
                # 导入模块的main.py
                module_name = f"modules.{item.name}.main"
                module = importlib.import_module(module_name)
                
                # 调用每个模块的register函数注册处理器
                if hasattr(module, "register"):
                    module.register(application)
                    print(f"✅ 已加载模块: {item.name}")
                else:
                    print(f"⚠️ 模块 {item.name} 缺少register函数，已跳过")
            except Exception as e:
                print(f"❌ 加载模块 {item.name} 失败: {str(e)}")
