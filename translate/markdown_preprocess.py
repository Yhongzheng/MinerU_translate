import re
import shutil
import time
import uuid
import os
import chardet
import requests
from icecream import ic
from urllib.parse import unquote, quote
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class MarkdownMapper:
    def __init__(self, output_dir=None, image_dir=None):
        """
        初始化映射字典、正则表达式模式和图片缓存目录。

        Attributes:
        - self.mapping (dict): 存储占位符与对应原始内容的映射关系。
        - self.patterns (dict): 包含不同类型内容的正则表达式模式，用于匹配不需要翻译的部分。
        - output_dir (str): 输出文件的目录路径，用于存储图片缓存。如果为 None，则使用当前工作目录。

        类型缩写对应关系:
        - FORMULA (F): 公式
        - IMAGE (I): 图片
        - TABLE (T): 表格
        - CODE_BLOCK (C): 代码块
        - INLINE_CODE (IC): 行内代码
        - HTML_TAG (H): HTML标签
        - COMMENT (M): 注释
        - YAML_FRONT_MATTER (Y): YAML头部
        """
        self.mapping = {}
        self.output_dir = str(output_dir) if output_dir else os.getcwd()
        self.image_dir = str(image_dir) if image_dir else self.output_dir
        self.cache_dir = os.path.join(self.output_dir, "images")
        os.makedirs(self.cache_dir, exist_ok=True)

        self.patterns = {
            "H": re.compile(r'(?<!<PH>)<.*?>(?!<\/PH>)'),  # HTML标签，优先处理
            "Y": re.compile(r'(?<!<PH>)^---\s*\n.*?\n---\s*\n(?!<\/PH>)', re.DOTALL),  # YAML头部
            "M": re.compile(r'(?<!<PH>)<!--.*?-->(?!<\/PH>)', re.DOTALL),  # 注释
            "C": re.compile(r'(?<!<PH>)```.*?```(?!<\/PH>)', re.DOTALL),  # 代码块
            "T": re.compile(
                r'(?<!<PH>)^\|(?:[^\n]+\|)+\n\|\s*[:-]+\s*\|(?:\s*[:-]+\s*\|)*\n(?:\|(?:[^\n]+\|)+\n)*(?!<\/PH>)',
                re.MULTILINE),  # 表格
            "F": re.compile(r'(?<!<PH>)\$.*?\$(?!<\/PH>)', re.DOTALL),  # 公式
            "IC": re.compile(r'(?<!<PH>)`.*?`(?!<\/PH>)'),  # 行内代码
            "I": re.compile(r'(?<!<PH>)!\[.*?\]\([^\)]+\)(?!<\/PH>)'),  # 图片
            "URL": re.compile(r'(?<!<PH>)\[(.*?)\]\((http[s]?://[^\)]+)\)(?!<\/PH>)')  # 网址
        }

    def _generate_placeholder(self, content_type):
        """
        生成一个唯一的占位符，用于替换公式、图片等不需要翻译的部分。

        Parameters:
        - content_type (str): 内容的类型，如公式、图片等。

        Returns:
        - str: 生成的占位符字符串。
        """
        while True:
            placeholder = f"{content_type}_{uuid.uuid4().hex[:6]}"
            if placeholder not in self.mapping:
                break
        return placeholder

    def _replace_with_placeholder(self, match, content_type):
        """
        根据内容类型将匹配的文本替换为占位符。

        对于图片内容，会处理路径并将图片复制到缓存目录（如果是本地图片）。
        对于网络图片，直接保留原始链接。非图片内容直接进行占位符替换。

        参数:
        - match: 正则表达式匹配对象，包含了待处理的原始内容。
        - content_type: 字符串，表示内容的类型 ('I' 表示图片)。

        返回:
        - 替换后的文本，其中包含占位符。
        """
        # 生成占位符
        placeholder = self._generate_placeholder(content_type)
        # 获取原始内容
        original_content = match.group(0)

        # 如果内容类型是图片
        if content_type == "I":
            try:
                # 提取图片路径，处理URL编码的字符
                original_path = unquote(re.search(r'\((.*?)\)', original_content).group(1))

                if original_path.startswith("http://") or original_path.startswith("https://"):
                    # 如果是网络图片，直接保留原始链接，不进行下载
                    self.mapping[placeholder] = original_content
                else:
                    # 处理本地图片路径
                    if not os.path.isabs(original_path):
                        original_path = os.path.join(self.image_dir, original_path)
                    original_path = os.path.normpath(original_path)

                    if os.path.exists(original_path):
                        new_path = self._copy_image_to_cache(original_path)
                        new_path = os.path.normpath(new_path).replace('\\', '/')
                        alt_text = re.search(r'\[(.*?)\]', original_content).group(1)
                        modified_content = f'![{alt_text}]({quote(new_path)})'
                        self.mapping[placeholder] = modified_content
                    else:
                        print(f"图片不存在：{original_path}")
                        self.mapping[placeholder] = original_content
            except Exception as e:
                # 如果处理图片时出错，打印中文提示
                print(f"处理图片时出错：{original_content}")
                print(f"异常信息：{e}")
                self.mapping[placeholder] = original_content
        else:
            # 非图片内容直接映射
            self.mapping[placeholder] = original_content

        # 返回带有占位符的文本
        return f"<PH>{placeholder}</PH>"

    def _copy_image_to_cache(self, original_path):
        """
        复制图片到目标目录中与源目录结构一致的路径，并返回相对于目标目录的相对路径。

        Parameters:
        - original_path (str): 原始图片路径。

        Returns:
        - str: 相对路径，用于替换Markdown中的图片链接。
        """
        # 获取图片在源文件夹中的相对路径
        rel_path = os.path.relpath(original_path, self.image_dir)
        # 目标路径应该保持相同的文件结构
        target_path = os.path.join(self.output_dir, rel_path)
        target_dir = os.path.dirname(target_path)

        # 如果目标路径的目录不存在，则创建
        os.makedirs(target_dir, exist_ok=True)

        # 复制图片到目标路径
        shutil.copy2(original_path, target_path)

        # 返回相对于output_dir的相对路径
        return os.path.relpath(target_path, self.output_dir)

    def clear_image_cache(self):
        """
        清理图片缓存目录中的所有文件和目录。
        """
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir, exist_ok=True)

    def extract_and_replace(self, markdown_text):
        """
        提取markdown文本中的公式、图片等不需要翻译的部分，并用占位符替换它们。

        Parameters:
        - markdown_text (str): 输入的Markdown文本。

        Returns:
        - str: 替换后的Markdown文本，已将不需要翻译的部分替换为占位符。
        """
        replaced_text = markdown_text
        for content_type, pattern in self.patterns.items():
            try:
                replaced_text = pattern.sub(lambda match: self._replace_with_placeholder(match, content_type),
                                            replaced_text)
            except Exception as e:
                print(f'在处理类型 {content_type} 时发生异常: {e}')
                raise
        return replaced_text

    def restore_text(self, translated_text):
        """
        将替换后的文本恢复为包含原始内容的文本，并根据需要在<PH>标签前后添加换行符。

        Parameters:
        - translated_text (str): 翻译后的Markdown文本，包含占位符。

        Returns:
        - str: 恢复后的Markdown文本，已将占位符替换为原始内容。
        """
        restored_text = translated_text

        # 先按照占位符替换为原始内容
        for placeholder, original_content in self.mapping.items():
            placeholder_with_tags = f"<PH>{placeholder}</PH>"

            # 查找带有<PH>标签的占位符位置
            index = restored_text.find(placeholder_with_tags)

            if index != -1 and (placeholder.startswith("C_") or placeholder.startswith("T_")):
                # 判断<PH>标签前面是否有换行符
                if index > 0 and restored_text[index - 1] != '\n':
                    original_content = f"\n{original_content}"

                # 判断</PH>标签后面是否有换行符
                end_index = index + len(placeholder_with_tags)
                if end_index < len(restored_text) and restored_text[end_index] != '\n':
                    original_content = f"{original_content}\n"

            # 替换占位符为原始内容
            restored_text = restored_text.replace(placeholder, original_content)

        # 再去除<PH>和</PH>标签
        restored_text = restored_text.replace("<PH>", "").replace("</PH>", "")

        return restored_text

    def prepare_markdown_for_translation(self, markdown_input):
        """
        处理Markdown文件或文本，提取并替换其中的公式、图片等不需要翻译的部分。

        Parameters:
        - markdown_input (str): Markdown文件的路径或Markdown文本内容。

        Returns:
        - tuple: 包含替换后的文本和占位符与原始内容的映射关系。

        Raises:
        - FileNotFoundError: 如果文件路径无效。
        - ValueError: 如果文件内容为空。
        """
        markdown_text = ""
        if os.path.exists(markdown_input):
            # 更新 图片 地址
            self.image_dir = os.path.dirname(markdown_input)  # 获取markdown所在路径，那么，md里的相对路径就可以用了
            # 传入的是文件路径，自动检测文件编码
            with open(markdown_input, 'rb') as file:
                raw_data = file.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding']
                ic("检测到编码类型:", encoding)  # 可选：打印检测到的编码

            # 使用检测到的编码读取文件内容，并转为utf-8
            with open(markdown_input, 'r', encoding=encoding) as file:
                source_text = file.read()

            # 确保所有内容都以utf-8编码处理
            markdown_text = source_text.encode('utf-8').decode('utf-8')
        else:
            # 传入的是文本
            markdown_text = markdown_input

        if not markdown_text.strip():
            raise ValueError("Markdown内容为空")
        # 清空映射关系，确保多次调用时不会混淆
        self.mapping = {}
        replaced_text = self.extract_and_replace(markdown_text)
        return replaced_text, self.mapping


if __name__ == '__main__':
    mapper = MarkdownMapper()
    mp = r"C:\Users\yongjie.yang\Desktop\2405.09798v1\2405.09798v1.md"
    replaced_text, mapping = mapper.prepare_markdown_for_translation(mp)
