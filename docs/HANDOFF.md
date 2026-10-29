# 작업 인계 메모

최신 항목을 맨 위에 추가합니다.

## 2026-10-29 — Claude Code (새 페이지 배포 완료)
- 한 일: 새 판매 페이지를 Netlify `alpha-performance` 사이트에 배포 (사용자 확인). 문서의 판매 페이지 주소를 alpha-performance로 변경
- 다음 할 일: 예전 사이트 2곳에 이동 파일 배포 → 링크트리 버튼 주소 변경 → 인스타 프로필 링크 → ManyChat → 랜딩페이지 추가 수정(사용자 코멘트 예정)

## 2026-10-29 — Claude Code (Netlify 정리)
- 발견: Netlify(Alpha Team, kim wonwoo 계정)에 사이트 5개. 링크트리는 8/10 버전인 grand-ganache-11ea1c를 가리킴. aquamarine-pika는 9/13 예전 디자인, alpha-performance는 빈 사이트
- 결정(제안): 새 페이지를 `alpha-performance` 사이트에 배포 → `https://alpha-performance.netlify.app/`. 예전 사이트 두 곳(aquamarine, grand-ganache)에는 `redirect/index.html`을 올려 UTM을 유지한 채 새 주소로 넘김
- 다음 할 일: 배포 확인 후 링크트리·ManyChat·문서의 주소를 alpha-performance로 변경. Hotjar(Contentsquare) 코드는 어느 사이트에 있었는지 미확인

## 2026-10-29 — Claude Code (판매 동선 가이드)
- 한 일: `docs/playbooks/sales-funnel.md` 작성 (링크 복구 순서, ManyChat 댓글→DM 설정·문구, 스토리 판매 방법, 예약 업로드, 영어+스페인어 캡션 형식)
- 현재 상태: 사용자가 프로필 링크를 내린 상태 (링크 클릭 0의 원인)
- 다음 할 일: Hotjar ID 받기 → 새 페이지 Netlify 배포 → 링크트리·프로필 링크 연결 → ManyChat 설정 → 게시물별 영어·스페인어 캡션 작성 지원
- KPI 재설정은 보류 (사용자 결정)

## 2026-10-29 — Claude Code (인스타 30일 분석)
- 한 일: 인스타 인사이트 캡처 10장 분석 → `docs/insights/2026-10-29_instagram-30d.md`
- 핵심: 프로필 방문 1,700 → 링크 클릭 0 (링크 복구 최우선) / 팔로워 70%가 25~44세 해외 남성, 스페인어 21.8% > 영어 19.5% / 팔로우는 원우 님 시연이 만듦
- 다음 할 일: 링크 복구 → 댓글→DM 자동화 → 스토리 링크 스티커 → KPI 재설정 결정

## 2026-10-28 — Claude Code (랜딩페이지 1차 수정)
- 한 일 (`site/index.html`):
  - 유입 경로를 Hotjar 이벤트 `src_<utm_medium>`로 기록 (스토리·링크트리·DM 구분)
  - `?internal=1`로 연 기기는 Hotjar에서 제외 (평균 세션 13분에 섞인 내부 접속 문제)
  - PayPal 링크가 없으면 가격 버튼이 "DM to buy · $20"로 바뀌고 인스타 DM으로 연결
  - `netlify.toml` 추가: Netlify에 레포를 연결하면 `site` 폴더가 자동 배포됨
- 막힌 것: 이 클라우드 환경에서는 netlify.app에 접속할 수 없어 실제 배포된 페이지는 확인 못 함
- 추가: 환불 불가 문구 반영 (가격 아래, FAQ, 푸터)
- 추가: 결제 링크를 Payhip 구매 링크로 넣고 'PayPal' 문구를 Payhip 기준으로 수정 (이벤트 이름 paypal_click은 그대로)
- 다음 할 일: Hotjar ID·coach.jpg 받기 → Netlify 배포 → 프로필·링크트리 반영 → 1~2주 뒤 인사이트 분석

## 2026-10-28 — Claude Code (현재 할 일)
- 한 일: 10/16 현황 정리(확정 문구, Hotjar 수치, KPI 역산, 추적 이벤트)를 PROJECT_CONTEXT.md에 합침
- 지금 할 일 (사용자 지정):
  1. 비즈니스 계정 링크 수정 — 인스타 프로필·링크트리를 PROJECT_CONTEXT.md "확정 문구"대로 반영
  2. 랜딩페이지 수정 — `site/index.html` (PayPal 링크, Hotjar ID, coach.jpg, 환불 정책, 그 외 수정 사항)
  3. 방문자 인사이트 분석 — 인스타 인사이트('공개 대상' 탭 포함)와 Hotjar 최신 수치로 분석

## 2026-10-28 — Claude Code (세션 "비즈니스 계정 및 랜딩페이지 수정")
- 한 일: 이 세션의 대화 전체(10/16~10/28)를 `docs/conversations/2026-10-16_business-account-landing-page.md`로 옮김. 도구 실행 과정은 빼고 사용자 메시지·Claude 답변·선택한 답변만 남김.
- 이어서 작업할 때: Claude Code에서 "docs/conversations의 대화 기록과 HANDOFF.md를 읽고 이어서 하자"라고 시작하면 됨.
- 다음 할 일: 10/26 항목의 다음 할 일 그대로

## 2026-10-28 — Claude Code
- 한 일: claude.ai Alpha Performance Project 컨텍스트에 이 레포(claude/practical-cray-ezhcif 브랜치) 추가 완료
- 참고: 프로젝트 쪽은 자동 반영이 아니므로, 레포 변경 후 프로젝트 컨텍스트에서 alphaperformance 항목을 동기화해야 최신 내용이 보임
- 다음 할 일: 아래 10/26 항목의 다음 할 일 그대로

## 2026-10-26 — Claude Code
- 한 일: 10/16에 만든 판매 페이지를 `site/index.html`로 레포에 추가. 프로젝트 목표·배경·기준 데이터·결정 기록을 PROJECT_CONTEXT.md에 정리.
- 다음 할 일:
  1. `site/index.html` 상단 AP_CONFIG에 PayPal 링크와 Hotjar ID 입력, `site/coach.jpg` 추가
  2. Netlify에 `site` 폴더 배포 (가능하면 이 레포를 Netlify에 연결해 자동 배포)
  3. 인스타 '공개 대상' 탭 캡처로 타깃(언어·결제자) 재확인

## 2026-10-26 — Claude Code
- 한 일: 연동용 기본 문서(CLAUDE.md, docs/PROJECT_CONTEXT.md, docs/HANDOFF.md) 생성
