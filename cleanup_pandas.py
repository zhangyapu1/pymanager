import os
import sys
import shutil
import site

# 获取site-packages目录
site_packages = site.getsitepackages()
print(f"Site packages directories: {site_packages}")

# 查找pandas相关文件
for site_pkg in site_packages:
    pandas_dir = os.path.join(site_pkg, 'pandas')
    pandas_dist_info = os.path.join(site_pkg, 'pandas-*.dist-info')
    
    if os.path.exists(pandas_dir):
        print(f"Found pandas directory: {pandas_dir}")
        try:
            shutil.rmtree(pandas_dir)
            print(f"Removed pandas directory")
        except Exception as e:
            print(f"Error removing pandas directory: {e}")
    
    import glob
    dist_info_files = glob.glob(pandas_dist_info)
    for dist_info in dist_info_files:
        if os.path.exists(dist_info):
            print(f"Found pandas dist-info: {dist_info}")
            try:
                shutil.rmtree(dist_info)
                print(f"Removed pandas dist-info")
            except Exception as e:
                print(f"Error removing dist-info: {e}")

print("Cleanup completed")