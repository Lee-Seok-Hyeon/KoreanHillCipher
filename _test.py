"""round-trip 및 엣지케이스 검증."""
from math import gcd
import random

from hangul_utils import MODULUS
from matrix_ops import determinant, matrix_mod_inverse, mat_vec_mod
from key_generator import generate_key_matrix, is_valid_key
from cipher import encrypt, decrypt

random.seed(42)
n = MODULUS

def check_inverse(K):
    """K · K^{-1} ≡ I (mod n) 확인."""
    Kinv = matrix_mod_inverse(K, n)
    size = len(K)
    for col in range(size):
        e = [1 if i == col else 0 for i in range(size)]
        # K · (Kinv 의 col열) 이 e 와 같은지
        kinv_col = [Kinv[i][col] for i in range(size)]
        prod = mat_vec_mod(K, kinv_col, n)
        if prod != e:
            return False
    return True

cases = [
    "한",                       # 한 글자
    "선형대수",                  # 정확히 4 (size3 -> 패딩)
    "행렬과모듈러연산",           # 길이 8
    "안녕하세요, 반갑습니다!",     # 문장부호+공백 통과
    "한글 Hill cipher 데모 2026", # 영문/숫자/공백 혼합
    "가나다라마바사아자차",        # 종성 없는 글자들
    "",                         # 빈 문자열
    "ABC 123 !!!",              # 한글 0개
    "가힣",                      # 패딩 문자 '힣'으로 끝남 (옛 설계의 한계 케이스)
    "안녕힣",                    # '힣'으로 끝남
    "힣",                        # '힣' 한 글자
    "테스트입니다 힣",            # 비한글 뒤 '힣'
]

print("== 키 검증 (gcd(det, n)=1) & 역행렬 정합성 ==")
for size in (2, 3):
    K = generate_key_matrix(size, n)
    d = determinant(K) % n
    assert is_valid_key(K, n), "유효성 검증 실패"
    assert gcd(d, n) == 1
    assert check_inverse(K), f"size={size} 역행렬 불일치"
    print(f"  size={size}: det={d}, gcd={gcd(d,n)}, K·K^-1=I  OK")

print("\n== 왕복 테스트 (size=2, 3 각각) ==")
all_ok = True
for size in (2, 3):
    K = generate_key_matrix(size, n)
    for t in cases:
        c = encrypt(t, K)
        r = decrypt(c, K)
        ok = (r == t)
        all_ok &= ok
        flag = "OK " if ok else "FAIL"
        print(f"  [{flag}] size={size}  {t!r}  ->  {c!r}  ->  {r!r}")

print("\n== 잘못된 키(gcd!=1) 복호화 시 예외 발생 확인 ==")
# det 가 2의 배수인 짝수 det 행렬 만들기 (gcd(det,n) != 1 유도)
bad = [[2, 0, 0], [0, 1, 0], [0, 0, 1]]   # det = 2, gcd(2, 11172)=2
try:
    decrypt("가나다", bad)
    print("  FAIL: 예외가 발생하지 않음")
    all_ok = False
except ValueError as e:
    print(f"  OK: 기대대로 예외 -> {e}")

print("\n== 무손실 검증: '힣'로 끝나는 평문도 정확히 복원 ==")
K = generate_key_matrix(3, n)
for t in ("가힣", "안녕힣", "힣", "끝이힣"):
    r = decrypt(encrypt(t, K), K)
    status = "OK" if r == t else "FAIL"
    all_ok &= (r == t)
    print(f"  [{status}] {t!r} -> 복호화 {r!r}")

print("\n전체 핵심 왕복:", "PASS" if all_ok else "FAIL")
