import os
import logging
import requests
from config import PROXY_PORT  # 从配置文件导入端口

# 配置代理环境变量
def set_proxy_env():
    """设置全局代理环境变量"""
    proxy_url = f"http://127.0.0.1:{7890}"
    os.environ['HTTP_PROXY'] = proxy_url
    os.environ['HTTPS_PROXY'] = proxy_url
    logging.info(f"已设置代理: {proxy_url}")

# 测试代理连接
def test_proxy():
    """测试代理是否能访问Telegram API"""
    try:
        proxy_url = f"http://127.0.0.1:{7890}"
        logging.info(f"测试代理连接: {proxy_url}")
        response = requests.get(
            url="https://api.telegram.org",
            timeout=5
        )
        if response.status_code == 200:
            logging.info("代理测试成功！")
            return True
        else:
            logging.warning(f"代理测试失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"代理连接异常: {str(e)}")
        return False