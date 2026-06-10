from math import gcd

from hangul_utils import MODULUS, code_to_char
from matrix_ops import determinant, mat_vec_mod
from key_generator import generate_key_matrix
from cipher import encrypt, decrypt, encode_full, decrypt_trace, PAD_CODE

N = MODULUS

LINE = "=" * 46
MENU = f"""
{LINE}
                한글 힐 사이퍼
{LINE}
 (1) 새로운 키 행렬 설정하기
 (2) 키 행렬 직접 입력하기
 (3) 암호화하기
 (4) 복호화하기
 (5) 현재 키 정보 보기
 (6) 자동 데모 실행
 (0) 종료
{LINE}"""

LOG_PROMPT = "단계별 로그를 보려면 0을, 넘기려면 그 외 아무 키나 누르세요: "


def parse_key(s: str):
    """ "a,b,c;d,e,f;g,h,i" 형식 문자열 -> 정사각 행렬."""
    rows = [r for r in s.strip().split(";") if r.strip()]
    K = [[int(x.strip()) for x in row.split(",")] for row in rows]
    size = len(K)
    if size == 0 or any(len(r) != size for r in K):
        raise ValueError("정사각 행렬이 아닙니다 (행/열 개수 불일치).")
    return K


def format_key(K) -> str:
    return ";".join(",".join(str(x) for x in row) for row in K)


def print_matrix(M, indent="    "):
    w = max(len(str(x)) for row in M for x in row)
    for row in M:
        print(indent + "[ " + "  ".join(str(x).rjust(w) for x in row) + " ]")


def key_summary(K):
    d = determinant(K) % N
    g = gcd(d, N)
    print(f"  크기 : {len(K)}×{len(K)}   (mod {N})")
    print_matrix(K)
    msg = "역행렬 존재 -> 복호화 가능" if g == 1 else "역행렬 없음 -> 복호화 불가"
    print(f"  det(K) mod n = {d},  gcd(det, n) = {g}  ->  {msg}")


def ask_int(prompt: str, default: int) -> int:
    raw = input(prompt).strip()
    return int(raw) if raw else default


# ------------------------- 단계별 로그 ------------------------- #
def _token_display(tokens):
    parts = []
    for kind, val in tokens:
        if kind == "hangul":
            parts.append(f"'{code_to_char(val)}' -> {val}\n")
        else:
            parts.append(f"{val!r} -> {val!r}\n")
    return "  ".join(parts) if parts else "(한글 없음)"


def log_encrypt(text, K):
    """암호화 과정을 단계별로 출력하고 암호문을 반환."""
    size = len(K)
    tokens, real, N, pad, header, full = encode_full(text, size)
    print("\n------------- 암호화 단계별 로그 -------------")
    print(f"[1] 평문 : {text!r}\n")
    print("[2] 음절 -> 정수\n  " + _token_display(tokens))
    print(f"한글 코드열({N}개) = {real}\n")
    print(f"[3] 헤더 블록 {header} (첫 칸=패딩 수 {pad}) + 패딩 {pad}개")
    print(f"    암호화 대상 full = {full}\n")
    print(f"\n[4] 블록별 C = K · v (mod {MODULUS})")
    for i in range(0, len(full), size):
        v = full[i:i + size]
        tag = " (헤더)" if i == 0 else ""
        print(f"      v={v}  ->  C={mat_vec_mod(K, v, MODULUS)}{tag}")
    cipher = encrypt(text, K)
    print(f"\n[5] 암호문 : {cipher!r}  (앞 {size}글자=암호화된 헤더)")
    return cipher


def log_decrypt(ciphertext, K):
    """복호화 과정을 단계별로 출력하고 평문을 반환."""
    size = len(K)
    try:
        tokens, codes, Kinv, dec, pad, N, real = decrypt_trace(ciphertext, K)
    except ValueError as e:
        print(f"  ! {e}")
        return None
    print("\n------------- 복호화 단계별 로그 -------------")
    print("[1] 모듈러 역행렬 K^(-1) (mod n)")
    print_matrix(Kinv)
    print("\n[2] 암호문 음절 -> 정수\n  " + _token_display(tokens))
    print(f"암호 코드열 = {codes}\n")
    print(f"[3] 블록별 v = K^(-1) · C (mod {MODULUS})")
    for i in range(0, len(codes), size):
        block = codes[i:i + size]
        tag = " (헤더)" if i == 0 else ""
        print(f"      C = {block}\t->\tv = {mat_vec_mod(Kinv, block, MODULUS)}{tag}")
    print(f"\n[4] 헤더 해석: pad={pad} -> 앞 {size}글자(헤더)·뒤 {pad}글자(패딩) 제거")
    print(f"    실제 본문 코드({N}개) = {real}\n")
    print(f"[5] 평문 : {decrypt(ciphertext, K)!r}")
    return decrypt(ciphertext, K)


