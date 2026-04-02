import os
import tempfile
import shutil
from typing import List
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from pdf2image import convert_from_path
import requests
from graphs.state import PDFToImagesInput, PDFToImagesOutput
from coze_coding_dev_sdk.s3 import S3SyncStorage


def pdf_to_images_node(
    state: PDFToImagesInput, config: RunnableConfig, runtime: Runtime[Context]
) -> PDFToImagesOutput:
    """
    title: PDF转图片
    desc: 将PDF文件转换为图片，用于后续OCR识别表格结构
    integrations: Storage
    """
    ctx = runtime.context
    
    # 初始化S3存储客户端
    storage = S3SyncStorage(
        endpoint_url=os.getenv("COZE_BUCKET_ENDPOINT_URL"),
        access_key="",
        secret_key="",
        bucket_name=os.getenv("COZE_BUCKET_NAME"),
        region="cn-beijing",
    )
    
    # 获取PDF文件URL
    pdf_url = state.pdf_file.url
    
    # 下载PDF到临时文件
    temp_dir = tempfile.mkdtemp()
    pdf_path = os.path.join(temp_dir, "input.pdf")
    
    try:
        # 下载PDF文件
        response = requests.get(pdf_url, timeout=60)
        response.raise_for_status()
        
        with open(pdf_path, "wb") as f:
            f.write(response.content)
        
        # 将PDF转换为图片
        images = convert_from_path(pdf_path, dpi=300)  # 使用300 DPI保证清晰度
        
        # 上传图片到对象存储
        image_urls: List[str] = []
        
        for i, image in enumerate(images):
            # 保存图片到临时文件
            image_path = os.path.join(temp_dir, f"page_{i+1}.png")
            image.save(image_path, "PNG")
            
            # 读取图片内容
            with open(image_path, "rb") as f:
                image_content = f.read()
            
            # 上传到对象存储
            file_key = storage.upload_file(
                file_content=image_content,
                file_name=f"bank_statement/page_{i+1}.png",
                content_type="image/png",
            )
            
            # 生成签名URL
            image_url = storage.generate_presigned_url(
                key=file_key,
                expire_time=86400,  # 1天有效期
            )
            image_urls.append(image_url)
    finally:
        # 清理临时文件
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    return PDFToImagesOutput(pdf_images=image_urls)
