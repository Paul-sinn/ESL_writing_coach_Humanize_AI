이 프로젝트의 변경 사항을 리뷰하라.

## Codex 전용 가드레일

- 이 저장소의 에이전트 규칙 파일은 `AGENTS.md`다. `CLAUDE.md`를 만들거나 참조하지 마라.
- 명령 문서는 `.codex/commands/` 아래에 둔다. `.claude/` 디렉토리나 `.claude/commands/` 파일을 만들거나 참조하지 마라.
- 리뷰 규칙의 단일 원본은 이 파일이다. 별도의 `docs/CODEX_REVIEW.md`를 만들지 마라.
- 하네스 규칙의 단일 원본은 `.codex/commands/harness.md`다. 별도의 `docs/CODEX_HARNESS.md`를 만들지 마라.

먼저 다음 문서들을 읽어라:

- `/harness/harness-framework-codex//AGENTS.md`
- `/harness/harness-framework-codex//docs/ARCHITECTURE.md`
- `/harness/harness-framework-codex/docs/ADR.md`

그런 다음 변경된 파일들을 확인하고, 아래 체크리스트로 검증하라:

## 체크리스트

1. **아키텍처 준수**: ARCHITECTURE.md에 정의된 디렉토리 구조를 따르고 있는가?
2. **기술 스택 준수**: ADR에 정의된 기술 선택을 벗어나지 않았는가?
3. **테스트 존재**: 새로운 기능에 대한 테스트가 작성되어 있는가?
4. **CRITICAL 규칙**: AGENTS.md의 CRITICAL 규칙을 위반하지 않았는가?
5. **빌드 가능**: 빌드 명령어가 에러 없이 통과하는가?

## 출력 형식

| 항목 | 결과 | 비고 |
|------|------|------|
| 아키텍처 준수 | OK/FAIL | {상세} |
| 기술 스택 준수 | OK/FAIL | {상세} |
| 테스트 존재 | OK/FAIL | {상세} |
| CRITICAL 규칙 | OK/FAIL | {상세} |
| 빌드 가능 | OK/FAIL | {상세} |

위반 사항이 있으면 수정 방안을 구체적으로 제시하라.
