import traceback

from translate import MarkdownMapper, translate_markdown
import chardet
import os
import logging
import asyncio
import json
from datetime import datetime
from markdown2 import markdown
from fpdf import FPDF

logging.basicConfig(
    filename='translation_process.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def create_output_directory(base_dir, original_file_name):
    # 使用文件名去掉扩展名和当前时间戳创建唯一目录
    base_name = os.path.splitext(os.path.basename(original_file_name))[0]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = os.path.join(base_dir, f"{base_name}_{timestamp}")

    # 创建目录
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


async def process_markdown_file(file_path, source_lang, target_lang, country):
    try:
        if os.path.exists(file_path):
            # 创建输出目录
            output_dir = create_output_directory(os.path.dirname(file_path), file_path)
        else:
            # 获取当前Python文件的完整路径
            current_file_path = os.path.abspath(__file__)
            # 获取当前Python文件所在的文件夹路径
            output_dir = os.path.dirname(current_file_path)

        # 创建MarkdownMapper实例并处理文本
        mapper = MarkdownMapper(output_dir=output_dir)
        replaced_text, mapping = mapper.prepare_markdown_for_translation(file_path)

        base_name = os.path.splitext(os.path.basename(file_path))[0]

        # 保存 mapping 信息
        mapping_file_path = os.path.join(output_dir, f"{base_name}_mapping.json")
        with open(mapping_file_path, "w", encoding="utf-8") as file:
            json.dump(mapping, file, ensure_ascii=False, indent=4)

        # 保存 replaced_text 信息
        replaced_text_file_path = os.path.join(output_dir, f"{base_name}_replaced_text.md")
        with open(replaced_text_file_path, "w", encoding="utf-8") as file:
            file.write(replaced_text)
        logging.info(f"Replaced text saved to: {replaced_text_file_path}")

        # 翻译处理
        translation = await translate_markdown(
            source_lang=source_lang,
            target_lang=target_lang,
            country=country,
            source_text=replaced_text,
        )

        if translation:
            # 恢复原始内容并保存
            final_text = mapper.restore_text(translation)
            translated_file_path = os.path.join(output_dir, f"{base_name}_translated.md")
            with open(translated_file_path, "w", encoding="utf-8") as file:
                file.write(final_text)
            logging.info(f"Translation saved to: {translated_file_path}")

            # # 保存为PDF
            # pdf_file_path = os.path.join(output_dir, f"{base_name}_translated.pdf")
            # save_markdown_as_pdf(final_text, pdf_file_path)
            # logging.info(f"PDF saved to: {pdf_file_path}")
        else:
            logging.error(f"Translation failed for file {file_path}")

    except Exception as e:
        logging.error(f"Error processing file {file_path}: {traceback.format_exc()}")
        raise  # 重新抛出异常，以便主程序可以捕获它


def save_markdown_as_pdf(markdown_text, pdf_file_path):
    def get_system_font_path(font_name):
        # 获取Windows字体目录
        font_dir = os.path.join(os.environ['WINDIR'], 'Fonts')
        for file_name in os.listdir(font_dir):
            if file_name.lower().startswith(font_name.lower()):
                return os.path.join(font_dir, file_name)
        return None

    # 将Markdown内容转换为HTML
    html_text = markdown(markdown_text)
    # 创建PDF对象
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # 获取并添加宋体（SimSun）字体路径
    simsun_path = get_system_font_path('simsun')
    if simsun_path:
        pdf.add_font('SimSun', '', simsun_path, uni=True)
    else:
        raise FileNotFoundError("SimSun font not found in the system fonts directory.")

    # 获取并添加Times New Roman字体路径
    times_path = get_system_font_path('times')
    if times_path:
        pdf.add_font('Times', '', times_path, uni=True)
    else:
        raise FileNotFoundError("Times New Roman font not found in the system fonts directory.")

    # 初始字体设置为宋体，处理中文
    pdf.set_font('SimSun', size=12)

    # 分别处理中文和英文字符
    def process_text(text):
        result = []
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                pdf.set_font('SimSun', size=12)
            else:
                pdf.set_font('Times', size=12)
            result.append(char)
        return ''.join(result)

    # 将Markdown内容逐字处理并添加到PDF
    processed_text = process_text(html_text)
    pdf.multi_cell(0, 10, processed_text)
    pdf.output(pdf_file_path)


if __name__ == '__main__':
    file_paths = [
        r"C:\Users\yongjie.yang\Desktop\agent综述\agent综述\agent综述.md"
        ,
    ]
    for path in file_paths:
        try:
            asyncio.run(process_markdown_file(path, "英语", "汉语", "中国"))
            print(f"Processing completed for {path}")
        except Exception as e:
            print(f"Error processing {path}: {traceback.format_exc()}")
