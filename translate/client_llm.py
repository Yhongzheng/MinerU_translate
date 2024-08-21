# -*- coding: utf-8 -*-

import base64
import time

import openai
import requests
import os
import gradio as gr
import threading
from queue import Queue
import traceback
import re
import json
import traceback
from typing import Union, List
from typing import List, Tuple, Optional
import dashscope
import qianfan
from http import HTTPStatus

current_dir = os.path.dirname(__file__)
file_path = os.path.join(current_dir, "API_KEYS.json")

with open(file_path, 'r', encoding='utf-8') as f:
    json_keys = json.load(f)


# 编码图像的函数
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def client_qwen(system_message: str, user_message: str, model: str = "qwen2-72b-instruct",
                max_tokens: int = 4096, temperature: int = 0, result_format: str = "text",
                image_paths: list = None, api_key: str = None, base_url: str = None):
    """
    发送请求到 DashScope。

    Args:
        system_message (str): 系统消息。这个不能为空，比如有默认值。
        user_message (str): 用户消息。
        model (str): 使用的模型。默认为 "qwen-vl-plus"。
        max_tokens (int): 最大token数。默认为4096。
        temperature (int): 温度。默认为0。
        result_format (str): 返回格式。[text|message]，默认为text，当为message时，输出参考message结果示例(json)
        image_paths (list): 图像路径列表。默认为None。
        api_key (str): API Key。如果未提供，则使用环境变量。
        base_url (str): Base URL。这个只有当使用openai的SDK采用，7月2号报错了，不再用openai的SDK，而用dashscope

    Returns:
        tuple: 返回响应内容和token使用数量。
    """
    dashscope.api_key = json_keys['cstore_dashscope']  # 如果您没有配置环境变量，请在此处用您的API Key进行替换
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"  # 填写 DashScope SDK的base_url
    try:
        # 通义千问的系统信息不能为空，所以必须给一个默认值。
        system_message = "你是一个帮助用户回答问题的助手。" if not system_message else system_message
        # 非图像模式
        if not image_paths:
            if result_format == 'message':
                system_message += "\n结果以json格式输出，且只输出json内容，不要有其他内容。"
            messages = [
                {"role": "system", "content": system_message},
                {'role': 'user', 'content': user_message}]
            response = dashscope.Generation.call(
                model=model,
                messages=messages,
                result_format=result_format
            )
            if response.status_code == HTTPStatus.OK:
                print(response)
                if result_format == 'text':
                    return response['output']['text'], response['usage']['total_tokens']
                else:  # json 格式的
                    result_json = response['output']['choices'][0]['message']['content']
                    return result_json, response['usage']['total_tokens']
            else:
                print('Request id: %s, Status code: %s, error code: %s, error message: %s' % (
                    response.request_id, response.status_code,
                    response.code, response.message
                ))
        else:
            image_urls = [{"image": image_path} for image_path in image_paths]

            messages = [{
                'role': 'system',
                'content': [{'text': system_message}]
            }, {
                'role': 'user',
                'content': [*image_urls, {'text': user_message}]
            }]
            response = dashscope.MultiModalConversation.call(
                model=model,
                messages=messages,
                result_format=result_format
            )
            if response.status_code == HTTPStatus.OK:  # 如果调用成功，则打印response
                print(response)
                result_text = response['output']['choices'][0]['message']['content'][0]['text']
                total_tokens = sum(
                    response['usage'][token] for token in ['input_tokens', 'output_tokens', 'image_tokens'])
                return result_text, total_tokens
            else:  # 如果调用失败
                return f"错误码：{response.code}\n错误信息：{response.message}", 0

    except Exception as e:
        error_message = f"发送给 通义千问 请求时发生错误: {traceback.format_exc()}"
        return error_message, None


def client_qianfan(
        prompt: str,
        system_message: str = "You are a helpful assistant.",
        model: str = "ERNIE-Speed-128K",
        temperature: float = 0.1
) -> Union[str, dict]:
    """
    使用 OpenAI API 生成补全内容。

    参数:
        prompt (str): 用户的提示或查询。
        system_message (str, 可选): 设置助手上下文的系统消息。
            默认为 "You are a helpful assistant."。
        model (str, 可选): 用于生成补全内容的 OpenAI 模型名称。
            默认为 "gpt-4-turbo"。
        temperature (float, 可选): 控制生成文本随机性的采样温度。
            默认为 0.3。
        json_mode (bool, 可选): 是否以 JSON 格式返回响应。
            默认为 False。

    返回值:
        Union[str, dict]: 生成的补全内容。
            如果 json_mode 为 True，返回完整的 API 响应字典。
            如果 json_mode 为 False，返回生成的文本字符串。
    """
    # 设置环境变量
    os.environ["QIANFAN_ACCESS_KEY"] = json_keys['QIANFAN_ACCESS_KEY']
    os.environ["QIANFAN_SECRET_KEY"] = json_keys['QIANFAN_SECRET_KEY']

    client = qianfan.ChatCompletion()

    resp = client.do(
        model=model,
        system=system_message,
        temperature=temperature,
        messages=[
            {"role": "user", "content": prompt}
        ])
    return resp["body"]['result']

