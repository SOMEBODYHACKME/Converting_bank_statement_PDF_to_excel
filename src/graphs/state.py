from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from utils.file.file import File


# ==================== 全局状态 ====================

class GlobalState(BaseModel):
    """全局状态定义"""
    pdf_file: File = Field(..., description="上传的PDF文件")
    pdf_images: List[str] = Field(default=[], description="PDF转换后的图片URL列表")
    pdf_text: str = Field(default="", description="PDF提取的原始文本（备用）")
    bank_name: str = Field(default="", description="识别出的银行名称")
    account_name: str = Field(default="", description="账户户名")
    account_number: str = Field(default="", description="账号")
    ocr_text: str = Field(default="", description="OCR识别的表格文本")
    raw_transactions: List[Dict[str, Any]] = Field(default=[], description="提取的原始交易记录")
    validated_transactions: List[Dict[str, Any]] = Field(default=[], description="校验后的交易记录")
    excel_url: str = Field(default="", description="生成的Excel文件URL")


# ==================== 图输入输出 ====================

class GraphInput(BaseModel):
    """工作流输入"""
    pdf_file: File = Field(..., description="银行流水PDF文件")


class GraphOutput(BaseModel):
    """工作流输出"""
    bank_name: str = Field(..., description="识别出的银行名称")
    account_name: str = Field(..., description="账户户名")
    transaction_count: int = Field(..., description="交易记录数量")
    excel_url: str = Field(..., description="生成的Excel文件下载链接")


# ==================== 节点输入输出定义 ====================

# PDF转图片节点
class PDFToImagesInput(BaseModel):
    """PDF转图片节点输入"""
    pdf_file: File = Field(..., description="PDF文件")


class PDFToImagesOutput(BaseModel):
    """PDF转图片节点输出"""
    pdf_images: List[str] = Field(..., description="转换后的图片URL列表")


# 银行类型识别节点
class BankIdentifyInput(BaseModel):
    """银行类型识别节点输入"""
    pdf_images: List[str] = Field(..., description="PDF图片URL列表")


class BankIdentifyOutput(BaseModel):
    """银行类型识别节点输出"""
    bank_name: str = Field(..., description="识别出的银行名称")
    account_name: str = Field(default="", description="账户户名")
    account_number: str = Field(default="", description="账号")


# OCR表格识别节点
class OCRRecognitionInput(BaseModel):
    """OCR表格识别节点输入"""
    pdf_images: List[str] = Field(..., description="PDF图片URL列表")


class OCRRecognitionOutput(BaseModel):
    """OCR表格识别节点输出"""
    ocr_text: str = Field(..., description="OCR识别的表格文本")


# 流水数据提取节点
class TransactionExtractInput(BaseModel):
    """流水数据提取节点输入"""
    ocr_text: str = Field(..., description="OCR识别的表格文本")
    bank_name: str = Field(..., description="银行名称")


class TransactionExtractOutput(BaseModel):
    """流水数据提取节点输出"""
    transactions: List[Dict[str, Any]] = Field(..., description="提取的交易记录列表")


# 数据校验与修正节点
class DataValidationInput(BaseModel):
    """数据校验与修正节点输入"""
    transactions: List[Dict[str, Any]] = Field(..., description="原始交易记录")
    bank_name: str = Field(..., description="银行名称")


class DataValidationOutput(BaseModel):
    """数据校验与修正节点输出"""
    validated_transactions: List[Dict[str, Any]] = Field(..., description="校验后的交易记录")


# Excel导出节点
class ExcelExportInput(BaseModel):
    """Excel导出节点输入"""
    validated_transactions: List[Dict[str, Any]] = Field(..., description="校验后的交易记录")
    bank_name: str = Field(..., description="银行名称")
    account_name: str = Field(default="", description="账户户名")
    account_number: str = Field(default="", description="账号")


class ExcelExportOutput(BaseModel):
    """Excel导出节点输出"""
    excel_url: str = Field(..., description="Excel文件下载链接")
    transaction_count: int = Field(..., description="交易记录数量")
