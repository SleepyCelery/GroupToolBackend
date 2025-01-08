from abc import ABC, abstractmethod
import requests
from element_group import Element
from typing import List
from functools import lru_cache
from datetime import timedelta
from loguru import logger


class ElementSource(ABC):
    display_name: str = "未命名数据源"

    @abstractmethod
    def get_elements(self) -> List[Element]:
        """从数据源获取Element列表的抽象方法"""
        pass


@lru_cache(maxsize=1, typed=False)
def get_newest_lol_api_version():
    """获取最新的LOL API版本，结果缓存1天"""
    try:
        url = "https://ddragon.leagueoflegends.com/api/versions.json"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()[0]
    except requests.RequestException as e:
        logger.error(f"获取最新API版本失败: {e}")
        return "14.24.1"


class LolHeroSource(ElementSource):
    display_name = "英雄联盟英雄数据"
    api_version: str = get_newest_lol_api_version()

    @classmethod
    def get_elements(cls) -> List[Element]:
        """从英雄联盟API获取所有英雄名字"""
        # 官方API地址
        url = f"https://ddragon.leagueoflegends.com/cdn/{cls.api_version}/data/zh_CN/champion.json"

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            # 提取所有英雄名字
            heroes = [
                Element(f"{champion_data['name']} {champion_data['title']}")
                for champion_data in data["data"].values()
            ]
            return heroes

        except requests.RequestException as e:
            logger.error(f"获取英雄数据失败: {e}")
            return []


def get_all_sources():
    return {cls.display_name: cls for cls in ElementSource.__subclasses__()}


def get_source_by_display_name(display_name: str):
    sources = get_all_sources()
    return sources.get(display_name)


def get_elements_from_source(display_name: str):
    source = get_source_by_display_name(display_name)
    if source:
        return source.get_elements()
    else:
        logger.error(f"未找到数据源: {display_name}")
        return []
