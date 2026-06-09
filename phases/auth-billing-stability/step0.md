# Step 0: auth-schema-contracts

## 읽어야 할 파일

먼저 아래 파일들을 읽고 프로젝트의 아키텍처와 설계 의도를 파악하라:

- `harness/harness-framework-codex/AGENTS.md`
- `harness/harness-framework-codex/docs/PRD.md`
- `harness/harness-framework-codex/docs/ARCHITECTURE.md`
- `harness/harness-framework-codex/docs/ADR.md`
- `backend/app/main.py`
- `backend/app/db/models.py`
- `supabase/migrations/20260531000100_allow_google_onboarding_without_username.sql`
- `tests/test_account_deletion.py`
- `tests/test_auth.py`

이 step은 최근 Google OAuth 가입 시 `profiles.username` NOT NULL 때문에 `/auth/v1/callback`이 실패했던 문제를 다시 깨지지 않게 계약으로 고정한다.

## 작업

1. Auth/onboarding DB 계약을 코드와 마이그레이션 기준으로 확인한다.
   - `profiles.username`은 Google OAuth 직후에는 `NULL` 가능해야 한다.
   - `profiles.nickname`은 과거 trigger/호환성 때문에 컬럼이 존재할 수 있으나, UI 입력 필드는 `username`만 요구한다.
   - onboarding 완료 시 `username`을 저장하고 `nickname`이 비어 있으면 `username`으로 보조 채움한다.
2. 필요한 경우 테스트를 보강한다.
   - Google OAuth 직후 profile에 username이 없어도 `/api/auth/me`가 onboarding 필요 상태를 반환하는지 확인하는 테스트를 추가 또는 보강한다.
   - onboarding 완료 시 `username`과 약관/개인정보 동의 시간이 저장되는 기존 계약을 유지한다.
3. 필요한 경우 Supabase migration 주석 또는 테스트 이름을 명확히 해서, 앞으로 `username NOT NULL`을 되돌리지 않도록 한다.

## Acceptance Criteria

```bash
python -m py_compile backend/app/main.py backend/app/db/models.py tests/test_account_deletion.py tests/test_auth.py
```

가능하고 `.env` 접근 금지 지시를 위반하지 않는 환경이면 다음도 실행한다:

```bash
pytest tests/test_account_deletion.py tests/test_auth.py
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. 아키텍처 체크리스트를 확인한다:
   - Auth route orchestration은 `backend/app/main.py`에 남아 있고, DB 모델은 `backend/app/db/models.py`에 남아 있는가?
   - Supabase `raw_user_meta_data`를 권한 판단에 사용하지 않는가?
   - UI에 nickname 입력 요구를 추가하지 않았는가?
3. 결과에 따라 `phases/auth-billing-stability/index.json`의 step 0을 업데이트한다:
   - 성공: `"status": "completed"`, `"summary": "Auth schema contract tests/documentation keep Google OAuth username nullable and onboarding explicit."`
   - 수정 3회 시도 후에도 실패: `"status": "error"`, `"error_message": "구체적 에러 내용"`
   - 사용자 개입 필요: `"status": "blocked"`, `"blocked_reason": "구체적 사유"` 후 즉시 중단

## 금지사항

- `.env`를 읽지 마라. 이유: 루트 AGENTS 지시가 명시적으로 금지한다.
- `profiles.username`을 다시 NOT NULL로 만들지 마라. 이유: Google OAuth callback 단계에서는 앱 username이 아직 없다.
- frontend에 nickname 필수 입력칸을 추가하지 마라. 이유: 제품 UX는 username onboarding만 요구한다.
- Supabase Auth user metadata를 권한 판단 기준으로 사용하지 마라. 이유: user metadata는 사용자 편집 가능하다.
