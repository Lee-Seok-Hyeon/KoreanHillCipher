"""한글 힐 사이퍼: 암호화 / 복호화 핵심 로직.

매핑 단위 : 완성형 한글 음절 1개 = 정수 1개  (유니코드 순서 차용)
모듈러    : n = 11172  (= 완성형 한글 음절 총 개수)
블록      : size×size 키 행렬로 음절을 size개씩 묶어 처리
비한글    : 공백·문장부호·영문·숫자 등은 암호화하지 않고 위치 그대로 통과

[ 헤더 블록으로 무손실 패딩 처리 ]
힐 사이퍼는 음절을 size개씩 묶어 행렬을 곱하므로, 음절 개수가 블록 크기의
배수가 아니면 패딩이 필요하다. 복호화 때 "패딩을 정확히 몇 개 떼야 하는지"를
알기 위해, 평문 코드열 앞에 **헤더 블록**을 하나 붙인다.

    header = [pad, 1, 1, ...]            # 첫 칸에 패딩 개수(pad), 나머지는 상수
    full   = header + 평문코드 + [PAD]*pad

full 전체를 블록 단위로 암호화하므로 헤더도 똑같이 행렬을 통과한다(평문 노출 X).
복호화 때 첫 블록을 풀면 pad를 알 수 있고, 그만큼만 정확히 떼어낸다.
→ 평문이 어떤 글자('힣' 포함)로 끝나든 항상 무손실로 복원된다.

암호문 구조(한글을 왼쪽부터 읽으면 암호화 순서와 동일):
    [암호화된 헤더 size개] + [원래 한글 자리(암호문)] + [암호화된 패딩 pad개]
    (비한글은 원래 위치 그대로 사이에 끼어 있음)
"""

from typing import List, Tuple

from hangul_utils import is_hangul_syllable, char_to_code, code_to_char, MODULUS
from matrix_ops import mat_vec_mod, matrix_mod_inverse, Matrix

PAD_CODE = MODULUS - 1     # 패딩 채움 값(복호화 시 개수로 잘라내므로 값 자체는 무관)

Token = Tuple[str, object]   # ('hangul', code:int) | ('plain', ch:str)


def _tokenize(text: str) -> List[Token]:
    """문자열을 ('hangul', code) / ('plain', char) 토큰 리스트로 분해."""
    tokens: List[Token] = []
    for ch in text:
        if is_hangul_syllable(ch):
            tokens.append(("hangul", char_to_code(ch)))
        else:
            tokens.append(("plain", ch))
    return tokens


def _blocks(seq: List[int], size: int):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def encode_full(plaintext: str, size: int):
    """평문 -> (tokens, real, N, pad, header, full).

    real  : 평문 속 한글 음절 코드열
    N     : 한글 음절 개수
    pad   : 마지막 블록을 채우기 위한 패딩 개수
    header: [pad, 0, ...] (size칸짜리 헤더 블록)
    full  : header + real + [PAD_CODE]*pad   (길이 = size + N + pad, size의 배수)
    """
    tokens = _tokenize(plaintext)
    real = [c for kind, c in tokens if kind == "hangul"]
    N = len(real)
    pad = (size - N % size) % size
    # 헤더 블록: 첫 칸에 패딩 개수(pad). 나머지 칸은 0이 아닌 상수(1)로 채워
    # 영벡터(K·0=0 → 항상 '가'로 노출)가 되는 것을 막는다.
    header = [pad] + [1] * (size - 1)
    full = header + real + [PAD_CODE] * pad
    return tokens, real, N, pad, header, full


def encrypt(plaintext: str, K: Matrix, n: int = MODULUS) -> str:
    """C = K · v  (mod n) 를 블록 단위로 적용해 암호문을 만든다."""
    size = len(K)
    tokens, real, N, pad, header, full = encode_full(plaintext, size)

    enc: List[int] = []
    for block in _blocks(full, size):
        enc.extend(mat_vec_mod(K, block, n))

    enc_header = enc[:size]            # 암호화된 헤더 블록
    enc_real = enc[size:size + N]      # 원래 한글 자리에 들어갈 값
    enc_fillers = enc[size + N:]       # 암호화된 패딩

    out: List[str] = [code_to_char(c) for c in enc_header]   # 1) 헤더를 맨 앞에
    idx = 0
    for kind, val in tokens:                                 # 2) 원래 순서대로
        if kind == "hangul":
            out.append(code_to_char(enc_real[idx]))
            idx += 1
        else:
            out.append(val)
    out.extend(code_to_char(c) for c in enc_fillers)         # 3) 패딩을 맨 끝에
    return "".join(out)


def decrypt_trace(ciphertext: str, K: Matrix, n: int = MODULUS):
    """복호화 중간 결과를 모두 반환: (tokens, codes, Kinv, dec, pad, N, real).

    오류(길이 불일치/헤더 손상)는 ValueError 로 알린다.
    """
    size = len(K)
    Kinv = matrix_mod_inverse(K, n)
    tokens = _tokenize(ciphertext)
    codes = [c for kind, c in tokens if kind == "hangul"]

    if len(codes) < size or len(codes) % size != 0:
        raise ValueError(
            f"암호문의 한글 음절 수가 {len(codes)}개로 올바르지 않습니다 "
            f"(헤더 {size}개 + 데이터, {size}의 배수여야 함). 암호문을 옮겨 "
            f"적는 과정에서 글자가 빠지거나 바뀌었을 가능성이 큽니다."
        )

    dec: List[int] = []
    for block in _blocks(codes, size):
        dec.extend(mat_vec_mod(Kinv, block, n))

    pad = dec[0]                       # 헤더 블록 첫 칸 = 패딩 개수
    if not (0 <= pad < size):
        raise ValueError(
            f"복원된 패딩 정보(={pad})가 비정상입니다. 키가 다르거나 암호문이 "
            f"손상됐을 수 있습니다."
        )
    data = dec[size:]                  # 헤더 블록을 뗀 실제 데이터
    N = len(data) - pad
    if N < 0:
        raise ValueError("암호문 길이가 헤더 정보와 맞지 않습니다.")
    real = data[:N]
    return tokens, codes, Kinv, dec, pad, N, real


def decrypt(ciphertext: str, K: Matrix, n: int = MODULUS) -> str:
    """v = K^{-1} · C  (mod n) 로 복호화하고, 헤더가 알려준 길이만큼 정확히 복원."""
    size = len(K)
    tokens, codes, Kinv, dec, pad, N, real = decrypt_trace(ciphertext, K, n)

    out: List[str] = []
    hangul_seen = 0
    real_idx = 0
    for kind, val in tokens:
        if kind == "hangul":
            if hangul_seen < size:          # 앞쪽 size개 = 헤더 → 버림
                pass
            elif real_idx < N:              # 실제 본문 N개 → 복원
                out.append(code_to_char(real[real_idx]))
                real_idx += 1
            else:                           # 뒤쪽 pad개 = 패딩 → 버림
                pass
            hangul_seen += 1
        else:
            out.append(val)
    return "".join(out)
