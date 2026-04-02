import os
import json
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import LLMClient
from langchain_core.messages import SystemMessage, HumanMessage
from graphs.state import OCRRecognitionInput, OCRRecognitionOutput


def ocr_recognition_node(
    state: OCRRecognitionInput, config: RunnableConfig, runtime: Runtime[Context]
) -> OCRRecognitionOutput:
    """
    title: OCR表格识别
    desc: 使用视觉模型识别PDF图片中的银行流水表格，准确提取每行数据
    integrations: 大语言模型（视觉模型）
    """
    ctx = runtime.context

    # OCR识别的系统提示词
    ocr_sp = """你是一个专业的银行流水表格OCR识别专家。

你的任务是：
1. 准确识别图片中的银行流水表格
2. 保持表格的行列结构，不要跳行、漏行或错行
3. 完整提取每一行的所有字段
4. 保持原始数据格式，不要修改或推测数据

识别要求：
- 交易日期：保持原格式，如"2023-01-01"或"2023/01/01"
- 收入金额：如果是收入，提取金额数字；如果不是，标记为空或0
- 支出金额：如果是支出，提取金额数字；如果不是，标记为空或0
- 余额：提取交易后的余额数字
- 对方户名：提取对方账户名称，保留星号(*)脱敏标记
- 对方账号：提取对方账号，保留星号(*)脱敏标记
- 摘要：提取交易摘要内容
- 币种：如CNY、USD等

输出格式：
按照表格顺序，逐行输出，每行用|分隔字段：
日期|收入|支出|余额|对方户名|对方账号|摘要|币种

重要提示：
1. 必须逐行识别，不能跳过任何一行
2. 如果某行数据不完整，用"空"标记
3. 如果某行是表头或非数据行，跳过
4. 数字只保留数字和小数点，去除逗号等分隔符
"""

    llm_client = LLMClient(ctx=ctx)
    all_ocr_text = []

    # 对每一页图片进行OCR识别
    for i, image_url in enumerate(state.pdf_images):
        # 构建消息
        messages = [
            SystemMessage(content=ocr_sp),
            HumanMessage(content=[
                {
                    "type": "text",
                    "text": f"这是银行流水的第{i+1}页，请识别表格中的所有交易记录，保持原始行列顺序，不要跳行或漏行。"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_url
                    }
                }
            ])
        ]

        # 调用视觉模型
        response = llm_client.invoke(
            messages=messages,
            model="doubao-seed-1-6-vision-250815",
            temperature=0.1,
            max_completion_tokens=4096
        )

        # 提取响应内容
        if isinstance(response.content, str):
            ocr_text = response.content.strip()
        elif isinstance(response.content, list):
            text_parts = []
            for item in response.content:
                if isinstance(item, str):
                    text_parts.append(item)
                elif isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            ocr_text = "".join(text_parts).strip()
        else:
            ocr_text = ""

        # 添加分页标记
        all_ocr_text.append(f"=== 第{i+1}页 ===\n{ocr_text}")

    # 合并所有页的OCR结果
    combined_ocr_text = "\n\n".join(all_ocr_text)

    return OCRRecognitionOutput(ocr_text=combined_ocr_text)
