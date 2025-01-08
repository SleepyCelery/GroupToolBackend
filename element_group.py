from typing import List, Optional, Union
import random
from collections import OrderedDict


class Element:
    def __init__(self, value: str):
        if not isinstance(value, str):
            raise ValueError("The value must be a string")
        self.value = value

    def __repr__(self):
        return f"Element({self.value})"

    @classmethod
    def to_str(cls, elements) -> Union[List[str], str]:
        """
        将Element对象或Element列表转换为字符串或字符串列表
        :param elements: 可以是单个Element对象或Element列表
        :return: 对应的字符串或字符串列表
        """
        if isinstance(elements, Element):
            return elements.value
        elif isinstance(elements, list):
            result = []
            for element in elements:
                if isinstance(element, Element):
                    result.append(element.value)
                elif isinstance(element, list):
                    result.append(cls.to_str(element))
                else:
                    raise ValueError("Invalid element type")
            return result
        else:
            raise ValueError("Input must be an Element or a list of Elements")


class Group:
    def __init__(self, pool: Optional[List[Element]] = None):
        self.pool = pool or []  # 元素池

    def add_element(self, element: Element):
        """向池中添加元素"""
        self.pool.append(element)

    def remove_element(self, element: Element):
        """从池中移除元素"""
        self.pool.remove(element)

    def clear_pool(self):
        """清空元素池"""
        self.pool.clear()

    def group_elements(
        self,
        mode: str = "equal",
        group_num: int = 2,
        group_size: int = None,
        randomize: bool = True,
    ):
        """
        分组方法
        :param mode: 分组模式，可选"equal"(均等分组)或"size"(按量分组)
        :param group_num: 分组数量，默认2组
        :param group_size: 每组元素数量，仅在按量分组模式下有效
        :param randomize: 是否随机分组，默认为True
        :return: 分组结果列表
        """
        if not self.pool:
            return []

        # 新增：如果需要随机分组，先打乱元素顺序
        working_pool = self.pool.copy()
        if randomize:
            random.shuffle(working_pool)

        if mode == "equal":
            # 均等分组
            per_group = len(working_pool) // group_num
            remainder = len(working_pool) % group_num
            groups = []
            start = 0
            for i in range(group_num):
                end = start + per_group + (1 if i < remainder else 0)
                groups.append(working_pool[start:end])
                start = end
            return groups

        elif mode == "size" and group_size:
            # 按量分组
            if group_size <= 0:
                raise ValueError(
                    "The number of elements per group must be greater than 0"
                )
            groups = []
            for i in range(0, len(working_pool), group_size):
                if len(groups) >= group_num:  # 达到指定组数后停止
                    break
                groups.append(working_pool[i : i + group_size])
            return groups

        else:
            raise ValueError(
                "Invalid grouping mode or parameter, grouping mode must be 'equal' or 'size'"
            )


class HotElementsCache:
    def __init__(self, max_size: int = 10):
        """初始化热点元素缓存
        :param max_size: 缓存最大容量，默认为10
        """
        if max_size <= 0:
            raise ValueError("max_size must be greater than 0")
        self.max_size = max_size
        self.cache = OrderedDict()  # 使用有序字典维护LRU顺序

    def add_element(self, element: Element):
        """添加或更新元素
        :param element: 要添加的元素
        """
        if not isinstance(element, Element):
            raise TypeError("Only Element objects can be added")

        if element in self.cache:
            # 如果元素已存在，先删除再重新插入到最前面
            del self.cache[element]
        else:
            # 如果缓存已满，移除最久未使用的元素（最后面的元素）
            if len(self.cache) >= self.max_size:
                self.cache.popitem(last=True)

        # 将元素插入到最前面
        self.cache[element] = None
        self.cache.move_to_end(element, last=False)

    def get_hot_elements(self) -> List[Element]:
        """获取最近使用的元素列表
        :return: 按最近使用顺序排列的元素列表
        """
        return list(self.cache.keys())

    def clear(self):
        """清空缓存"""
        self.cache.clear()
