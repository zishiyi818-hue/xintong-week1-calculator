"""calculator.py 的自动化测试。

运行：
    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import io
import sys
import unittest
from decimal import Decimal
from pathlib import Path

# 允许直接运行本文件，也允许从项目根目录运行 unittest discover。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import calculator  # noqa: E402


class CalculateTests(unittest.TestCase):
    """四则运算核心逻辑。"""

    def test_add_integers(self) -> None:
        self.assertEqual(calculator.calculate("12", "+", "30"), Decimal("42"))

    def test_subtract_integers(self) -> None:
        self.assertEqual(calculator.calculate("12", "-", "30"), Decimal("-18"))

    def test_multiply_integers(self) -> None:
        self.assertEqual(calculator.calculate("12", "*", "30"), Decimal("360"))

    def test_divide_exact(self) -> None:
        self.assertEqual(calculator.calculate("9", "/", "2"), Decimal("4.5"))

    def test_negative_numbers(self) -> None:
        self.assertEqual(calculator.calculate("-8", "*", "-2.5"), Decimal("20"))

    def test_decimal_has_no_binary_float_error(self) -> None:
        self.assertEqual(calculator.calculate("0.1", "+", "0.2"), Decimal("0.3"))

    def test_scientific_notation(self) -> None:
        self.assertEqual(calculator.calculate("1e3", "+", "2e2"), Decimal("1200"))

    def test_fullwidth_operator(self) -> None:
        self.assertEqual(calculator.calculate("8", "×", "7"), Decimal("56"))

    def test_fullwidth_digits(self) -> None:
        self.assertEqual(calculator.calculate("１２", "＋", "３"), Decimal("15"))

    def test_division_by_zero(self) -> None:
        with self.assertRaises(calculator.DivisionByZeroError):
            calculator.calculate("1", "/", "0")

    def test_zero_divided_by_zero(self) -> None:
        with self.assertRaises(calculator.DivisionByZeroError):
            calculator.calculate("0", "/", "0")

    def test_invalid_operator(self) -> None:
        with self.assertRaises(calculator.InvalidOperatorError):
            calculator.calculate("1", "%", "2")

    def test_invalid_number(self) -> None:
        with self.assertRaises(calculator.InvalidNumberError):
            calculator.calculate("abc", "+", "2")

    def test_empty_number(self) -> None:
        with self.assertRaises(calculator.InvalidNumberError):
            calculator.parse_number("   ")

    def test_nan_is_rejected(self) -> None:
        with self.assertRaises(calculator.InvalidNumberError):
            calculator.parse_number("NaN")

    def test_infinity_is_rejected(self) -> None:
        with self.assertRaises(calculator.InvalidNumberError):
            calculator.parse_number("Infinity")

    def test_boolean_is_rejected(self) -> None:
        with self.assertRaises(calculator.InvalidNumberError):
            calculator.calculate(True, "+", 1)


class FormatResultTests(unittest.TestCase):
    """结果格式化。"""

    def test_trim_trailing_zeros(self) -> None:
        self.assertEqual(calculator.format_result(Decimal("12.5000")), "12.5")

    def test_zero(self) -> None:
        self.assertEqual(calculator.format_result(Decimal("-0")), "0")

    def test_tiny_nonzero_value(self) -> None:
        self.assertEqual(
            calculator.format_result(Decimal("0.00000000005")),
            "0.00000000005",
        )

    def test_large_integer(self) -> None:
        self.assertEqual(
            calculator.format_result(Decimal("1E+20")),
            "100000000000000000000",
        )

    def test_repeating_decimal_is_trimmed_to_ten_places(self) -> None:
        result = calculator.calculate("1", "/", "3")
        self.assertEqual(calculator.format_result(result), "0.3333333333")


class ReplTests(unittest.TestCase):
    """模拟完整交互会话。"""

    @staticmethod
    def run_session(text: str) -> tuple[int, str]:
        output = io.StringIO()
        code = calculator.run_repl(io.StringIO(text), output)
        return code, output.getvalue()

    def test_continuous_calculation(self) -> None:
        code, output = self.run_session("12\n+\n30\n5\n*\n6\nq\n")
        self.assertEqual(code, 0)
        self.assertIn("结果：12 + 30 = 42", output)
        self.assertIn("结果：5 * 6 = 30", output)
        self.assertIn("已退出计算器", output)

    def test_division_by_zero_then_continue(self) -> None:
        _, output = self.run_session("9\n/\n0\n6\n-\n2\nq\n")
        self.assertIn("除数不能为 0", output)
        self.assertIn("结果：6 - 2 = 4", output)

    def test_invalid_number_then_retry(self) -> None:
        _, output = self.run_session("abc\n12\n+\n30\nq\n")
        self.assertIn("无法识别数字", output)
        self.assertIn("结果：12 + 30 = 42", output)

    def test_invalid_operator_then_retry(self) -> None:
        _, output = self.run_session("12\n%\n*\n2\nq\n")
        self.assertIn("不支持的运算符", output)
        self.assertIn("结果：12 * 2 = 24", output)

    def test_quit_immediately(self) -> None:
        code, output = self.run_session("q\n")
        self.assertEqual(code, 0)
        self.assertIn("已退出计算器", output)

    def test_quit_word_is_case_insensitive(self) -> None:
        _, output = self.run_session("EXIT\n")
        self.assertIn("已退出计算器", output)

    def test_decimal_expression_prints_clean_result(self) -> None:
        _, output = self.run_session("0.1\n+\n0.2\nq\n")
        self.assertIn("结果：0.1 + 0.2 = 0.3", output)


if __name__ == "__main__":
    unittest.main()
