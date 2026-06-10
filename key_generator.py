"""유효한 키 행렬 자동 생성.

키 행렬 K 가 복호화 가능하려면 mod n 역행렬이 존재해야 하고,
이는  gcd(det(K), n) == 1  과 동치이다.

** 옛 설계(mod 29, 소수)와의 핵심 차이 **
    이 프로젝트의 n = 11172 는 소수가 아니다.
        11172 = 2^2 · 3 · 7^2 · 19
    따라서 det(K) 가 2, 3, 7, 19 중 어느 하나의 배수여도 역행렬이 없다.
    즉 "det(K) != 0 인가"만 확인하면 안 되고, 반드시 "gcd(det, n) == 1"을
    확인해야 한다.  (소수 모듈러였다면 det != 0 검증으로 충분했다.)
"""

import random
from math import gcd

from matrix_ops import determinant, Matrix

# 참고: 11172 의 소인수 (검증/설명용)
MODULUS_PRIME_FACTORS = (2, 3, 7, 19)


def is_valid_key(K: Matrix, n: int) -> bool:
    """K 가 mod n 에서 역행렬을 갖는가 (gcd(det, n) == 1)."""
    return gcd(determinant(K) % n, n) == 1


def generate_key_matrix(size: int, n: int, max_tries: int = 100_000) -> Matrix:
    """gcd(det(K), n) == 1 을 만족하는 size×size 키 행렬을 무작위 생성."""
    for _ in range(max_tries):
        K = [[random.randrange(n) for _ in range(size)] for _ in range(size)]
        if gcd(determinant(K) % n, n) == 1:
            return K
    raise RuntimeError(f"{max_tries}회 시도에도 유효한 키 행렬 생성 실패")
