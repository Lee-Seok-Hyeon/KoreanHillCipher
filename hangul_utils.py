"""한글 음절 <-> 정수 코드 변환 유틸리티.

힐 사이퍼(한글 확장판)에서 '완성형 한글 음절'을 정수로 다루기 위한 모듈이다.
초·중·종성으로 분해하지 않고, 유니코드가 한글 음절에 부여한 순서를 그대로 차용한다.

    code = ord(음절) - 0xAC00      # 0 ~ 11171   ('가' = 0, '힣' = 11171)
    음절 = chr(code + 0xAC00)

장점
    - 분해/결합 로직이 사라져 매핑이 단순하다.
    - 음절 1개 = 정수 1개  이므로 mod 11172 와 정확히 맞아떨어진다.
"""

HANGUL_BASE = 0xAC00                       # '가'
HANGUL_LAST = 0xD7A3                       # '힣'
MODULUS = HANGUL_LAST - HANGUL_BASE + 1    # = 11172  (완성형 한글 음절 총 개수)


def is_hangul_syllable(ch: str) -> bool:
    """완성형 한글 음절('가'~'힣')이면 True."""
    return HANGUL_BASE <= ord(ch) <= HANGUL_LAST


def char_to_code(ch: str) -> int:
    """한글 음절 -> 0~11171 정수."""
    if not is_hangul_syllable(ch):
        raise ValueError(f"완성형 한글 음절이 아닙니다: {ch!r}")
    return ord(ch) - HANGUL_BASE


def code_to_char(code: int) -> str:
    """0~11171 정수 -> 한글 음절."""
    return chr((code % MODULUS) + HANGUL_BASE)
