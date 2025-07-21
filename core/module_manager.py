import os
import importlib
from pathlib import Path
from telegram.ext import Application

def load_modules(application: Application):
    """动态加载所有模块"""
    # 使用Path处理路径，避免跨平台问题
    current_dir = Path(__file__).parent
    modules_dir = current_dir.parent / "modules"  # 正确定位到modules目录
    
    # 确保模块目录存在
    if not modules_dir.exists():
        print(f"⚠️ 模块目录不存在: {modules_dir}")
        return
    
    # 遍历模块目录
    for module_name in os.listdir(modules_dir):
        module_path = modules_dir / module_name
        main_file = module_path / "main.py"
        
        # 检查是否为有效的模块目录
        if (module_path.is_dir() and 
            not module_name.startswith("__") and 
            main_file.exists()):
            
            try:
                # 动态导入模块
                module = importlib.import_module(f"modules.{module_name}.main")
                
                # 检查并调用register函数
                if hasattr(module, "register") and callable(module.register):
                    module.register(application)
                    print(f"✅ 模块 {module_name} 已加载")
                else:
                    print(f"⚠️ 模块 {module_name} 缺少register函数，已跳过")
                    
            except ImportError as e:
                print(f"❌ 模块 {module_name} 导入失败: 缺少依赖 - {e}")
            except Exception as e:
                print(f"❌ 模块 {module_name} 加载失败: {str(e)}")
