"""信创软件小组第 1 周任务：基础命令行计算器（R5）。

支持加、减、乘、除，并在除数为 0 时给出提示。
"""


def calculate(left: float, operator: str, right: float) -> float:
    """根据运算符完成一次四则运算。"""
    if operator == "+":
        return left + right
    if operator == "-":
        return left - right
    if operator == "*":
        return left * right
    if operator == "/":
        if right == 0:
            raise ZeroDivisionError("除数不能为 0")
        return left / right
    raise ValueError(f"不支持的运算符：{operator}")


def main() -> None:
    print("=" * 44)
    print("        信创软件小组 · 第 1 周计算器")
    print("        支持 + - * /，输入 q 退出")
    print("=" * 44)

    while True:
        left_text = input("请输入第 1 个数字：").strip()
        if left_text.lower() == "q":
            break
        operator = input("请输入运算符（+ - * /）：").strip()
        if operator.lower() == "q":
            break
        right_text = input("请输入第 2 个数字：").strip()
        if right_text.lower() == "q":
            break

        left = float(left_text)
        right = float(right_text)
        result = calculate(left, operator, right)
        print(f"结果：{left:g} {operator} {right:g} = {result:g}")
        print("-" * 44)

    print("已退出计算器，再见！")


if __name__ == "__main__":
    main()
