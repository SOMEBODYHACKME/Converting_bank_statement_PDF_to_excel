from langgraph.graph import StateGraph, END
from graphs.state import (
    GlobalState,
    GraphInput,
    GraphOutput,
)

# 导入节点函数
from graphs.nodes.pdf_to_images_node import pdf_to_images_node
from graphs.nodes.bank_identify_node import bank_identify_node
from graphs.nodes.ocr_recognition_node import ocr_recognition_node
from graphs.nodes.transaction_extract_node import transaction_extract_node
from graphs.nodes.data_validation_node import data_validation_node
from graphs.nodes.excel_export_node import excel_export_node


# 创建状态图
builder = StateGraph(
    GlobalState, input_schema=GraphInput, output_schema=GraphOutput
)

# 添加节点
builder.add_node("pdf_to_images", pdf_to_images_node)
builder.add_node(
    "bank_identify",
    bank_identify_node,
    metadata={"type": "agent", "llm_cfg": "config/bank_identify_llm_cfg.json"},
)
builder.add_node("ocr_recognition", ocr_recognition_node)
builder.add_node(
    "transaction_extract",
    transaction_extract_node,
    metadata={"type": "agent", "llm_cfg": "config/transaction_extract_llm_cfg.json"},
)
builder.add_node(
    "data_validation",
    data_validation_node,
    metadata={"type": "agent", "llm_cfg": "config/data_validation_llm_cfg.json"},
)
builder.add_node("excel_export", excel_export_node)

# 设置入口点
builder.set_entry_point("pdf_to_images")

# 添加边 - 构建DAG
builder.add_edge("pdf_to_images", "bank_identify")
builder.add_edge("bank_identify", "ocr_recognition")
builder.add_edge("ocr_recognition", "transaction_extract")
builder.add_edge("transaction_extract", "data_validation")
builder.add_edge("data_validation", "excel_export")
builder.add_edge("excel_export", END)

# 编译图
main_graph = builder.compile()
