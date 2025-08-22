import unittest
from worldalphabets import get_index_data, get_language

class TestHelpers(unittest.TestCase):
    def test_get_index_data(self):
        data = get_index_data()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_get_language(self):
        lang_info = get_language('en')
        self.assertIsInstance(lang_info, dict)
        self.assertEqual(lang_info['language'], 'en')
        self.assertEqual(lang_info['language-name'], 'English')

    def test_get_language_invalid(self):
        lang_info = get_language('invalid-code')
        self.assertIsNone(lang_info)

if __name__ == '__main__':
    unittest.main()
