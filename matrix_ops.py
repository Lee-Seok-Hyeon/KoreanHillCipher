"""정수·모듈러 환경을 위한 행렬 연산 (numpy 비의존).

numpy.linalg.inv() 는 부동소수점 역행렬을 돌려주므로 정수·mod 환경에서는 그대로
쓸 수 없다. 대신 다음을 직접 구현한다.

    1) 확장 유클리드 알고리즘 -> 정수의 모듈러 곱셈 역원
    2) 행렬식 + 수반행렬(adjugate) -> 모듈러 역행렬
           K^{-1}  ≡  det(K)^{-1} · adj(K)   (mod n)

여인수(cofactor) 전개 기반이라 작은 행렬(2~4차)에 적합하며, 수업에서 배운
'행렬식·수반행렬·역행렬' 개념과 코드가 1:1로 대응된다.
"""

from typing import List, Tuple

Matrix = List[List[int]]
Vector = List[int]


def egcd(a: int, b: int) -> Tuple[int, int, int]:
    """확장 유클리드. (g, x, y) 반환, ax + by = g = gcd(a, b)."""
    if b == 0:
        return a, 1, 0
    g, x1, y1 = egcd(b, a % b)
    return g, y1, x1 - (a // b) * y1


def mod_inverse(a: int, n: int) -> int:
    """a 의 mod n 곱셈 역원. gcd(a, n) != 1 이면 ValueError."""
    a %= n
    g, x, _ = egcd(a, n)
    if g != 1:
        raise ValueError(f"{a} 는 mod {n} 에서 역원이 없습니다 (gcd={g}).")
    return x % n


def minor(M: Matrix, r: int, c: int) -> Matrix:
    """r행, c열을 제거한 소행렬."""
    return [[M[i][j] for j in range(len(M)) if j != c]
            for i in range(len(M)) if i != r]


def determinant(M: Matrix) -> int:
    """정수 행렬식 (여인수 전개)."""
    n = len(M)
    if n == 1:
        return M[0][0]
    if n == 2:
        return M[0][0] * M[1][1] - M[0][1] * M[1][0]
    det = 0
    for c in range(n):
        det += ((-1) ** c) * M[0][c] * determinant(minor(M, 0, c))
    return det


def adjugate(M: Matrix) -> Matrix:
    """수반행렬 = 여인수행렬의 전치."""
    n = len(M)
    if n == 1:
        return [[1]]
    cof = [[((-1) ** (i + j)) * determinant(minor(M, i, j)) for j in range(n)]
           for i in range(n)]
    return [[cof[j][i] for j in range(n)] for i in range(n)]   # 전치


def mat_vec_mod(M: Matrix, v: Vector, n: int) -> Vector:
    """행렬·벡터 곱 (mod n).  result = M · v  (mod n)."""
    size = len(M)
    return [sum(M[i][j] * v[j] for j in range(size)) % n for i in range(size)]


def matrix_mod_inverse(K: Matrix, n: int) -> Matrix:
    """K 의 mod n 역행렬.   K^{-1} = det(K)^{-1} · adj(K)  (mod n).

    gcd(det(K), n) != 1 이면 (역원이 없으면) ValueError 가 전파된다.
    """
    d = determinant(K) % n
    d_inv = mod_inverse(d, n)            # gcd(det, n) != 1 이면 여기서 예외
    adj = adjugate(K)
    size = len(K)
    return [[(d_inv * adj[i][j]) % n for j in range(size)] for i in range(size)]
