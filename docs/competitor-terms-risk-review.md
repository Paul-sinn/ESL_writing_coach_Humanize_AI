# 경쟁사 약관 참고 보고서

참고 대상: HumaLingo Terms and Conditions  
URL: https://www.humalingo.com/terms-and-conditions  
작성 목적: EssayCoach 약관/안전장치 보강 포인트 정리  

> 참고: 이 문서는 법률 자문이 아니라, 경쟁사 약관 구조를 참고한 제품/운영 리스크 점검 보고서입니다. 실제 출시 전에는 변호사 또는 관련 전문가 검토가 필요합니다.

---

## 한 줄 결론

EssayCoach는 **AI detector / 학업 제재 리스크 방어 문구는 이미 꽤 잘 되어 있음**.  
하지만 HumaLingo처럼 **구독, 결제, 환불, 계정 삭제, 서비스 장애, 사용자 책임** 쪽 문구를 더 단단히 해야 함.

---

## HumaLingo가 강하게 걸어둔 안전장치

HumaLingo 약관에서 참고할 만한 핵심 방어 구조는 아래와 같음.

### 1. 전문적 조언 아님

서비스 결과를 전문적 조언, 확정적 판단, 보장된 결과로 보지 말라고 명시함.

우리 서비스에 적용하면:

- EssayCoach는 글쓰기 보조 도구임
- 공식 학업 판단이나 AI detector 판정 도구가 아님
- 결과는 참고용이며 최종 판단은 사용자 책임

---

### 2. 결과 보장 안 함

HumaLingo는 서비스가 항상 정확하거나 특정 결과를 보장하지 않는다는 구조를 둠.

우리 서비스에 적용하면:

- Turnitin, GPTZero, ZeroGPT 등 특정 점수 보장 안 함
- AI-likeness 점수는 참고용 추정치임
- 학교/교수/플랫폼별 판단 결과가 다를 수 있음

---

### 3. 구독 자동갱신/취소 규칙 명확

HumaLingo는 구독이 취소 전까지 자동 갱신된다고 분명히 말함.

우리 서비스에 필요한 문구:

- 구독은 매월 자동 갱신됨
- 사용자가 취소하기 전까지 결제가 계속됨
- 취소해도 현재 결제 기간 끝까지 이용 가능
- 가격 변경 가능성이 있고, 변경 시 사전 고지

---

### 4. 계정 삭제와 구독 취소를 분리

HumaLingo 약관에서 특히 중요한 부분:

> 계정을 삭제해도 구독이 자동으로 취소되는 것은 아님.

우리 서비스도 Polar 결제와 계정 삭제가 분리될 수 있으므로 반드시 필요함.

쉽게 말하면:

> 계정 삭제 버튼과 구독 취소 버튼은 다른 버튼이다.

---

### 5. 환불 제한

디지털 서비스는 제공되면 환불이 제한된다는 구조를 둠.

우리 서비스에 적용하면:

- 요청이 처리되어 결과가 생성되면 크레딧은 차감됨
- AI detection 결과가 마음에 들지 않는다는 이유만으로 환불 불가
- 기술 오류로 결과가 생성되지 않은 경우는 별도 검토 가능

---

### 6. 서비스 중단/오류 면책

HumaLingo는 서비스가 항상 끊김 없이 작동한다고 보장하지 않음.

우리 서비스에 필요한 문구:

- 서버 점검, 오류, 업데이트, 외부 API 장애 가능
- OpenAI, Supabase, Polar, Vercel 등 외부 서비스 장애 가능
- 일시적 접속 불가나 처리 실패가 발생할 수 있음

---

## EssayCoach에 이미 잘 들어가 있는 것

현재 `frontend/public/terms.html` 기준으로 좋은 문구들이 이미 있음.

### 이미 있는 좋은 방어 문구

1. **AI detector bypass 서비스가 아님**
   - “EssayCoach is a writing assistance tool — not an AI detector bypass service.”

2. **Turnitin/GPTZero 결과 보장 안 함**
   - 특정 AI detection score를 보장하지 않는다고 명시되어 있음.

3. **학교/직장 정책 준수는 사용자 책임**
   - 사용자가 자기 학교, 직장, 플랫폼 정책을 확인해야 한다고 되어 있음.

