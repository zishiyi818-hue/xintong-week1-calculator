"""信创软件小组第 1 周任务：命令行四则运算计算器。

R5 底线：
    - 支持加、减、乘、除；
    - 除数为 0 时给出明确提示。

R6 进阶：
    - 捕获非法数字、非法运算符；
    - 支持循环连续计算；
    - 使用 Decimal 避免二进制浮点误差；
    - 核心逻辑与输入输出分离，便于自动化测试。
"""

from __future__ import annotations

import sys
import unicodedata
from decimal import Decimal, InvalidOperation, localcontext
from typing import TextIO

# 支持的运算符。键是内部标准写法，值是显示名称。
OPERATORS = {
    "+": "加法",
    "-": "减法",
    "*": "乘法",
    "/": "除法",
}

# 将中文输入法下常见的全角符号统一成半角符号。
OPERATOR_ALIASES = {
    "＋": "+",
    "－": "-",
    "＊": "*",
    "／": "/",
    "×": "*",
    "÷": "/",
}

QUIT_WORDS = frozenset({"q", "quit", "exit", "退出", "结束"})

BANNER = """==============================================
        信创软件小组 · 第 1 周计算器
        支持 + - * /，输入 q 退出
==============================================
"""


class CalculatorError(Exception):
    """计算器业务异常基类。"""


class InvalidNumberError(CalculatorError):
    """输入内容无法转换为有限数字。"""

    def __init__(self, raw: str) -> None:
        self.raw = raw
        super().__init__(f"无法识别数字“{raw}”")


class InvalidOperatorError(CalculatorError):
    """输入了不支持的运算符。"""

    def __init__(self, raw: str) -> None:
        self.raw = raw
        super().__init__(f"不支持的运算符“{raw}”，仅支持 + - * /")


class DivisionByZeroError(CalculatorError):
    """除数为 0。"""

    def __init__(self) -> None:
        super().__init__("除数不能为 0")


class QuitRequested(Exception):
    """内部信号：用户要求退出，不对外暴露。"""


def parse_number(raw: str) -> Decimal:
    """把用户输入解析为有限 Decimal。

    Args:
        raw: 用户输入的原始文本，可以包含首尾空格或全角数字。

    Raises:
        InvalidNumberError: 输入为空、不是数字，或为 NaN / Infinity。
    """
    text = unicodedata.normalize("NFKC", str(raw)).strip()
    if not text:
        raise InvalidNumberError(raw)

    try:
        value = Decimal(text)
    except (InvalidOperation, ValueError):
        raise InvalidNumberError(raw) from None

    if not value.is_finite():
        raise InvalidNumberError(raw)
    return value


def normalize_operator(raw: str) -> str:
    """统一全角符号，并返回标准运算符写法。"""
    text = unicodedata.normalize("NFKC", str(raw)).strip()
    return OPERATOR_ALIASES.get(text, text)


def validate_operator(raw: str) -> str:
    """校验运算符，返回标准写法。

    Raises:
        InvalidOperatorError: 运算符不在 + - * / 中。
    """
    operator = normalize_operator(raw)
    if operator not in OPERATORS:
        raise InvalidOperatorError(raw)
    return operator


def _as_decimal(value: Decimal | int | float | str) -> Decimal:
    """把 calculate 的入参统一转换为 Decimal。"""
    if isinstance(value, bool):
        raise InvalidNumberError(str(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise InvalidNumberError(str(value))
        return value
    if isinstance(value, (int, float)):
        return parse_number(str(value))
    if isinstance(value, str):
        return parse_number(value)
    raise InvalidNumberError(str(value))


def calculate(
    left: Decimal | int | float | str,
    operator: str,
    right: Decimal | int | float | str,
) -> Decimal:
    """执行一次四则运算。

    Examples:
        >>> calculate("0.1", "+", "0.2")
        Decimal('0.3')

    Raises:
        InvalidNumberError: 任一操作数非法。
        InvalidOperatorError: 运算符非法。
        DivisionByZeroError: 除法运算的除数为 0。
    """
    left_value = _as_decimal(left)
    right_value = _as_decimal(right)
    op = validate_operator(operator)

    if op == "/" and right_value == 0:
        raise DivisionByZeroError()

    # 28 位有效数字足够日常计算，同时避免除法结果无限长。
    with localcontext() as context:
        context.prec = 28
        if op == "+":
            return left_value + right_value
        if op == "-":
            return left_value - right_value
        if op == "*":
            return left_value * right_value
        return left_value / right_value


def format_result(value: Decimal) -> str:
    """把 Decimal 格式化成适合终端显示的字符串。

    - 去掉小数末尾多余的 0；
    - 最多保留 10 位小数；
    - 极小但非 0 的数使用普通小数形式，避免显示成 0。
    """
    if value == 0:
        return "0"

    if abs(value) < Decimal("0.0000000001"):
        text = format(value.normalize(), "f")
    else:
        text = f"{value:.10f}"

    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _read_line(prompt: str, stdin: TextIO, stdout: TextIO) -> str:
    """显示提示并读取一行；空输入（EOF）转为 EOFError。"""
    stdout.write(prompt)
    stdout.flush()
    line = stdin.readline()
    if line == "":
        raise EOFError
    text = line.strip()
    if text.casefold() in QUIT_WORDS:
        raise QuitRequested
    return text


def _read_number(prompt: str, stdin: TextIO, stdout: TextIO) -> Decimal:
    """反复读取，直到得到合法数字或用户退出。"""
    while True:
        raw = _read_line(prompt, stdin, stdout)
        try:
            return parse_number(raw)
        except InvalidNumberError as exc:
            stdout.write(f"  [输入错误] {exc}，请重新输入。\n")


def _read_operator(prompt: str, stdin: TextIO, stdout: TextIO) -> str:
    """反复读取，直到得到合法运算符或用户退出。"""
    while True:
        raw = _read_line(prompt, stdin, stdout)
        try:
            return validate_operator(raw)
        except InvalidOperatorError as exc:
            stdout.write(f"  [运算符错误] {exc}，请重新输入。\n")


def run_repl(stdin: TextIO | None = None, stdout: TextIO | None = None) -> int:
    """运行交互式计算器主循环。

    参数允许注入文本流，单元测试因此可以模拟完整会话。
    """
    stdin = stdin if stdin is not None else sys.stdin
    stdout = stdout if stdout is not None else sys.stdout

    stdout.write(BANNER)

    while True:
        try:
            left = _read_number("请输入第 1 个数字（q 退出）：", stdin, stdout)
            operator = _read_operator(
                "请输入运算符（+ - * /，q 退出）：", stdin, stdout
            )
            right = _read_number("请输入第 2 个数字（q 退出）：", stdin, stdout)
        except QuitRequested:
            break

        try:
            result = calculate(left, operator, right)
        except CalculatorError as exc:
            stdout.write(f"  [计算失败] {exc}\n")
        else:
            stdout.write(
                f"结果：{format_result(left)} {operator} "
                f"{format_result(right)} = {format_result(result)}\n"
            )
        stdout.write("-" * 46 + "\n")

    stdout.write("已退出计算器，再见！\n")
    stdout.flush()
    return 0


def main() -> int:
    """程序入口，处理 Ctrl+C 与输入结束。"""
    try:
        return run_repl()
    except (EOFError, KeyboardInterrupt):
        print("\n输入已结束，计算器退出。")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
