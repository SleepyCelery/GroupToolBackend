from sqlmodel import create_engine, SQLModel, Field
from sqlalchemy import JSON
from typing import Optional, List, Any
from datetime import datetime, timezone
import os
from enum import Enum
from pydantic import ValidationError, model_validator, FieldValidationInfo

# 创建SQLite数据库引擎
DATABASE_URL = "sqlite:///database.db"
engine = create_engine(DATABASE_URL, echo=True)


class GroupMode(Enum):
    EQUAL = "equal"
    SIZE = "size"


class GroupResult(SQLModel, table=True):
    """
    分组结果 Model
    """

    id: Optional[int] = Field(default=None, primary_key=True, description="分组ID")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="创建时间"
    )
    group_name: str = Field(default="", description="分组名称", index=True)
    group_mode: GroupMode = Field(default=GroupMode.EQUAL, description="分组模式")
    group_size: Optional[int] = Field(
        default=None, description="每组元素数量，仅在按量分组模式下有效"
    )
    is_public: bool = Field(default=True, description="是否公开")
    private_password: Optional[str] = Field(
        default=None, description="私有分组密码，当is_public为false时必填"
    )
    source_elements: Optional[List[str]] = Field(
        default=None, sa_type=JSON, description="源元素列表"
    )
    data_source: Optional[List[str]] = Field(
        default=None, sa_type=JSON, description="数据源列表"
    )
    group_count: int = Field(default=2, description="分组数量")
    group_result: List[List[str]] = Field(
        default=[], sa_type=JSON, description="分组结果"
    )

    @model_validator(mode="after")
    def validate_private_password(self) -> "GroupResult":
        if not self.is_public and not self.private_password:
            raise ValueError("Private password is required for private groups")
        return self

    @model_validator(mode="after")
    def validate_group_size(self) -> "GroupResult":
        if self.group_mode == GroupMode.SIZE and self.group_size is None:
            raise ValueError("Group size is required when group mode is SIZE")
        return self

    class Config:
        table_name = "grouping_results"


class CreateGroupRequest(SQLModel, table=False):
    """
    创建分组请求 Model
    """

    group_name: str
    is_public: bool = True
    private_password: Optional[str] = None
    source_elements: Optional[List[str]] = None
    data_source: Optional[List[str]] = None
    group_mode: GroupMode = Field(default=GroupMode.EQUAL)
    group_count: int = Field(default=2)
    group_size: Optional[int] = None

    @model_validator(mode="before")
    def check_at_least_one_source(cls, data: dict) -> dict:
        if not data.get("source_elements") and not data.get("data_source"):
            raise ValueError("Need at least one source")
        return data

    @model_validator(mode="after")
    def validate_group_size(self) -> "CreateGroupRequest":
        if self.group_mode == GroupMode.SIZE and self.group_size is None:
            raise ValueError("Group size is required when group mode is SIZE")
        return self


class GroupResultResponse(SQLModel, table=False):
    """
    完整分组结果展示响应 Model
    """

    id: int
    group_name: str
    group_mode: GroupMode
    is_public: bool
    source_elements: Optional[List[str]] = None
    data_source: Optional[List[str]] = None
    group_count: int
    group_result: List[List[str]]
    created_at: datetime
    share_url: str

class BriefGroupResultResponse(SQLModel, table=False):
    """
    简要分组结果展示响应 Model
    """

    id: int
    group_name: str
    is_public: bool
    created_at: datetime

class GetLatestGroupsResponse(SQLModel, table=False):
    """
    获取最新分组响应 Model
    """

    groups: List[BriefGroupResultResponse]


class GetHotElementsResponse(SQLModel, table=False):
    """
    获取热门元素响应 Model
    """

    elements: List[str]


class GetGroupResultResponse(SQLModel, table=False):
    """
    获取分组响应 Model
    """

    group: GroupResultResponse


class GeneralResponse(SQLModel, table=False):
    """
    通用响应 Model
    """

    success: bool
    message: str
    data: Any


# 创建数据库表（如果不存在）
if not os.path.exists("database.db"):
    SQLModel.metadata.create_all(engine)