4. **출력물 검토 책임**
   - 결과물을 사용자가 직접 검토, 수정, 확인해야 한다고 되어 있음.

5. **AI 모델 학습에 사용하지 않는다는 문구**
   - “Your writing is never used to train AI models.”

6. **크레딧 환불 제한**
   - 요청 처리 후 크레딧은 일반적으로 환불되지 않는다고 되어 있음.

7. **남용 계정 제한 가능**
   - scraping, 자동 요청, 과도한 사용 시 계정 제한 가능.

---

## EssayCoach에 추가하면 좋은 것들

## 1. 운영자 정보 / 약관 적용 범위

현재 약관에는 EssayCoach 이름은 있지만, 실제 운영 주체 정보가 약함.

추가하면 좋은 내용:

- 운영자 또는 회사명
- 연락 이메일
- 약관이 웹사이트, 웹앱, API, 결제, 크레딧, 계정 기능에 모두 적용된다는 문구

예시 방향:

```text
These Terms govern your access to and use of EssayCoach, including our website, web app, APIs, paid plans, credits, and related services.
```

---

## 2. 구독 자동갱신 문구

유료 구독이 있으므로 꼭 필요함.

추가할 내용:

- 구독은 자동 갱신됨
- 취소 전까지 계속 청구됨
- 취소 후에도 현재 결제 기간 끝까지 이용 가능
- 가격은 변경될 수 있음
- 가격 변경 시 사전 고지

쉬운 표현:

```text
If you purchase a subscription, it will automatically renew each billing period unless you cancel before the renewal date.
```

---

## 3. 계정 삭제 ≠ 구독 취소

매우 중요함.

사용자가 계정을 삭제했는데 결제가 계속되면 큰 컴플레인으로 이어질 수 있음.

추가 추천 문구:

```text
Deleting your account does not automatically cancel an active subscription. To stop future billing, you must cancel your subscription through the billing portal or by contacting support.
```

한국어 의미:

> 계정 삭제는 구독 취소가 아니다.  
> 돈이 더 안 나가게 하려면 구독도 따로 취소해야 한다.

---

## 4. 결제/환불/크레딧 규칙 상세화

현재 환불 제한 문구는 있지만 더 구체화하면 좋음.

추가할 내용:

- 크레딧은 요청이 성공적으로 처리되면 차감됨
- 결과가 생성되지 않은 기술 오류는 검토 가능
- AI detector 결과 불만족은 환불 사유 아님
- 구독 크레딧이 이월되지 않는다면 명시
- 세금, 수수료, 환율, 결제 대행사 정책 가능성 명시

---

## 5. 서비스 오류/중단 면책

출시 후 가장 흔한 컴플레인 중 하나가 “왜 안 돼요?”임.

추가할 내용:

- 서비스가 항상 100% 작동한다고 보장하지 않음
- 점검/업데이트/장애 가능
- 외부 서비스 장애 가능
- 데이터 처리 지연 가능

예시 방향:

```text
We do not guarantee that the Service will be uninterrupted, error-free, or available at all times.
```

---

## 6. 사용자 콘텐츠 권리/허가 문구

사용자가 에세이를 붙여넣기 때문에 필요함.

추가할 내용:

- 사용자는 업로드한 글을 제출할 권리가 있어야 함
- 타인의 개인정보, 저작권 침해물, 불법 콘텐츠를 넣으면 안 됨
- 사용자는 EssayCoach가 결과 생성을 위해 텍스트를 처리하도록 제한적 권한을 줌
- 사용자는 자기 원문 소유권을 유지함

---

## 7. 금지 사용 더 구체화

현재 남용 방지 문구가 있지만 더 구체화하면 좋음.

추가 금지 예시:

- 불법 목적 사용
- 학교/시험/입학/취업 정책 위반 목적 사용
- AI detector 우회 보장처럼 홍보하거나 재판매
- 자동화 scraping
- 시스템 과부하
- 타인 계정 사용
- 결제 사기
- 악의적 chargeback abuse

---

## 빼거나 조심해야 할 것들

## 1. “완전 면책”처럼 보이는 표현은 조심

