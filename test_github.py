import urllib.request
import re

url = 'https://github.com/zhangyapu1/pymanager/releases/tag/1.0.3'
req = urllib.request.Request(url, headers={'User-Agent': 'ScriptManager'})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        print('状态码:', resp.getcode())
        content = resp.read().decode()
        print('页面内容长度:', len(content))
        
        # 查找资产链接
        patterns = [
            r'href=["\'](/[^"/]+/[^"/]+/releases/download/[^"/]+/[^"\'\s]+\.(?:exe|zip|rar))["\']',
            r'href=["\'](https://github.com/[^"/]+/[^"/]+/releases/download/[^"/]+/[^"\'\s]+\.(?:exe|zip|rar))["\']',
            r'download_url[^"\']+["\']([^"\']+)["\']',
            r'assets[^"\']+["\']([^"\']+download[^"\']+)["\']'
        ]
        
        for i, pattern in enumerate(patterns):
            matches = re.findall(pattern, content)
            print(f'模式{i+1}找到:', matches)
        
        # 查找包含download的链接
        download_links = re.findall(r'href=["\']([^"\']+download[^"\']+)["\']', content)
        print('包含download的链接:', download_links[:10])
        
        # 保存页面内容到文件
        with open('github_page.html', 'w', encoding='utf-8') as f:
            f.write(content)
        print('页面内容已保存到github_page.html')
except Exception as e:
    print('错误:', e)
    import traceback
    print('错误堆栈:', traceback.format_exc())