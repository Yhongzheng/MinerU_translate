import subprocess
import os


def run_magic_pdf(pdf_path, method='auto', lang=None, start=0, end=None, debug=False):
    # 获取PDF文件的目录和文件名
    dir_path, pdf_name = os.path.split(pdf_path)
    pdf_name_without_ext, _ = os.path.splitext(pdf_name)

    # 创建与PDF文件同名的文件夹
    output_dir = os.path.join(dir_path, pdf_name_without_ext)
    os.makedirs(output_dir, exist_ok=True)

    # 构造命令行参数
    command = ['magic-pdf', '-p', pdf_path, '-o', output_dir, '-m', method]

    if lang:
        command.extend(['-l', lang])
    if start is not None:
        command.extend(['-s', str(start)])
    if end is not None:
        command.extend(['-e', str(end)])
    if debug:
        command.append('-d')

    # 执行命令
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')

    # 输出结果
    if result.returncode == 0:
        print(result.stdout)
    else:
        print(f"Error: {result.stderr}")


# 示例使用
run_magic_pdf(r"C:\Users\yongjie.yang\Desktop\DeepSeek_R1.pdf")