현재 약관에는 이런 방향의 문구가 있음:

```text
EssayCoach is not liable for any academic, professional, or legal consequences...
```

방향은 좋지만, 너무 절대적으로 쓰면 관할에 따라 약할 수 있음.

더 안전한 표현:

```text
To the maximum extent permitted by law, EssayCoach is not responsible for...
```

한국어 의미:

> 법이 허용하는 최대 범위에서만 책임을 제한한다.

---

## 2. Binding arbitration / class action waiver는 조심

현재 약관에 중재/집단소송 포기 문구가 있음.

이 문구는 미국 서비스에서 흔하지만, 잘못 쓰면 오히려 위험할 수 있음.

조심해야 하는 이유:

- 회사 소재지가 명확하지 않음
- 미성년자 사용 가능성 있음
- 해외 사용자 가능성 있음
- 소비자 보호법 이슈 가능

추천:

- 변호사 검토 전에는 약하게 두거나 제거 후보로 보기
- 유지하려면 회사 소재지, 관할, 예외, opt-out 방식 등을 정확히 정리해야 함

---

## 3. “Your writing is never used to train AI models” 표현은 실제 처리 방식과 맞춰야 함

마케팅상 좋은 문구지만 매우 강한 약속임.

현재 표현:

```text
Your writing is never used to train AI models.
```

더 안전한 표현:

```text
We do not use your submitted writing to train our own AI models. Third-party processors handle submitted text according to their own data processing terms.
```

이유:

- 우리는 학습에 안 쓴다고 말할 수 있음
- 하지만 OpenAI 같은 제3자 처리 조건과 충돌하지 않게 해야 함

---

## 4. “not stored after results are returned”도 실제 시스템과 맞아야 함

Privacy 페이지에 텍스트가 결과 반환 후 저장되지 않는다는 표현이 있음.

만약 서버 로그, 오류 로그, 분석 로그, OpenAI 처리 기록 등에 일부라도 남을 수 있으면 위험함.

더 안전한 표현:

```text
We do not intentionally store submitted writing as user content after processing, except where temporary processing, security, debugging, abuse prevention, or legal compliance requires it.
```

한국어 의미:

> 우리는 원칙적으로 글을 저장하지 않지만, 보안/오류처리/법적 의무 때문에 임시 처리나 기록이 필요할 수 있다.

---

## 우선순위

## 바로 추가 추천 TOP 5

1. **구독 자동갱신/취소 규칙**
2. **계정 삭제와 구독 취소는 다르다는 문구**
3. **서비스 중단/오류/외부 API 장애 면책**
4. **사용자 콘텐츠 권리 및 처리 허가**
5. **“법이 허용하는 범위에서” 면책 표현 추가**

---

## 수정/완화 추천 TOP 3

1. **“never used to train AI models” 표현 완화**
2. **“not stored after results are returned” 표현 완화**
3. **arbitration/class action waiver는 변호사 검토 전까지 조심**

---

## 최종 판단

EssayCoach 약관은 **AI detector / 학업 리스크 방어는 이미 꽤 좋음**.

하지만 출시 전에는 아래 영역을 보강해야 함:

- 구독 자동갱신
- 결제 취소
- 환불 제한
- 계정 삭제와 구독 취소 분리
- 서비스 장애 면책
- 사용자 콘텐츠 권리
- 개인정보/텍스트 저장 표현 정확화

특히 유료 크레딧/구독이 있는 서비스이므로, **결제 관련 약관 보강이 1순위**임.

---

## 추천 다음 작업

1. `frontend/public/terms.html`에 결제/구독/계정삭제 문구 추가
2. `frontend/public/privacy.html`의 “never train / not stored” 표현을 실제 시스템과 맞게 완화
3. Help Center의 환불/구독 취소 FAQ를 약관과 같은 표현으로 맞춤
4. 약관 마지막에 실제 support/privacy 이메일과 운영자 정보를 정리
5. 출시 전 법률 전문가에게 최종 검토 요청

---

## 추가 의견: “교육 및 오락 목적” 강하게 명시하기

사용자는 실제로 TOS를 거의 읽지 않기 때문에, 약관에는 방어 문구를 조금 더 강하게 넣는 것이 좋음.

