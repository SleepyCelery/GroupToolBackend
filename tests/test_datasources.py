import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import unittest
from unittest.mock import patch, Mock
from datasources import (
    ElementSource,
    LolHeroSource,
    get_all_sources,
    get_source_by_display_name,
    get_elements_from_source,
)
from element_group import Element
from requests import RequestException


class TestElementSource(unittest.TestCase):
    def test_abstract_method(self):
        """测试ElementSource抽象类"""
        with self.assertRaises(TypeError):
            ElementSource()  # 不能实例化抽象类


class TestLolHeroSource(unittest.TestCase):
    @patch("datasources.requests.get")
    def test_get_elements_success(self, mock_get):
        """测试成功获取英雄数据"""
        # 模拟API响应
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "Aatrox": {"name": "亚托克斯", "title": "暗裔剑魔"},
                "Ahri": {"name": "阿狸", "title": "九尾妖狐"},
            }
        }
        mock_get.return_value = mock_response

        elements = LolHeroSource.get_elements()
        self.assertEqual(len(elements), 2)
        self.assertIsInstance(elements[0], Element)
        self.assertEqual(elements[0].value, "亚托克斯 暗裔剑魔")
        self.assertEqual(elements[1].value, "阿狸 九尾妖狐")

    @patch("datasources.requests.get")
    def test_get_elements_failure(self, mock_get):
        """测试获取英雄数据失败"""
        # 模拟API请求失败
        mock_get.side_effect = RequestException("API请求失败")

        # 调用方法
        elements = LolHeroSource.get_elements()

        # 验证返回空列表
        self.assertEqual(len(elements), 0)
        self.assertIsInstance(elements, list)


class TestDataSourceFunctions(unittest.TestCase):
    def test_get_all_sources(self):
        """测试获取所有数据源"""
        sources = get_all_sources()
        self.assertIn("英雄联盟英雄数据", sources)
        self.assertEqual(sources["英雄联盟英雄数据"], LolHeroSource)

    def test_get_source_by_display_name(self):
        """测试通过显示名称获取数据源"""
        source = get_source_by_display_name("英雄联盟英雄数据")
        self.assertEqual(source, LolHeroSource)

        source = get_source_by_display_name("不存在的数据源")
        self.assertIsNone(source)

    @patch("datasources.get_source_by_display_name")
    def test_get_elements_from_source(self, mock_get_source):
        """测试从数据源获取元素"""
        # 模拟数据源
        mock_source = Mock()
        mock_source.get_elements.return_value = [Element("测试元素")]
        mock_get_source.return_value = mock_source

        elements = get_elements_from_source("测试数据源")
        self.assertEqual(len(elements), 1)
        self.assertEqual(elements[0].value, "测试元素")

        # 测试不存在的数据源
        mock_get_source.return_value = None
        elements = get_elements_from_source("不存在的数据源")
        self.assertEqual(len(elements), 0)


if __name__ == "__main__":
    unittest.main()
