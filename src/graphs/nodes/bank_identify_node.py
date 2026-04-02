import os
import json
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import LLMClient
from langchain_core.messages import SystemMessage, HumanMessage
from graphs.state import BankIdentifyInput, BankIdentifyOutput


def bank_identify_node(
    state: BankIdentifyInput, config: RunnableConfig, runtime: Runtime[Context]
) -> BankIdentifyOutput:
    """
    title: 银行类型识别
    desc: 使用视觉模型从PDF图片中识别银行类型、账户户名和账号
    integrations: 大语言模型（视觉模型）
    """
    ctx = runtime.context

    # 读取大模型配置文件
    cfg_file = os.path.join(
        os.getenv("COZE_WORKSPACE_PATH", ""), config["metadata"]["llm_cfg"]
    )
    with open(cfg_file, "r", encoding="utf-8") as fd:
        _cfg = json.load(fd)

    llm_config = _cfg.get("config", {})
    sp = _cfg.get("sp", "")

    # 只使用第一页图片识别银行信息
    first_image_url = state.pdf_images[0] if state.pdf_images else ""

    # 构建多模态消息
    messages = [
        SystemMessage(content=sp),
        HumanMessage(content=[
            {
                "type": "text",
                "text": "请识别这张银行流水图片中的银行名称、账户户名和账号。注意：账号中的星号(*)是脱敏标记，请保留原样。"
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": first_image_url
                }
            }
        ])
    ]

    # 调用视觉模型
    llm_client = LLMClient(ctx=ctx)
    response = llm_client.invoke(
        messages=messages,
        model="doubao-seed-1-6-vision-250815",  # 使用视觉模型
        temperature=llm_config.get("temperature", 0.1),
        max_completion_tokens=llm_config.get("max_completion_tokens", 2048)
    )

    # 提取响应内容
    if isinstance(response.content, str):
        content_text = response.content.strip()
    elif isinstance(response.content, list):
        text_parts = []
        for item in response.content:
            if isinstance(item, str):
                text_parts.append(item)
            elif isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(item.get("text", ""))
        content_text = "".join(text_parts).strip()
    else:
        content_text = ""

    # 解析JSON
    try:
        # 尝试提取JSON对象
        start_idx = content_text.find("{")
        end_idx = content_text.rfind("}") + 1
        if start_idx != -1 and end_idx > start_idx:
            json_str = content_text[start_idx:end_idx]
            result = json.loads(json_str)
            bank_name = result.get("bank_name", "未知银行")
            account_name = result.get("account_name", "")
            account_number = result.get("account_number", "")
        else:
            bank_name = "未知银行"
            account_name = ""
            account_number = ""
    except json.JSONDecodeError:
        # 如果JSON解析失败，尝试直接提取银行名称
        bank_name = content_text if content_text else "未知银行"
        account_name = ""
        account_number = ""

    return BankIdentifyOutput(
        bank_name=bank_name,
        account_name=account_name,
        account_number=account_number
    )
