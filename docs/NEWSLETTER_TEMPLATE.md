"""
# Python-KIS 월간 뉴스레터 템플릿

## 📰 Python-KIS Monthly Newsletter

### 2025년 12월호

---

## 🎯 이번 달의 주요 뉴스

### 1️⃣ Phase 3 에러 처리 & 로깅 시스템 완료

**개선 사항:**
- ✅ Exception 클래스 확대: 3개 → 13개
  - `KisConnectionError`, `KisAuthenticationError`, `KisRateLimitError` 등
  - 각 에러에 대한 재시도 가능 여부 명시

- ✅ Retry 메커니즘 구현
  - Exponential backoff with jitter
  - `@with_retry` 및 `@with_async_retry` 데코레이터
  - 최대 재시도 설정 가능

- ✅ JSON 구조 로깅 추가
  - `JsonFormatter` 클래스로 ELK/Datadog 호환
  - 로그 레벨별 색상 구분 (DEBUG/INFO/WARNING/ERROR)
  - 타임스탐프, 예외 정보, 컨텍스트 자동 포함

**영향:**
- 프로덕션 환경에서 안정성 향상
- 디버깅 시간 단축
- 자동 재시도로 일시적 오류 대응 개선

**예제:**
```python
from pykis.utils.retry import with_retry
from pykis.logging import enable_json_logging

# JSON 로깅 활성화 (프로덕션)
enable_json_logging()

# 재시도 메커니즘 적용
@with_retry(max_retries=5, initial_delay=2.0)
def fetch_quote(symbol):
    return kis.stock(symbol).quote()

quote = fetch_quote("005930")
```

---

### 2️⃣ CI/CD 파이프라인 확장

**개선 사항:**
- ✅ Cross-platform 테스트: 3 OS × 2 Python 버전 (6 조합)
- ✅ 자동 커버리지 검사: 90% 미만 시 빌드 실패
- ✅ Pre-commit 훅 8개 자동화
- ✅ 통합/성능 테스트 14개 추가

**이점:**
- Windows, macOS 사용자 버그 조기 발견
- 코드 품질 자동 유지
- 메인브랜치 안정성 보장

---

### 3️⃣ 공개 API 정리 완료

**변경:**
- 공개 API: 154개 → 20개 (89% 축소)
- IDE 자동완성: 명확하고 간결함
- 문서화: 사용자 혼란 제거

**사용 방법:**
```python
# ✅ 추천: 공개 API만 사용
from pykis import PyKis, Quote, Balance, Order
from pykis.helpers import create_client

kis = create_client("config.yaml")
quote: Quote = kis.stock("005930").quote()

# ⚠️ 내부 구현 (v3.0.0에서 제거)
from pykis.types import KisObjectProtocol  # Deprecated
```

---

## 📊 통계

| 항목 | 현황 | 변화 |
|------|------|------|
| **예외 클래스** | 13개 | +10개 |
| **테스트** | 863개 | +31개 |
| **커버리지** | 94% | +1% |
| **공개 API** | 20개 | -134개 |
| **문서** | 7개 | +1개 (FAQ) |

---

## 🆕 새로운 기능

### JSON 구조 로깅

```python
from pykis.logging import enable_json_logging

enable_json_logging()

# 이후 로그는 JSON 형식으로 출력
# {"timestamp": "2025-12-20T14:20:00+00:00", "level": "INFO", 
#  "message": "...", "module": "kis", ...}
```

### 자동 재시도

```python
from pykis.utils.retry import with_retry

@with_retry(max_retries=5, initial_delay=1.0)
def fetch_data(symbol):
    return kis.stock(symbol).quote()

# 429/5xx 에러 시 자동 재시도 (exponential backoff)
```

### 서브 로거

```python
from pykis.logging import get_logger

api_logger = get_logger("pykis.api")
client_logger = get_logger("pykis.client")

api_logger.info("API 호출 시작")
client_logger.debug("HTTP 요청 전송")
```

---

## 🐛 버그 수정

| 버그 | 해결 |
|------|------|
| **pre-commit 훅 실패** | 로컬 pytest/coverage 훅 제거 (CI에서만 검사) |
| **Windows 인코딩 문제** | UTF-8 명시적 설정 |
| **Rate limit 처리 부재** | `KisRateLimitError` + retry 메커니즘 추가 |

---

## 📚 문서 업데이트

### 이번 달 추가된 문서

1. **FAQ.md** (23개 Q&A)
   - 설치, 인증, 시세, 주문, 계좌, 에러처리, 고급 사용법
   - Windows 인코딩, Docker 실행, 성능 최적화 팁

2. **ARCHITECTURE_REPORT_V3_KR.md** (Phase 3 업데이트)
   - Phase 3 Week 1-2 완료 마크
   - 에러 처리 & 로깅 세부 설명

### 다음 달 계획

- [ ] Jupyter Notebook 튜토리얼 (3개)
- [ ] 영문 문서 작성 (QUICKSTART, FAQ)
- [ ] 튜토리얼 비디오 스크립트
- [ ] 기여자 가이드 (CONTRIBUTING.md)

---

## 🚀 다음 릴리스 (v2.2.0)

### 예정된 변경사항

- 공개 타입 모듈 분리 (`pykis/public_types.py`)
- `__init__.py` 리팩토링 (공개 API 최소화)
- Deprecation 경고 시스템
- 마이그레이션 가이드

### 릴리스 일정

- **일정**: 2026년 1월 (약 2-3주)
- **주요 기능**: 에러 처리, 로깅, 공개 API 정리
- **하위 호환성**: 100% 유지

---

## 👥 커뮤니티

### GitHub Discussions 새로운 주제

| 주제 | 수 | 상태 |
|------|-----|------|
| **질문** | 12 | 🟢 답변됨 |
| **기능 제안** | 5 | 🟡 검토 중 |
| **버그 리포트** | 3 | 🟢 해결됨 |

**인기 질문 (이번 달)**:
1. "Rate limit을 어떻게 처리하나요?" - ✅ 해결 (v2.2.0에서 자동 재시도)
2. "로그 레벨을 조절할 수 있나요?" - ✅ 가능 (setLevel 함수)
3. "Windows에서 에러가 발생합니다" - ✅ FAQ 추가

### 기여자

이번 달 감사의 말:
- 🙏 버그 리포트를 해주신 모든 분들
- 🙏 코드 리뷰와 아이디어를 주신 분들
- 🙏 문서 개선을 위해 피드백해주신 분들

---

## 📈 성과 지표

```
🔴 에러 처리: Week 1-2 완료 ✅
🟡 로깅 시스템: Week 1-2 완료 ✅
🟢 다음 목표: Week 3-4 (문서, 커뮤니티) 진행 중
```

**프로젝트 진행률**:
- Phase 1 (공개 API 정리): ✅ 100% 완료
- Phase 2 (CI/CD & 테스트): ✅ 100% 완료
- Phase 3 (에러/로깅 & 커뮤니티): 🔄 50% 완료 (Week 1-2 완료, Week 3-4 진행 중)

---

## 💡 팁 & 트릭

### Tip 1: 배치 요청으로 성능 향상

```python
# 비효율적: N 번의 개별 요청
for symbol in symbols:
    quote = kis.stock(symbol).quote()

# 효율적: 가능하면 배치 요청
quotes = kis.stocks(symbols).quotes()
```

### Tip 2: 비동기 처리로 속도 향상

```python
import asyncio
from pykis import PyKis

async def fetch_all():
    tasks = [kis.stock(s).quote_async() for s in symbols]
    return await asyncio.gather(*tasks)

results = asyncio.run(fetch_all())
```

### Tip 3: JSON 로깅으로 운영 편의성 향상

```python
from pykis.logging import enable_json_logging

# 프로덕션에서 활성화하면 ELK/Datadog 등에서 쉽게 분석 가능
enable_json_logging()
```

---

## 📅 이벤트 & 일정

### 예정된 일정

- **2025-12-31**: v2.1.7 보안 패치 릴리스
- **2026-01-15**: v2.2.0 (Phase 3 Week 1-2 포함) 릴리스
- **2026-02-15**: v2.3.0 (추가 문서, Jupyter) 릴리스
- **2026-03-01**: v3.0.0 (공개 API 최종 정리) 계획

### 커뮤니티 모임 (Online)

- **정기**: 매월 첫째 주 수요일 20:00 (KST)
- **주제**: 사용 팁, 버그 리포트, 기능 제안
- **링크**: [GitHub Discussions](https://github.com/QuantumOmega/python-kis/discussions)

---

## 🎁 이달의 추천 (Tip of the Month)

### "예상치 못한 네트워크 오류? 재시도 데코레이터를 사용하세요!"

```python
from pykis.utils.retry import with_retry

@with_retry(max_retries=5, initial_delay=2.0)
def reliable_fetch(symbol):
    return kis.stock(symbol).quote()

# 자동으로 exponential backoff로 재시도됩니다
quote = reliable_fetch("005930")
```

이제 일시적인 네트워크 오류나 서버 부하로 인한 429 에러도 자동으로 처리됩니다!

---

## 🔗 유용한 링크

- 📖 [공식 문서](https://github.com/QuantumOmega/python-kis)
- 💬 [GitHub Discussions](https://github.com/QuantumOmega/python-kis/discussions)
- 🐛 [Bug Reports](https://github.com/QuantumOmega/python-kis/issues)
- 📚 [FAQ](./FAQ.md)
- 🚀 [QUICKSTART](./QUICKSTART.md)
- 📋 [CHANGELOG](./CHANGELOG.md)

---

## 📝 구독 및 피드백

**이 뉴스레터를 개선하는 데 도움을 주세요!**

- ❓ 알고 싶은 기능이 있나요? [Issues](https://github.com/QuantumOmega/python-kis/issues) 또는 [Discussions](https://github.com/QuantumOmega/python-kis/discussions)에서 제안해주세요.
- 💬 피드백이 있으신가요? GitHub Discussions "Newsletter Feedback" 주제로 댓글 남겨주세요.
- 📧 이메일로 구독하고 싶으신가요? [여기](https://github.com/QuantumOmega/python-kis#subscribe)에서 가능합니다.

---

**Python-KIS 팀**
**발행일**: 2025-12-20
**다음 호**: 2026-01-20
"""
