# Step 1: billing-deletion-contracts

## 읽어야 할 파일

먼저 아래 파일들을 읽고 프로젝트의 아키텍처와 설계 의도를 파악하라:

- `harness/harness-framework-codex/AGENTS.md`
- `harness/harness-framework-codex/docs/PRD.md`
- `harness/harness-framework-codex/docs/ARCHITECTURE.md`
- `harness/harness-framework-codex/docs/ADR.md`
- `backend/app/main.py`
- `backend/app/services/billing.py`
- `backend/app/services/polar_webhook.py`
- `tests/test_account_deletion.py`
- `tests/test_polar_webhook.py`
- `tests/test_checkout_api.py`

이전 step에서 생성/수정된 테스트와 문서를 먼저 읽고, auth schema 계약과 충돌하지 않게 작업하라.

## 작업

1. 앱 계정삭제 플로우의 billing 계약을 고정한다.
   - 유료 구독과 `polar_subscription_id`가 있으면 로컬 soft-delete 전에 Polar subscription revoke를 먼저 호출해야 한다.
   - Polar revoke 실패 시 local subscription/account를 free로 낮추거나 profile을 deleted 처리하지 않아야 한다.
   - revoke 성공 또는 Polar 404(이미 없음)일 때만 local subscription 상태를 `free`로 동기화하고 `polar_subscription_id`를 `None`으로 비운다.
2. 필요한 경우 `BillingService.revoke_polar_subscription(polar_subscription_id: str) -> None`의 테스트를 보강한다.
   - URL은 `/v1/subscriptions/{id}`를 사용한다.
   - subscription id는 URL-safe하게 quote한다.
   - 404는 성공 취급한다.
   - 4xx/5xx와 network error는 `PolarCheckoutUpstreamError`로 전달한다.
3. webhook 기반 취소 처리와 앱 계정삭제 처리의 상태 전이가 서로 충돌하지 않는지 확인한다.

## Acceptance Criteria

```bash
python -m py_compile backend/app/main.py backend/app/services/billing.py backend/app/services/polar_webhook.py tests/test_account_deletion.py tests/test_polar_webhook.py tests/test_checkout_api.py
```

가능하고 `.env` 접근 금지 지시를 위반하지 않는 환경이면 다음도 실행한다:

```bash
pytest tests/test_account_deletion.py tests/test_polar_webhook.py tests/test_checkout_api.py
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. 아키텍처 체크리스트를 확인한다:
   - Polar API 호출은 `backend/app/services/billing.py`에 있고 route는 thin orchestration만 하는가?
   - account deletion은 soft-delete 정책을 유지하는가?
   - Polar customer/payment record 전체 삭제가 아니라 subscription revoke만 수행하는가?
3. 결과에 따라 `phases/auth-billing-stability/index.json`의 step 1을 업데이트한다:
   - 성공: `"status": "completed"`, `"summary": "Account deletion revokes Polar subscriptions before local soft-delete and preserves failure safety."`
   - 수정 3회 시도 후에도 실패: `"status": "error"`, `"error_message": "구체적 에러 내용"`
   - 사용자 개입 필요: `"status": "blocked"`, `"blocked_reason": "구체적 사유"` 후 즉시 중단

## 금지사항

- Polar customer 전체 삭제 API를 사용하지 마라. 이유: 결제/세금/감사 이력은 외부 시스템에 보존되어야 한다.
- Polar revoke 실패 후 로컬 DB만 free/deleted로 바꾸지 마라. 이유: 고아 유료 구독이 남는다.
- `polar_subscription_id`를 free 상태에 남기지 마라. 이유: 이후 동기화와 UI가 오래된 유료 구독으로 오판할 수 있다.
- `.env`를 읽지 마라. 이유: 루트 AGENTS 지시가 명시적으로 금지한다.