특히 EssayCoach는 아래 영역과 연결될 수 있음:

- 학교 과제
- AI detector 결과
- 학업 제재
- 입학/취업용 글
- 유료 결제
- 사용자 제출 글

따라서 TOS에는 서비스 성격을 강하게 제한하는 문구가 필요함.

---

## 추천 강한 문구

아래 문구를 `frontend/public/terms.html`의 **What This Service Is** 섹션 초반에 추가하는 것을 추천.

```text
EssayCoach is provided for educational, informational, entertainment, and writing-assistance purposes only. EssayCoach does not provide professional, legal, academic, disciplinary, admissions, employment, or institutional advice or decisions. Any scores, feedback, rewrites, suggestions, or AI-likeness estimates are non-binding, informational outputs only and must not be relied upon as guaranteed, official, or definitive results.
```

한국어 의미:

> EssayCoach는 교육, 정보 제공, 오락, 글쓰기 보조 목적의 서비스일 뿐이다.  
> 전문적/법률적/학업적/징계적/입학/취업/기관 판단을 제공하지 않는다.  
> 점수, 피드백, 재작성, 제안, AI 유사도 추정치는 공식적이거나 확정적인 결과가 아니며 보장되지 않는다.

---

## 추가 책임 제한 문구

위 문구와 함께 아래 문구도 넣는 것을 추천.

```text
You use EssayCoach at your own risk. You are solely responsible for reviewing, editing, verifying, and deciding whether and how to use any output generated by the Service.
```

한국어 의미:

> 사용자는 EssayCoach를 본인 책임으로 사용한다.  
> 결과물을 검토하고, 수정하고, 확인하고, 사용할지 말지는 전적으로 사용자 책임이다.

---

## 더 강한 면책 문구

현재 약관에도 학업/직업/법적 결과에 대한 책임 제한 문구가 있지만, 아래처럼 더 넓게 정리하면 좋음.

```text
To the maximum extent permitted by law, EssayCoach is not responsible for any academic, professional, legal, disciplinary, admissions, employment, financial, or personal consequences arising from your use of or reliance on the Service.
```

한국어 의미:

> 법이 허용하는 최대 범위에서 EssayCoach는 사용자가 서비스를 사용하거나 결과를 믿고 행동해서 생긴 학업, 직업, 법률, 징계, 입학, 취업, 금전, 개인적 결과에 책임지지 않는다.

---

## 너무 과한 표현은 피하기

아래처럼 쓰는 것은 비추천.

```text
We are never responsible for anything under any circumstances.
```

이유:

- 법적으로 무효가 될 수 있음
- 사용자 신뢰도가 떨어질 수 있음
- 결제 서비스에서 너무 무책임하게 보일 수 있음

대신 항상 아래 표현을 붙이는 것이 좋음:

```text
To the maximum extent permitted by law
```

---

## TOS와 앱 UI 표현 분리 추천

약관에는 강하게 써도 됨.

하지만 랜딩 페이지나 앱 내부에는 너무 무섭게 쓰면 전환율이 떨어질 수 있음.

### TOS 문구

강하게:

```text
educational, informational, entertainment, and writing-assistance purposes only
```

### 앱 UI 문구

짧고 신뢰감 있게:

```text
Educational writing assistance only. No detection result is guaranteed.
```

한국어 의미:

> 교육용 글쓰기 보조 도구입니다. AI detection 결과는 보장되지 않습니다.

---

## 이 문구를 넣어야 하는 이유

이 문구는 아래 컴플레인 방어에 도움됨:

1. “이거 썼는데 Turnitin에서 걸렸어요.”
2. “AI score가 낮다고 했는데 학교에서 문제 삼았어요.”
3. “Humanize 했는데 결과가 마음에 안 들어요.”
4. “이걸 믿고 제출했는데 점수가 안 나왔어요.”
5. “이거 전문적인 학업 조언 아니었나요?”
6. “입학/취업 글에 썼는데 결과가 안 좋았어요.”

즉, EssayCoach는 **결과 보장 서비스가 아니라 교육/정보/오락/글쓰기 보조 도구**라는 점을 명확히 해야 함.
