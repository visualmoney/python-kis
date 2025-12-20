# 동적 버저닝 시스템 (Dynamic Versioning)

이 문서는 Python-KIS의 현재 버전 관리 방식(현행)과 개선 방향(권장)을 설명합니다.

---

## 목표
- 릴리스 자동화: Git 태그 기반으로 버전을 자동 주입
- 일관성: 소스(`pykis/__env__.py`), 배포 메타데이터(`pyproject.toml`), 배포 아티팩트(휠/SDist) 간 동일 버전 보장
- 단순화: 수동 버전 갱신 제거 및 CI에서 재현 가능

---

## 현행 설계

### 구성 요소
- `pyproject.toml`
  - `[project] dynamic = ["version"]`
  - `[tool.setuptools.dynamic] version = { attr = "pykis.__env__.__version__" }`
- `pykis/__env__.py`
  - `VERSION = "{{VERSION_PLACEHOLDER}}"` (CI에서 태그로 대체)
  - `__version__ = VERSION`
- `setuptools-scm` (build-system에 선언)
  - 현재는 직접 사용하지 않음(참조만 있음)
- `tool.poetry.version = "2.1.6"`
  - Poetry 메타 전용(실제 배포 버전과 불일치 가능)

### 동작 흐름
1. 개발 중: `__env__.py` 내 `VERSION`은 `24+dev`로 동작 (placeholder 미치환)
2. 릴리스 태그(v2.2.0 등) 생성 → CI에서 `VERSION_PLACEHOLDER`를 태그 값으로 치환
3. `pip build`/`poetry build` 시 `[tool.setuptools.dynamic]`이 `pykis.__env__.__version__`를 읽어 프로젝트 버전 사용

### 장단점
- 장점: 단일 소스(`__env__.py`)에서 런타임과 배포 메타 버전을 동기화
- 단점:
  - `tool.poetry.version`과의 이중 관리 위험
  - Git 태그가 없을 때 버전 추론 불가 (개발 스냅샷은 `24+dev` 고정)
  - `setuptools-scm` 미활용 (잠재적 자동화 기회 미사용)

---

## 개선 방향 (권장 아키텍처)

### 옵션 A: setuptools-scm 기반 단일 소스 (권장)
- 원칙: "Git 태그 = 단일 진실 공급원(SoT)"
- 구성:
  - `pyproject.toml`
    - `[project] dynamic = ["version"]`
    - `setuptools-scm` 활성(기본값) → Git 태그에서 버전 자동 추론
  - `pykis/__env__.py`
    - `from importlib.metadata import version as _dist_version`
    - `__version__ = _dist_version("python-kis")`
    - 개발 환경(소스 실행)에서는 `try/except`로 `setuptools_scm.get_version()` fallback 사용
- 이점:
  - 태그만으로 배포 버전, 런타임 버전 자동 일치
  - placeholder 치환 스텝 제거(단순화)

### 옵션 B: 현재 구조 유지 + CI 정합성 검사 추가
- CI에서 다음을 보장:
  - 태그 `vX.Y.Z` → `__env__.py` 치환 → 빌드 후 휠 `Metadata-Version` 확인
  - `tool.poetry.version`를 태그와 자동 동기화(커밋)
- 이점: 변경 최소화, 즉시 적용 가능
- 단점: 치환 스크립트/커밋 오버헤드 지속

---

### 옵션 C: Poetry 중심 빌드/배포 (플러그인 기반)

Poetry를 주 빌드/배포 도구로 사용하는 현 상황을 반영하여, 버전을 Git 태그에서 자동으로 주입하는 접근입니다.

**권장 플러그인**: `poetry-dynamic-versioning`

- 기능: Git 태그에서 버전을 추출하여 `tool.poetry.version`을 동적으로 설정
- 장점:
  - Poetry 단일 경로로 메타데이터 관리 (간결성)
  - 태그만으로 버전 일치 자동화 (CI/로컬 모두 유효)
  - `__env__.py` placeholder 제거 가능 (A안과 유사한 단순화)
