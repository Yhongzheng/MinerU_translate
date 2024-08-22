if True:
    improvement_prompt = """
    这是一个针对Markdown格式文档内容的翻译质量改进请求，翻译方向是从 {source_lang} 到 {target_lang}。请根据以下标准对提供的译文进行分析、批评，并基于这些批评和建议改进翻译：
    
    注意：
    1. 请严格保留原文的Markdown结构，确保所有的占位符（<PH></PH>）及其包裹的内容不被翻译或修改。
    2. 已经用<PH></PH>标记的部分，包括HTML标签、YAML头部、注释、代码块、表格、公式、行内代码、图片和网址等元素，请勿修改这些部分的内容或格式。
    3. 遇到作者姓名和参考文献时，请保持原文，不进行翻译。
    4. 专有名词保留：原文中的专有名词（如人名、地名、品牌名等）应保持不变，不要翻译。
    4.1 不需要翻译的专有名词举例如(不区分大小写)：AI Agent、transformer、LLM、dspy、LangChain等。
    5. 请仅对需要改进的文本内容进行调整，避免对已经正确的部分（如Markdown结构、占位符等）进行修改。
    6. 请以标准的 UTF-8 编码返回结果，避免使用 Unicode 转义字符。
    
    源文本和初次翻译如下，以 XML 标签 <SOURCE_TEXT></SOURCE_TEXT> 和 <TRANSLATION></TRANSLATION> 分隔：
    
    <SOURCE_TEXT>
    {original_text}
    </SOURCE_TEXT>
    
    <TRANSLATION>
    {translated_text}
    </TRANSLATION>
    
    请在编写建议和改进时，特别注意以下方面：
    (i) 准确性：通过纠正添加、误译、遗漏或未翻译的错误，确保翻译准确反映源文本的内容。
    (ii) 流畅性：确保译文符合 {target_lang} 的语法、拼写和标点符号规则，避免不必要的重复。
    (iii) 风格：确保翻译反映源文本的风格，并考虑 {country} 的文化背景。
    (iv) 术语：确保术语使用的一致性，避免上下文不合适或不一致的使用。
    (v) 其他错误：修正其他可能存在的翻译错误。
    
    输出要求：
    1. 提供具体、有帮助的建议清单。
    2. 直接输出改进后的译文，不要输出其他非必要内容。
    3. 改进后的译文应符合上述所有要求，保留原始 Markdown 结构和所有占位符。
    
    请按下文json格式要求输出，不要有其他非json内容，并确保Markdown格式未被改变：
    {{
    "attention": 你认为翻译质量可以改进的方面,
    "translate": 改进后的译文
    }}
    """

print(improvement_prompt)