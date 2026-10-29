# Alpha Performance — 프로젝트 컨텍스트

> claude.ai 프로젝트(Alpha Performance Project)와 Claude Code가 함께 쓰는 기준 문서입니다.

## 목표 (KPI)
| 기간 | 팔로워 | 구매 |
|---|---|---|
| 1개월 | 25,000 | 1건 (외부인) |
| 3개월 | 30,000 | 100건 |
| 6개월 | 50,000 | 1,000건 |

## 배경 / 범위
- 인스타그램 @alpha_football_rehab: 축구 스피드, 부상 재활, 코어·근력 운동. 유명 선수 훈련 해설과 코치 직접 시연. 팔로워 약 2만.
- 코치: 원우 (UDT 출신, 재활 전공, 전 헬스 트레이너, 도르트문트 거주, 현 U-20 대표 선수 1명 코칭, 쾰른 체대 석사 준비).
- 운영: 원우 님은 코칭·촬영·전문성, 친구(이 프로젝트 사용자)가 편집·업로드·판매·고객 응대 담당.
- 상품: 6주 스피드 프로그램 (24세션, 주 4회, 장비 불필요, PDF + 영상 링크), $20. 결제·PDF 전달은 Payhip (상품 코드 08O1t, PayPal 결제).
- 판매 페이지: https://alpha-performance.netlify.app/ (Netlify). 새 버전은 `site/index.html`.

## 기준 데이터 (2026-10-10 캡처, 최근 90일)
| 단계 | 수치 | 전환율 |
|---|---|---|
| 도달 → 프로필 방문 | 588,053 → 9,200 | 1.6% |
| 프로필 방문 → 팔로우 | 9,200 → 4,444 | 48% |
| 프로필 방문 → 링크 클릭 | 9,200 → 58 | 0.6% |
| 링크 클릭 → 구매 | 58 → 0 | - |
- 조회 80%, 반응 81%가 비팔로워. 스토리 90일 반응 303건.
- Hotjar (10/16 기준): 주간 세션 약 5회, LCP 1.68초, 이탈률 80%, 평균 세션 13분 25초(내부 접속 섞임 추정).
- 원우 님 시연 콘텐츠(Explosive Power 3.7만, Deceleration 3.6만)가 스타 콘텐츠(손흥민 3.3만)보다 높음.
- KPI 역산 (페이지 전환율 2% 가정): 3개월 100건에는 페이지 방문 약 5,000회(주 385회) 필요. 프로필 링크만으로는 불가능하므로 스토리·DM 직접 판매와 도달 확대 병행.

## 최근 30일 (10/29 캡처) — 자세한 분석은 `docs/insights/2026-10-29_instagram-30d.md`
- 팔로워 20,729 (+170), 조회 186,425, 조회한 사람 52,007, 프로필 방문 1,700 → 링크 클릭 0
- 팔로워: 남성 90%, 25-44세 70%, 브라질·이집트·미국·스페인·아르헨티나, 스페인어 21.8% · 영어 19.5%
- 팔로우 상위: 원우 님 시연 3개(+126/+55/+51) vs 스타 콘텐츠(+17)

## KPI 역산 ($20, 페이지 전환율 2% 가정)
| 목표 | 필요한 페이지 방문 | 주당 방문 |
|---|---|---|
| 1개월 1건 | 약 50 | 약 12 (현재 4.5) |
| 3개월 100건 | 약 5,000 | 약 385 |
| 6개월 1,000건 | 약 50,000 | 약 1,900 |
- 프로필 클릭률을 10%로 올려도 90일 920회, 약 18건. 스토리·DM 직접 판매와 도달 확대가 함께 필요.

## 확정 문구 (10/16)
**인스타그램 프로필**
- 이름: `Wonwoo | Football Speed & Rehab Coach`
- 소개글: `Ex-UDT · Rehab-trained football coach` / `Coaching a Korea U-20 international` / `Get faster in 6 weeks: 24 sessions, no gym ↓`
- 링크: 링크트리 1개

**링크트리**
- 제목: `Alpha Performance | Coach Wonwoo`
- 소개: `Ex-UDT · Rehab specialist · Coaching a U-20 international`
- 버튼: `⚡ 6-Week Speed Program ($20)`
- 주소: `https://alpha-performance.netlify.app/?utm_source=instagram&utm_medium=linktree&utm_campaign=bio`
- 스토리 링크 스티커: `https://alpha-performance.netlify.app/?utm_source=instagram&utm_medium=story&utm_campaign=<날짜>`

## 판매 페이지 추적 이벤트 (Hotjar Events)
- `buy_click_hero`, `buy_click_sticky`: 상단·하단 고정 구매 버튼
- `view_coach`, `view_pricing`: 코치 소개·가격 섹션 도달
- `paypal_click`: PayPal 결제 버튼 클릭
- `src_<utm_medium>`: 유입 경로 (예: `src_linktree`, `src_story`, `src_dm`, UTM 없으면 `src_direct`/`src_referral`)
- 퍼널: 세션 → view_pricing → paypal_click → PayPal 결제 완료
- 내부 접속 제외: 본인 기기에서 한 번 `?internal=1`로 열면 그 기기는 Hotjar에서 빠짐 (`?internal=0`으로 해제)

## 결정 기록
| 날짜 | 결정 | 출처(채팅/코드) |
|------|------|-----------------|
| 2026-10-10 | 자체 도메인은 첫 판매 후 구매, 그전까지 링크트리 무료 경유 (버튼 1개) | 채팅 |
| 2026-10-10 | "$99 → $20, 80% OFF" 상시 할인 표기 제거 | 채팅 |
| 2026-10-16 | 판매 페이지를 영어 단일 페이지로 새로 제작 (코치 경력, 6주 일정, FAQ, Hotjar 이벤트) | Claude Code |
| 2026-10-16 | 인스타 프로필·링크트리 문구 영어로 확정 (UTM: utm_source=instagram&utm_medium=linktree) | Claude Code |
| 2026-10-16 | 가격 $20, 결제 PayPal (AP_CONFIG.PAYPAL_URL) | 채팅 |
| 2026-10-28 | PayPal 링크가 비어 있으면 구매 버튼을 인스타 DM으로 연결 (DM 직접 판매) | Claude Code |
| 2026-10-28 | 환불 불가 (즉시 다운로드 상품). 가격 아래·FAQ·푸터에 표시, 파일 오류는 DM으로 재전송 | 사용자 |
| 2026-10-28 | 결제 링크를 Payhip 구매 링크로 설정 (`https://payhip.com/buy?s=1&cart_links%5B%5D=08O1t&qty%5B08O1t%5D=1`) | 사용자 |
| 2026-10-29 | 판매 페이지 주소를 `https://alpha-performance.netlify.app/`로 이전 (새 페이지 배포 완료). 예전 aquamarine-pika·grand-ganache는 새 주소로 이동 처리 | Claude Code |
| 2026-10-26 | 채팅 프로젝트와 Claude Code를 이 레포로 연동 | Claude Code |

## 확인 필요
- U-20 선수 관련 문구: 선수·보호자 동의
- 원우 님 사진 (`site/coach.jpg`)
- Hotjar Site ID (`site/index.html` 상단 AP_CONFIG)
