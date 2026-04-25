import urllib.request
import time

# 国内镜像源列表
MIRRORS = [
    "https://pypi.tuna.tsinghua.edu.cn/simple",  # 清华源
    "https://pypi.mirrors.ustc.edu.cn/simple",  # 中科大源
    "https://mirrors.aliyun.com/pypi/simple",    # 阿里云源
    "https://pypi.hustunique.com/simple",        # 华中科技大学源
    "https://pypi.douban.com/simple"             # 豆瓣源
]

def test_mirror_accessibility(mirror_url):
    """测试镜像源的可访问性"""
    try:
        start_time = time.time()
        # 构建测试URL - 访问simple目录
        test_url = mirror_url.rstrip('/')
        # 设置超时
        req = urllib.request.Request(test_url, headers={
            'User-Agent': 'PyManager/1.0'
        })
        with urllib.request.urlopen(req, timeout=10) as response:
            status_code = response.getcode()
            response_time = time.time() - start_time
            return True, status_code, response_time
    except Exception as e:
        return False, str(e), 0

def main():
    print("=== 国内PyPI镜像源可访问性测试 ===")
    print()
    
    results = []
    
    for mirror in MIRRORS:
        print(f"测试: {mirror}")
        success, status, response_time = test_mirror_accessibility(mirror)
        
        if success:
            print(f"  ✓ 可访问 | 状态码: {status} | 响应时间: {response_time:.2f}秒")
            results.append((mirror, True, response_time))
        else:
            print(f"  ✗ 不可访问 | 错误: {status}")
            results.append((mirror, False, 0))
        print()
    
    print("=== 测试结果汇总 ===")
    print()
    
    # 按响应时间排序
    working_mirrors = [(url, time) for url, success, time in results if success]
    working_mirrors.sort(key=lambda x: x[1])
    
    if working_mirrors:
        print("可用的镜像源（按响应时间排序）:")
        for url, response_time in working_mirrors:
            print(f"  {url} - {response_time:.2f}秒")
    else:
        print("没有可用的镜像源")
    
    print()
    
    if len(working_mirrors) < len(MIRRORS):
        print("不可用的镜像源:")
        for url, success, _ in results:
            if not success:
                print(f"  {url}")
    
    print()
    print("测试完成！")

if __name__ == "__main__":
    main()