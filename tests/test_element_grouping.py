import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import unittest

from element_group import Element, Group
from element_group import HotElementsCache


class TestElement(unittest.TestCase):
    def test_element_creation(self):
        """测试Element类的创建"""
        elem = Element("test")
        self.assertEqual(elem.value, "test")
        self.assertEqual(str(elem), "Element(test)")

    def test_invalid_element_creation(self):
        """测试无效的Element创建"""
        with self.assertRaises(ValueError):
            Element(123)  # 非字符串输入


class TestGroup(unittest.TestCase):
    def setUp(self):
        """测试前置准备"""
        self.elements = [Element(str(i)) for i in range(10)]
        self.group = Group(self.elements)

    def test_add_element(self):
        """测试添加元素"""
        new_elem = Element("new")
        self.group.add_element(new_elem)
        self.assertIn(new_elem, self.group.pool)

    def test_remove_element(self):
        """测试移除元素"""
        elem_to_remove = self.elements[0]
        self.group.remove_element(elem_to_remove)
        self.assertNotIn(elem_to_remove, self.group.pool)

    def test_clear_pool(self):
        """测试清空元素池"""
        self.group.clear_pool()
        self.assertEqual(len(self.group.pool), 0)

    def test_equal_grouping(self):
        """测试均等分组"""
        groups = self.group.group_elements(mode="equal", group_num=3)
        self.assertEqual(len(groups), 3)
        self.assertEqual(len(groups[0]), 4)  # 10个元素分3组，第一组4个
        self.assertEqual(len(groups[1]), 3)  # 第二组3个
        self.assertEqual(len(groups[2]), 3)  # 第三组3个

    def test_size_grouping(self):
        """测试按量分组"""
        groups = self.group.group_elements(mode="size", group_size=4, group_num=3)
        self.assertEqual(len(groups), 3)
        self.assertEqual(len(groups[0]), 4)
        self.assertEqual(len(groups[1]), 4)
        self.assertEqual(len(groups[2]), 2)

    def test_invalid_grouping(self):
        """测试无效分组参数"""
        with self.assertRaises(ValueError):
            self.group.group_elements(mode="invalid_mode")

        with self.assertRaises(ValueError):
            self.group.group_elements(mode="size", group_size=0)


class TestHotElementsCache(unittest.TestCase):
    def setUp(self):
        """测试前置准备"""
        self.cache = HotElementsCache(max_size=3)
        self.elements = [Element(f"元素{i}") for i in range(5)]

    def test_add_element(self):
        """测试添加元素"""
        # 添加新元素
        self.cache.add_element(self.elements[0])
        self.assertIn(self.elements[0], self.cache.get_hot_elements())

        # 添加重复元素
        self.cache.add_element(self.elements[0])
        self.assertEqual(len(self.cache.get_hot_elements()), 1)

    def test_lru_eviction(self):
        """测试LRU淘汰机制"""
        # 添加3个元素
        for i in range(3):
            self.cache.add_element(self.elements[i])

        # 添加第4个元素，应该淘汰最早的元素
        self.cache.add_element(self.elements[3])
        self.assertNotIn(self.elements[0], self.cache.get_hot_elements())
        self.assertIn(self.elements[3], self.cache.get_hot_elements())

        # 访问第二个元素，使其成为最新
        self.cache.add_element(self.elements[1])

        # 添加第5个元素，应该淘汰第三个元素
        self.cache.add_element(self.elements[4])
        self.assertNotIn(self.elements[2], self.cache.get_hot_elements())
        self.assertIn(self.elements[1], self.cache.get_hot_elements())

    def test_get_hot_elements(self):
        """测试获取热点元素"""
        self.cache.clear()
        # 添加元素
        for i in range(3):
            self.cache.add_element(self.elements[i])

        # 获取热点元素
        hot_elements = self.cache.get_hot_elements()
        self.assertEqual(len(hot_elements), 3)
        self.assertEqual(hot_elements[0].value, "元素2")  # 最新添加的元素在最前面
        self.assertEqual(hot_elements[2].value, "元素0")  # 最早添加的元素在最后面

    def test_clear(self):
        """测试清空缓存"""
        # 添加元素
        for i in range(3):
            self.cache.add_element(self.elements[i])

        # 清空缓存
        self.cache.clear()
        self.assertEqual(len(self.cache.get_hot_elements()), 0)

    def test_max_size(self):
        """测试最大容量"""
        # 添加超过最大容量的元素
        for i in range(5):
            self.cache.add_element(self.elements[i])

        # 验证只保留最新的3个元素
        hot_elements = self.cache.get_hot_elements()
        self.assertEqual(len(hot_elements), 3)
        self.assertIn(self.elements[4], hot_elements)
        self.assertIn(self.elements[3], hot_elements)
        self.assertIn(self.elements[2], hot_elements)


if __name__ == "__main__":
    unittest.main()