def action_new_key():
    try:
        size = ask_int("키 행렬 크기 (기본 3): ", 3)
    except ValueError:
        print("  ! 숫자를 입력하세요.")
        return None
    if size < 2:
        print("  ! 크기는 2 이상이어야 합니다.")
        return None
    K = generate_key_matrix(size, N)
    print("\n[새 키 생성 완료]")
    key_summary(K)
    return K


def action_input_key():
    print('형식 예시:  5,17,3;2,9,11;7,4,6   (행은 ; 로, 원소는 , 로 구분)')
    raw = input("키 행렬 입력: ")
    try:
        K = parse_key(raw)
    except ValueError as e:
        print(f"  ! 입력 형식 오류: {e}")
        return None
    d = determinant(K) % N
    if gcd(d, N) != 1:
        print(f"  ! 이 행렬은 gcd(det, {N}) = {gcd(d, N)} 이라 복호화할 수 없습니다.")
        print("    (det 가 2·3·7·19 중 하나의 배수) — 다른 행렬을 입력하세요.")
        return None
    print("\n[키 설정 완료]")
    key_summary(K)
    return K


def action_encrypt(K):
    if K is None:
        print("  ! 먼저 키를 설정하세요 (메뉴 1 또는 2).")
        return None
    text = input("평문 입력: ")
    cipher = encrypt(text, K)
    print(f"  암호문 -> {cipher}")
    if input(LOG_PROMPT).strip() == "0":
        log_encrypt(text, K)
    return cipher


def action_decrypt(K, last_cipher):
    if K is None:
        print("  ! 먼저 키를 설정하세요 (메뉴 1 또는 2).")
        return
    text = input("암호문 입력 (엔터 시 마지막 암호문 사용): ")
    if not text:
        if last_cipher:
            text = last_cipher
            print(f"  (마지막 암호문 사용) {text}")
        else:
            print("  ! 입력된 암호문이 없습니다.")
            return
    try:
        plain = decrypt(text, K)
    except ValueError as e:
        print(f"  ! 복호화 실패: {e}")
        return
    print(f"  복호문 -> {plain}")
    if input(LOG_PROMPT).strip() == "0":
        log_decrypt(text, K)


def action_show_key(K):
    if K is None:
        print("  현재 설정된 키가 없습니다. (메뉴 1 또는 2로 설정하세요.)")
        return
    print("[현재 키]")
    key_summary(K)


def action_demo():
    text = "이것은 한글 힐 사이퍼입니다."
    size = 3

    print("\n" + LINE)
    print("  자동 데모 (음절 단위 매핑 · mod 11172)")
    print(LINE)
    print("11172 = 2^2 · 3 · 7^2 · 19  (합성수)")
    print("  -> 키 검증은 det != 0 이 아니라 gcd(det, 11172) = 1 이어야 함\n")

    K = generate_key_matrix(size, N)
    print(f"[STEP 0] {size}×{size} 키 행렬 생성")
    print_matrix(K)
    d = determinant(K) % N
    print(f"  det(K) mod n = {d},  gcd(det, n) = {gcd(d, N)}")

    cipher = log_encrypt(text, K)        # 암호화 단계별 로그
    recovered = log_decrypt(cipher, K)   # 복호화 단계별 로그
    print(f"\n[검증] 원문 일치 : {'성공' if recovered == text else '실패'}")


def main():
    key = None
    last_cipher = None
    while True:
        print(MENU)
        try:
            choice = input("선택 > ").strip()
            if choice == "1":
                new = action_new_key()
                if new is not None:
                    key = new
            elif choice == "2":
                new = action_input_key()
                if new is not None:
                    key = new
            elif choice == "3":
                result = action_encrypt(key)
                if result is not None:
                    last_cipher = result
            elif choice == "4":
                action_decrypt(key, last_cipher)
            elif choice == "5":
                action_show_key(key)
            elif choice == "6":
                action_demo()
            elif choice == "0":
                print("제작자: 고려대학교 컴퓨터소프트웨어학과 이석현")
                break
            else:
                print("  ! 0~6 사이의 숫자를 입력하세요.")
        except (EOFError, KeyboardInterrupt):
            print("\n입력이 종료되어 메뉴를 닫습니다.")
            break


if __name__ == "__main__":
    main()
