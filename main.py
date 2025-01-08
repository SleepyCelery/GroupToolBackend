from fastapi import FastAPI
from loguru import logger
from models import *
from sqlmodel import Session, select
from element_group import *
from datasources import (
    get_all_sources,
    get_source_by_display_name,
    get_elements_from_source,
)
import os

SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8080")
DEBUG = os.getenv("DEBUG", "False")

hot_element_cache = HotElementsCache(max_size=10)

app = FastAPI()


@app.get("/latest_groups", response_model=GeneralResponse)
def get_latest_groups():
    """
    获取最新的 10 个分组信息，用于首页展示
    """
    try:
        with Session(engine) as session:
            statement = select(GroupResult).order_by(GroupResult.id.desc()).limit(10)
            groups = session.exec(statement).all()
            data = []
            for group in groups:
                data.append(
                    BriefGroupResultResponse(
                        id=group.id,
                        group_name=group.group_name,
                        is_public=group.is_public,
                        created_at=group.created_at,
                    )
                )
            return GeneralResponse(
                success=True,
                message="Latest groups fetched successfully",
                data=GetLatestGroupsResponse(groups=data),
            )
    except Exception as e:
        logger.error(f"Error fetching latest groups: {e}")
        return GeneralResponse(
            success=False, message="Failed to fetch latest groups", data=None
        )


@app.post("/group_result", response_model=GeneralResponse)
def create_group(group: CreateGroupRequest):
    """
    创建一个新分组
    """
    try:
        with Session(engine) as session:
            group_name = group.group_name
            group_mode = group.group_mode
            if isinstance(group_mode, str):
                group_mode = GroupMode(group_mode)
            if group_mode == GroupMode.SIZE:
                group_size = group.group_size
            else:
                group_size = None
            group_count = group.group_count
            is_public = group.is_public
            if is_public:
                private_password = None
            else:
                private_password = group.private_password
            source_elements = group.source_elements
            data_source = group.data_source
            all_elements = []
            if source_elements:
                for element in source_elements:
                    all_elements.append(Element(value=element))
                # 如果公开，则将元素添加到热门元素缓存中
                if is_public:
                    for element in source_elements:
                        hot_element_cache.add_element(Element(element))
            if data_source:
                for source in data_source:
                    source_class = get_source_by_display_name(source)
                    if source_class:
                        elements = get_elements_from_source(source)
                        all_elements.extend(elements)
            group_instance = Group(pool=all_elements)
            result = group_instance.group_elements(
                mode=group_mode.value,
                group_num=group_count,
                group_size=group_size,
                randomize=True,
            )
            group_result_row = GroupResult(
                group_name=group_name,
                group_mode=group_mode,
                is_public=is_public,
                private_password=private_password,
                source_elements=source_elements,
                group_count=group_count,
                group_result=Element.to_str(result),
            )
            session.add(group_result_row)
            session.commit()
            logger.info(f"Group created successfully: {group_result_row.id}")
            return GeneralResponse(
                success=True,
                message="Group created successfully",
                data=GroupResultResponse(
                    id=group_result_row.id,
                    group_name=group_name,
                    group_mode=group_mode,
                    is_public=is_public,
                    source_elements=source_elements,
                    data_source=data_source,
                    group_count=group_count,
                    group_result=Element.to_str(result),
                    created_at=group_result_row.created_at,
                    share_url=f"{SERVER_URL}/group_result?group_id={group_result_row.id}&password={private_password}",
                ),
            )
    except Exception as e:
        logger.error(f"Error creating group: {e}")
        return GeneralResponse(
            success=False, message="Failed to create group", data=None
        )


@app.get("/group_result", response_model=GeneralResponse)
def get_group_result(group_id: int, password: Optional[str] = None):
    """
    根据 Group ID 获取分组结果
    如果分组结果不存在，则返回失败
    如果分组结果存在，则判断是否为公开
    如果为公开，则返回分组结果
    如果为私有，则判断是否输入了密码
    如果输入了密码，则判断密码是否正确
    如果密码正确，则返回分组结果
    如果密码不正确，则返回失败
    """
    with Session(engine) as session:
        statement = select(GroupResult).where(GroupResult.id == group_id)
        group_result = session.exec(statement).first()
        if group_result:
            if group_result.is_public:
                return GeneralResponse(
                    success=True,
                    message="Result fetched successfully",
                    data=group_result.model_dump(exclude={"private_password"}),
                )
            else:
                if password == group_result.private_password:
                    return GeneralResponse(
                        success=True,
                        message="Result fetched successfully",
                        data=group_result.model_dump(exclude={"private_password"}),
                    )
                else:
                    return GeneralResponse(
                        success=False,
                        message="Invalid password",
                        data=None,
                    )
        else:
            return GeneralResponse(
                success=False,
                message="Result not found",
                data=None,
            )


@app.get("/hot_elements", response_model=GeneralResponse)
def get_hot_elements():
    """
    获取热门元素
    """
    try:
        return GeneralResponse(
            success=True,
            message="Hot elements fetched successfully",
            data=Element.to_str(hot_element_cache.get_hot_elements()),
        )
    except Exception as e:
        logger.error(f"Error fetching hot elements: {e}")
        return GeneralResponse(
            success=False, message="Failed to fetch hot elements", data=None
        )


@app.get("/data_sources", response_model=GeneralResponse)
def get_data_sources():
    """
    获取所有数据源
    """
    return GeneralResponse(
        success=True,
        message="Data sources fetched successfully",
        data=list(get_all_sources().keys()),
    )


@app.get("/search_groups", response_model=GeneralResponse)
def search_groups(query: str):
    """
    根据搜索字符串查询分组
    支持通过ID或分组名称进行搜索
    """
    try:
        with Session(engine) as session:
            # 尝试将查询字符串转换为整数（用于ID搜索）
            try:
                query_id = int(query)
                # 按ID搜索
                statement = select(GroupResult).where(GroupResult.id == query_id)
            except ValueError:
                # 按名称搜索
                statement = select(GroupResult).where(
                    GroupResult.group_name.contains(query)
                )

            groups = session.exec(statement).all()

            data = []
            for group in groups:
                data.append(
                    BriefGroupResultResponse(
                        id=group.id,
                        group_name=group.group_name,
                        is_public=group.is_public,
                        created_at=group.created_at,
                    )
                )

            return GeneralResponse(
                success=True,
                message="Search completed successfully",
                data=GetLatestGroupsResponse(groups=data),
            )
    except Exception as e:
        logger.error(f"Error searching groups: {e}")
        return GeneralResponse(
            success=False, message="Failed to search groups", data=None
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8080)
