from fractions import Fraction
from itertools import combinations,product

NODES = ("A","B","C","D")
M = 2

# 明确指定部分完整名单的概率
DECLARED_PROBABILITIES = {
    frozenset(("A", "B")): Fraction(1, 2),
    frozenset(("A", "C")): Fraction(1, 4),
    frozenset(("C", "D")): Fraction(1, 4),
}

def enumerate_legal_lists():
    """列出所有恰好包含 M 家店的合法名单。"""
    rows = []

    for selected in combinations(NODES, M):
        treated = frozenset(selected)
        probability = DECLARED_PROBABILITIES.get(treated, Fraction(0))
        rows.append((treated, probability))

    return rows

def print_probability_table(rows):
    print("所有合法试点名单及概率：")

    total = Fraction(0)

    for treated, probability in rows:
        label = "".join(sorted(treated))
        print(f"{label}: {probability}")
        total += probability

    print(f"概率总和: {total}")

    assert total == 1
    assert all(len(treated) == M for treated, _ in rows)

def check_impossible_assignments():
    """检查不满足恰好选 M 家的完整二元处理向量。"""
    print("\n不可能的处理向量：")

    for bits in product((0, 1), repeat=len(NODES)):
        treated = frozenset(
            node for node, bit in zip(NODES, bits) if bit == 1
        )

        if len(treated) != M:
            probability = Fraction(0)
            print(
                f"{bits} -> 处理店数={len(treated)}, "
                f"概率={probability}"
            )
def print_marginal_probabilities(rows):
    """计算每家店被选中的概率。"""
    print("\n每家店被选中的概率：")

    for node in NODES:
        probability = sum(
            (
                p
                for treated, p in rows
                if node in treated
            ),
            Fraction(0),
        )
        print(f"P({node} 被选中) = {probability}")

if __name__ == "__main__":
    rows = enumerate_legal_lists()
    print_probability_table(rows)
    check_impossible_assignments()
    print_marginal_probabilities(rows)