- 단점:
  - 플러그인 의존성 추가
  - setuptools 기반 동적 버전과 중복 설정 시 충돌 위험 → 한 경로만 유지 필요

**도입 절차**:

1) 플러그인 설치

```bash
poetry self add poetry-dynamic-versioning
poetry self show poetry-dynamic-versioning
```

2) 설정 추가 (`pyproject.toml`)

```toml
[tool.poetry]
version = "0.0.0"  # placeholder, 실제 버전은 태그에서 주입

[tool.poetry-dynamic-versioning]
enable = true
vcs = "git"
style = "pep440"
strict = true
tagged-metadata = true
```

3) 코드 측 (선택)

`pykis/__env__.py`에서 런타임 버전을 배포 메타에서 읽도록 단순화:

```python
from importlib.metadata import version as _dist_version
__version__ = _dist_version("python-kis")
```

4) CI 반영

- 태그 푸시 시 `poetry build` 실행 → 플러그인이 태그를 버전으로 사용
- 비태그 브랜치: `strict=false`로 설정하거나, 사전 릴리스 규칙(`+devN`) 지정

**권고사항**:

- 옵션 C를 채택하는 경우, `[build-system]`의 `setuptools-dynamic` 경로는 제거하여 단일 경로(Poetry)만 사용합니다.
- 문서에 "버전은 Git 태그로 관리한다"를 명시하고, 태그 없이 배포 금지 규칙을 CI로 enforce 합니다.

## 구현 가이드

### A안 (setuptools-scm 전환) 구현 체크리스트
- [ ] `pykis/__env__.py`에서 placeholder 제거 및 `setuptools_scm` fallback 추가
- [ ] CI에서 태그가 없는 커밋은 `+devN` 형태 버전 허용
- [ ] `tool.poetry.version` 제거(또는 문서화: 관리 대상 아님)
- [ ] 배포 전 `git tag` 강제

샘플 코드(`pykis/__env__.py`):
```python
try:
    from importlib.metadata import version as _dist_version
    __version__ = _dist_version("python-kis")
except Exception:
    try:
        from setuptools_scm import get_version
        __version__ = get_version(root="..", relative_to=__file__)
    except Exception:
        __version__ = "0.0.0+unknown"
```

### B안 (현행 유지) 보강 체크리스트
- [ ] CI: 태그 파싱(`vX.Y.Z`) → `__env__.py` placeholder 치환 → 빌드
- [ ] CI: 빌드 산출물의 버전과 태그 일치 검사
- [ ] CI: `pyproject.toml`의 `tool.poetry.version` 자동 동기화 커밋(Optional)

치환 스텝 예시(GitHub Actions):
```bash
$tag=${GITHUB_REF_NAME#v}
python - <<'PY'
from pathlib import Path
p=Path('pykis/__env__.py')
s=p.read_text(encoding='utf-8')
s=s.replace('{{VERSION_PLACEHOLDER}}', '${tag}')
p.write_text(s, encoding='utf-8')
print('Set version to', '${tag}')
PY
```

---

## CI 파이프라인 반영(요약)
- 테스트: `pytest -m "not requires_api" --cov --cov-report=xml`
- 커버리지: `--cov-fail-under=90` 또는 리포터만 업로드 후 대시보드 정책으로 관리
- 아티팩트: `reports/coverage.xml`, `reports/test_report.html` 업로드
- 릴리스(태그): 버전 치환/검증 → `poetry build` → (선택) PyPI 공개

---

## FAQ
- Q: Poetry의 `tool.poetry.version`은 어떻게 하나요?
  - A: 배포 버전은 `[project]/setuptools` 기준으로 관리합니다. 혼동 방지를 위해 제거 또는 문서로 비관리 필드임을 명시합니다.
- Q: 태그 없이 로컬에서 버전은?
  - A: A안은 `setuptools_scm`가 `0.0.0+dirty`/`+devN` 형식을 제공합니다. B안은 `24+dev` 등 개발 표식 유지.
- Q: 런타임에서 `__version__`은?
  - A: 배포 패키지 설치 시 배포 메타에서 읽은 정확한 버전으로 노출됩니다.
