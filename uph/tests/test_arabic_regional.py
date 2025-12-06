import frappe
from frappe.tests.utils import FrappeTestCase
from uph.regional.arabic import money_in_words, in_words, get_number_format_info

class TestArabicRegional(FrappeTestCase):
    def setUp(self):
        self.original_lang = frappe.local.lang

    def tearDown(self):
        frappe.local.lang = self.original_lang

    def test_money_in_words_english(self):
        frappe.local.lang = "en"
        result = money_in_words(1234.56, "USD")
        self.assertIn("only", result.lower())

    def test_money_in_words_arabic(self):
        frappe.local.lang = "ar"
        result = money_in_words(1000.00, "YER")
        self.assertIsInstance(result, str)

    def test_money_in_words_zero(self):
        frappe.local.lang = "en"
        result = money_in_words(0, "USD")
        self.assertIn("Zero", result)

    def test_money_in_words_negative(self):
        self.assertEqual(money_in_words(-100, "USD"), "")

    def test_in_words_english(self):
        self.assertIn("hundred", in_words(123, lang="en").lower())

    def test_get_number_format_info(self):
        self.assertEqual(get_number_format_info("#,###.##"), (".", ",", 2))

    def test_get_number_format_info_default(self):
        self.assertEqual(get_number_format_info("unknown"), (".", ",", 2))
