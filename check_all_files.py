import os
import sys
import traceback

# 日志文件路径
LOG_FILE = 'error_log.txt'

# 要检查的目录
CHECK_DIRS = ['', 'modules', 'data']

def check_file(file_path):
    """检查单个Python文件的语法错误"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        compile(code, file_path, 'exec')
        return True, None
    except Exception as e:
        return False, str(e)

def main():
    """检查所有Python文件"""
    error_count = 0
    total_files = 0
    
    # 清空日志文件
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write('===== 项目文件检查日志 =====\n')
        f.write(f'检查时间: {os.popen("date /t").read().strip()} {os.popen("time /t").read().strip()}\n\n')
    
    for dir_name in CHECK_DIRS:
        dir_path = os.path.join(os.getcwd(), dir_name)
        if not os.path.exists(dir_path):
            continue
        
        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    total_files += 1
                    
                    success, error = check_file(file_path)
                    if not success:
                        error_count += 1
                        with open(LOG_FILE, 'a', encoding='utf-8') as f:
                            f.write(f'文件: {file_path}\n')
                            f.write(f'错误: {error}\n\n')
    
    # 写入总结
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write('===== 检查总结 =====\n')
        f.write(f'总文件数: {total_files}\n')
        f.write(f'错误文件数: {error_count}\n')
        f.write(f'检查完成!\n')
    
    print(f'检查完成! 共检查 {total_files} 个文件，发现 {error_count} 个错误。')
    print(f'详细信息请查看 {LOG_FILE}')

if __name__ == '__main__':
    main()
