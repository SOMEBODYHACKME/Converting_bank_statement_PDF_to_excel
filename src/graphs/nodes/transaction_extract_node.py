import os
import json
from jinja2 import Template
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import LLMClient
from langchain_core.messages import SystemMessage, HumanMessage
from graphs.state import TransactionExtractInput, TransactionExtractOutput


def transaction_extract_node(
    state: TransactionExtractInput, config: RunnableConfig, runtime: Runtime[Context]
) -> TransactionExtractOutput:
    """
    title: 流水数据提取
    desc: 从OCR识别结果中提取结构化的交易记录数据
    integrations: 大语言模型
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
    up = _cfg.get("up", "")

    # 使用jinja2模板渲染用户提示词
    up_tpl = Template(up)
    user_prompt_content = up_tpl.render({
        "bank_name": state.bank_name,
        "ocr_text": state.ocr_text
    })

    # 构建消息
    messages = [
        SystemMessage(content=sp),
        HumanMessage(content=user_prompt_content)
    ]

    # 调用大模型
    llm_client = LLMClient(ctx=ctx)
    response = llm_client.invoke(
        messages=messages,
        model=llm_config.get("model", "doubao-seed-1-8-251228"),
        temperature=llm_config.get("temperature", 0.1),
        top_p=llm_config.get("top_p", 0.9),
        max_completion_tokens=llm_config.get("max_completion_tokens", 16384)
    )

    # 提取JSON数据
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
        content_text = "[]"

    # 解析JSON
    try:
        # 尝试提取JSON数组
        start_idx = content_text.find("[")
        end_idx = content_text.rfind("]") + 1
        if start_idx != -1 and end_idx > start_idx:
            json_str = content_text[start_idx:end_idx]
            transactions = json.loads(json_str)
        else:
            transactions = []
    except json.JSONDecodeError:
        transactions = []

    return TransactionExtractOutput(transactions=transactions)
