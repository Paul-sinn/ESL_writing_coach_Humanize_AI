# HumanizeIQ — 법적·윤리 리스크 리포트

**작성일:** 2026-05-01
**검토 범위:** 코드베이스 전체 (backend, frontend, CLAUDE.md 페르소나 문서)

---

## 1. 학문적 부정직 조장 리스크 (Academic Integrity Risk)

### 1-1. 핵심 문제: 제품 설계 의도 자체가 부정행위 조장

`CLAUDE.md`의 타겟 페르소나 정의가 가장 심각한 문제입니다.

> *"Kim is taking English classes... he uses AI to generate his essays. His core anxiety: getting caught by his professor's AI detection tools."*
> *"A humanizer that rewrites AI-generated text to pass detection"*

서비스의 핵심 가치 제안이 **AI 탐지 도구 우회**임을 내부 문서가 명시적으로 선언하고 있습니다. 투자자 실사, 법적 분쟁, 규제 기관 조사 시 이 문서는 불리한 증거가 됩니다.

### 1-2. 관련 법·규정 노출

| 구분 | 내용 | 리스크 수준 |
|---|---|---|
| **OpenAI 이용약관** | 학문적 무결성 도구를 우회하는 콘텐츠 생성을 명시 금지 (Usage Policies §3) | **Critical** |
| **영국 contract cheating 법** | 타인의 과제를 대신 작성해주는 서비스 운영을 형사처벌 대상으로 규정 | High |
| **호주 TEQSA Act 2011** | 'Academic cheating service' 운영을 연방 범죄로 규정 | High |
| **한국 교육법·대학 학칙** | 직접 처벌 규정 미비, 민사 손해배상 소송 가능성 존재 | Medium |
| **미국 FERPA** | 학생 데이터 처리 시 복잡한 개인정보 의무 발생 | Medium |

### 1-3. OpenAI API 약관 위반 — 즉각 대응 필요

`config.py`의 `humanize_model: gpt-5` 설정이 AI 탐지 우회 텍스트 생성에 사용됩니다. OpenAI 이용약관 위반 확인 시 **API 키 즉시 정지** 처분 가능 → 서비스 전체 중단 리스크.

### 1-4. 권고

- **단기:** UI 및 내부 문서에서 "pass detection", "evade" 등 우회 의도 표현 제거
- **중기:** 허용 가능한 유스케이스 재정의 — "영어 작문 향상 도구"로 포지셔닝 전환
- **문서:** `CLAUDE.md` 페르소나 설명을 법적으로 방어 가능한 표현으로 수정

---

## 2. 개인정보 처리 리스크 (Privacy Risk)

### 2-1. 수집 데이터 목록 (코드 기준)

| 데이터 | 수집 위치 | 제3자 전송 여부 |
|---|---|---|
| 에세이 전문 텍스트 | `POST /api/analyze`, `POST /api/humanize` | OpenAI API로 전송됨 |
| IP 주소 | `main.py` — `client_ip = request.client.host` | 서버 내 저장 (rate limit용) |
| 사용자 ID | `X-User-Id` 헤더 | 서버 내 저장 |
| LangSmith 트레이스 | `.env`의 `LANGSMITH_API_KEY` 설정 시 | LangSmith 외부 서버로 워크플로우 전체 전송 |

### 2-2. 핵심 위반 사항

**GDPR (EU 이용자 대상 시)**
- 개인정보 처리 동의 메커니즘 없음 — 텍스트 입력 전 OpenAI 전송 사실 미고지
- Privacy Notice 없음
- 데이터 보존 정책 없음

**한국 PIPA (개인정보보호법) — 타겟 페르소나가 한국인**
- 제15조: 개인정보 수집 시 목적·항목·보유기간 고지 의무 위반
- 제17조: 제3자 제공(OpenAI) 시 별도 동의 필요
- 위반 시 과태료 최대 3천만 원, 중대 위반 시 형사처벌

**LangSmith 트레이싱 — 숨겨진 리스크**
`LANGSMITH_API_KEY`가 설정되면 에세이 원문이 외부 서버에 저장되나 사용자에게 전혀 고지되지 않음.

### 2-3. 인증 보안 결함

`backend/app/main.py`의 `get_user_id()`:

```python
def get_user_id(x_user_id: str | None) -> str:
    return x_user_id or "demo-pro"
```

`X-User-Id` 헤더가 완전히 인증되지 않습니다. 누구든 임의의 사용자 ID를 헤더에 담아 다른 계정의 크레딧을 소비할 수 있습니다. **과금 데이터 무결성 침해이자 개인정보 위반.**

---

## 3. 이용약관 미비 사항 (Terms of Service Requirements)

### 3-1. 현재 존재하지 않는 필수 문서

| 문서 | 법적 필요성 | 현황 |
|---|---|---|
| 이용약관 (ToS) | 서비스 이용 계약의 기초 | **없음** |
| 개인정보처리방침 | GDPR·PIPA·CCPA 법적 의무 | **없음** |
| 환불 정책 | 유료 서비스 과금 시 소비자보호법 의무 | **없음** |
| AI 생성 콘텐츠 면책 고지 | 출력물 정확성 관련 책임 한정 | **없음** |

### 3-2. 결제 시스템 미완성

`backend/app/services/billing.py`:

```python
def create_checkout_url(self, product_code: str) -> str:
    return f"https://billing.example.com/checkout/{product_code}"
```

실제 결제 프로세서 미연동 상태. 실제 결제를 수집하면서 이 상태를 유지하면 **사기(Fraud)에 해당**.

### 3-3. CORS 와일드카드

`backend/app/main.py`:

```python
allow_origins=["*"]
```

프로덕션 환경에서 CORS 전체 허용은 CSRF 공격 벡터를 열어 보안 정책상 수용 불가.

---

## 4. 우선순위별 권고 요약

### Critical (즉시 조치)
1. OpenAI 이용약관 재검토 — 현재 사용 목적 위반 여부 확인 또는 사용 방식 변경
2. `X-User-Id` 헤더 인증 구현 — 현재 완전 무방비 상태 (`main.py:get_user_id`)

### High (출시 전 필수)
3. 개인정보처리방침 작성 및 게시 (OpenAI 데이터 전송 포함)
4. 이용약관 작성 — 서비스 허용 범위, 학문적 부정직 면책 조항 포함
5. 결제 프로세서 연동 전까지 유료 결제 버튼 비활성화
6. LangSmith 트레이싱 사용 여부 사용자 고지

### Medium (출시 후 단기)
7. 서비스 포지셔닝 재정의 — "AI 탐지 우회"에서 "영어 작문 개선"으로
8. CORS 허용 도메인 명시 제한 (`allow_origins=["https://yourdomain.com"]`)
9. 데이터 보존 정책 수립 및 자동 삭제 구현
10. AI 분석 결과 정확성 보장 불가 면책 고지 추가

---

*이 리포트는 코드 분석 기반의 내부 검토이며, 실제 법적 의견을 대체하지 않습니다. 상업적 출시 전 법률 전문가 검토를 권장합니다.*
