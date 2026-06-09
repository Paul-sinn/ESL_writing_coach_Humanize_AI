# Step 2: frontend-onboarding-errors

## 읽어야 할 파일

먼저 아래 파일들을 읽고 프로젝트의 아키텍처와 설계 의도를 파악하라:

- `harness/harness-framework-codex/AGENTS.md`
- `harness/harness-framework-codex/docs/PRD.md`
- `harness/harness-framework-codex/docs/ARCHITECTURE.md`
- `harness/harness-framework-codex/docs/ADR.md`
- `harness/harness-framework-codex/docs/UI_GUIDE.md`
- `frontend/src/App.jsx`
- `frontend/src/context/AuthContext.jsx`
- `frontend/src/lib/supabase.js`
- `frontend/src/styles.css`
- `frontend/package.json`

이전 step에서 생성/수정된 auth와 billing 계약을 먼저 읽고, frontend가 그 계약을 사용자에게 명확히 보여주도록 작업하라.

## 작업

1. Google/email 로그인 후 `/api/auth/me` 응답에서 `needs_onboarding`이 true인 경우 username onboarding UI가 확실히 열리는지 확인하고, 누락되어 있으면 보강한다.
2. onboarding 실패/계정삭제 실패/Polar 취소 실패 같은 서버 에러를 modal 또는 profile/account 영역에서 inline으로 표시한다.
3. UI copy는 username만 요구해야 하며 nickname을 언급하지 않는다.
4. UI_GUIDE를 따라 AI 슬롭성 장식 추가 없이 기존 작업형 UI 안에서 에러와 다음 행동을 명확히 보여준다.

## Acceptance Criteria

```bash
cd frontend && npm run build
```

가능하면 다음 정적 검증도 실행한다:

```bash
python -m py_compile backend/app/main.py
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. 아키텍처 체크리스트를 확인한다:
   - Supabase client는 `frontend/src/lib/supabase.js` 경계를 유지하는가?
   - API 호출은 기존 `fetchJson`/AuthContext 패턴과 일치하는가?
   - nickname 입력 또는 마케팅성 장식을 추가하지 않았는가?
3. 결과에 따라 `phases/auth-billing-stability/index.json`의 step 2를 업데이트한다:
   - 성공: `"status": "completed"`, `"summary": "Frontend reliably opens username onboarding and shows account/billing errors inline."`
   - 수정 3회 시도 후에도 실패: `"status": "error"`, `"error_message": "구체적 에러 내용"`
   - 사용자 개입 필요: `"status": "blocked"`, `"blocked_reason": "구체적 사유"` 후 즉시 중단

## 금지사항

- nickname 입력 필드를 추가하지 마라. 이유: 제품 onboarding 계약은 username만 요구한다.
- 보라/인디고 gradient text, glow, orb 장식을 추가하지 마라. 이유: UI_GUIDE의 AI 슬롭 금지 항목이다.
- 프론트엔드에서 Polar 또는 외부 결제 API를 직접 호출하지 마라. 이유: 결제/구독 상태 변경은 backend API 경계에서 처리해야 한다.
- `.env`를 읽지 마라. 이유: 루트 AGENTS 지시가 명시적으로 금지한다.
