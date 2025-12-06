import frappe
import math
from frappe.utils import flt, get_defaults, cint

def get_number_format_info(format: str) -> tuple[str, str, int]:
	return number_format_info.get(format) or (".", ",", 2)


number_format_info = {
	"#,###.##": (".", ",", 2),
	"#.###,##": (",", ".", 2),
	"# ###.##": (".", " ", 2),
	"# ###,##": (",", " ", 2),
	"#'###.##": (".", "'", 2),
	"#, ###.##": (".", ", ", 2),
	"#,##,###.##": (".", ",", 2),
	"#,###.###": (".", ",", 3),
	"#.###": ("", ".", 0),
	"#,###": ("", ",", 0),
	"#.########": (".", "", 8),
}
from frappe.utils import get_defaults
from num2words import num2words

def money_in_words(
	number: str | float | int,
	main_currency: str | None = None,
	fraction_currency: str | None = None,
):
	"""
	Returns string in words with currency and fraction currency.
	Handles Arabic formatting where the currency is at the end.
	"""
	_ = frappe._

	try:
		number = float(number)
	except ValueError:
		return ""

	number = flt(number)
	if number < 0:
		return ""

	# Get default currency
	d = get_defaults()
	if not main_currency:
		main_currency = d.get("currency", "INR")
	if not fraction_currency:
		fraction_currency = frappe.db.get_value("Currency", main_currency, "fraction", cache=True) or _("Cent")

	# Get number format
	number_format = (
		frappe.db.get_value("Currency", main_currency, "number_format", cache=True)
		or frappe.db.get_default("number_format")
		or "#,###.##"
	)
	fraction_length = get_number_format_info(number_format)[2]

	# Convert number to string with the correct decimal places
	n = f"%.{fraction_length}f" % number
	numbers = n.split(".")
	main, fraction = numbers if len(numbers) > 1 else [n, "00"]

	if len(fraction) < fraction_length:
		zeros = "0" * (fraction_length - len(fraction))
		fraction += zeros

	in_million = number_format != "#,##,###.##"

	# Detect Arabic language
	is_arabic = frappe.local.lang.startswith("ar")

	# Convert numbers to words
	main_words = in_words(main, in_million, lang="ar" if is_arabic else "en").title()
	fraction_words = in_words(fraction, in_million, lang="ar" if is_arabic else "en").title()

	# Arabic Formatting: Place currency at the end
	if is_arabic:
		if main == "0" and fraction in ["00", "000"]:
			out = f"صفر {main_currency}"
		elif main == "0":
			out = f"{fraction_words} {_(fraction_currency,context='Currency')}"
	
		else:
			out = f"{main_words} {_(main_currency, context='Currency') }"
			if cint(fraction):
				out += f" {_('And')}{fraction_words} {_(fraction_currency,context='Currency')}"
	else:
		# Default English formatting
		if main == "0" and fraction in ["00", "000"]:
			out = _(main_currency, context="Currency") + " " + _("Zero")
		elif main == "0":
			out = f"{fraction_words} {fraction_currency}"
		else:
			out = _(main_currency, context="Currency") + " " + main_words
			if cint(fraction):
				out += " " + _("and") + " " + fraction_words + " " + fraction_currency

	return out + " " + _("only.")

def in_words(integer: int, in_million=True, lang="en") -> str:
	"""
	Returns string in words for the given integer, with Arabic support.
	"""
	try:
		ret = num2words(integer, lang=lang)
	except (NotImplementedError, OverflowError):
		ret = num2words(integer, lang="en")  # Fallback to English
	return ret.replace("-", " ")


def test_arabic():
    amount=10000.00
    currency="YER"
    frappe.response["charset"] = "utf-8"

    frappe.local.lang = "ar"
    return money_in_words(amount,currency)