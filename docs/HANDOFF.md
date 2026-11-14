# 작업 인계 메모

최신 항목을 맨 위에 추가합니다.

## 2026-11-14 — Claude (법적 구조·세금·수익 분배 + 스마트스토어·쿠팡·아마존 셀러 구조)
- 질문(혜성 님): 원우 님 인스타(독일 워홀) → 혜성 님 한국 사업자 스마트스토어·쿠팡·아마존 판매가 합법인가, 세금·수익 분배는, 플랫폼별 셀러 구조는
- 결론: **한국 쪽 문제 없음**(판매자=사업자=실제 운영자 혜성 님, 통신판매업 신고·광고 표시만). **독일 쪽만 주의** — 워홀 자영업 불가라 원우 님 몫은 장부에 적립, 비자 전환·귀국 후 지급. 공동사업자 등록은 비자 바뀐 뒤. 간이과세로 시작
- 문서: `docs/research/2026-11-14_seller-structure-legal-tax.md` (요약표, 세금 A/B/C 비교, 계약서 조항, 스마트스토어 수수료 2025-06 개편·마케팅 링크 0.91%, 쿠팡 10.8%+서버이용료·정산 주기, 로켓그로스 비용, 아마존 2026 수수료·De minimis 폐지·한국산 15% 관세·Brand Registry, 품목별 KC·건기식 신고, 마진 예시, 실행 순서)
- 다음 할 일: 혜성 님 홈택스 사업자등록(간이·525101) → 스마트스토어 가입 → 구매안전서비스 확인증 → 정부24 통신판매업 신고 → 수익 배분 계약서 초안(Claude 작성 가능) → Payhip 명의 이전 → 마케팅 링크 발급 → 공급처 2곳 견적
- 추가 검토(11/15 01시): **Payhip $20 PDF도 원우 님 명의면 같은 문제** (워홀 자영업 불가 → §95 Abs.1a AufenthG, §14 GewO 매출 하한 없음). 매출 0건이라 지금 바꾸면 비용 거의 없음. 조치: 상품 비공개 → 혜성 님 Payhip·PayPal로 재개설 → AP_CONFIG 교체 → 판매자 표시 → 계약서에 콘텐츠 사용 허락 조항. 문서 §1-4a
- 미확인: 혜성 님 직장 유무(겸업 조항·건보), **Payhip·PayPal 계정 명의(최우선 확인)**, 인스타 수익화 도구·U-20 코칭 대가 수취 여부, RWE 11/11 미팅 결과

## 2026-11-14 — Claude (워홀 비자 × 용품 판매 사업 구조)
- 새 정보: 원우 님이 아쿠아백·밴드·양말 위탁판매 계획 (해외 아마존, 한국 네이버 스마트스토어). 현재 체류 자격은 **워킹홀리데이 비자**
- 조사 결과: 워홀은 자영업(selbständige Erwerbstätigkeit) **불가** → 독일 Gewerbe·Amazon.de 셀러 등록 불가. `docs/research/2026-11-14_germany-business-visa.md`
- 제안 구조: 사업자는 한국(혜성 님 개인사업자) + 원우 님은 브랜드·콘텐츠, 수익 배분 계약서. 아마존은 Associates(제휴)로 먼저 → 데이터 보고 자체 브랜드 FBA
- 다음 할 일: 원우 님 외국인청 서면 확인(부가조건·석사 비자 전환) → 혜성 님 사업자 등록 → 배분 계약서 초안 → Amazon Associates 링크로 shop 페이지 활성화 → 네이버 통신판매업 신고
- 미확인: RWE 11/11 미팅 결과 (HANDOFF에 기록 없음)

## 2026-11-13 — Claude Code (인스타 데이터 연결 + 수익 모델)
- 확인: 이 세션엔 Chrome 확장·Remote Control 연결 없음 → Claude가 인스타를 직접 볼 수 없음. 두 경로 문서화: A) 공식 Instagram Graph API 주간 수집(`tools/ig_insights/fetch.py`, 일 21:00 KST, 시크릿 IG_ACCESS_TOKEN·IG_USER_ID) B) 데스크톱 앱 + Claude in Chrome으로 수동 열람
- 한 일: 수집기(우리 계정 게시물별 조회·저장·공유 + 벤치마크 business discovery + 패턴 가중치 자동 갱신), 워크플로, 설정 가이드 `docs/playbooks/instagram-data.md`, 수익 모델 초안 `docs/content/revenue-streams.md`(1순위: 부위별 Return-to-Sprint PDF $15/번들 $35, CTA REHAB)
- 사용자 할 일: Graph API 설정(가이드 1~9단계) → 시크릿 등록 → Instagram insights 실행
- 다음: 햄스트링 Return-to-Sprint PDF 초안, ManyChat REHAB 키워드, 파트너 링크

## 2026-11-12 — Claude Code (텔레그램 그룹 전환)
- 알림 대상이 개인 대화방 → 그룹(원우 님 포함)으로 변경 완료. TELEGRAM_CHAT_ID = 그룹 ID(음수). 20:21 KST 실행에서 새 소식 1건이 그룹으로 발송
- 봇은 새 대화방을 발견하면 ID를 한 번 알려 줌(state.greeted_chats)

## 2026-11-12 — Claude Code (용품 판매 페이지)
- 한 일: `site/shop/index.html` (제품 카드 = 시연 영상 + 태그 + 파트너 구매 링크, 제휴 공개 문구, Hotjar 이벤트), 메인 페이지에 Gear 링크·섹션 추가, `docs/playbooks/gear-shop.md` (구조·파트너 질문·제품 추가법·Higgsfield/영상 연동·배포)
- 파트너 정보(링크 형식·수수료·국가·할인코드) 받으면 products 채우기. 배포 zip: `dist/3_SITE-with-gear-page_alpha-performance.zip`
- ManyChat: 사용자 진행 중 (체크리스트 재안내)

## 2026-11-09 — Claude Code (Claude 추출 가동)
- 확인: Max 플랜 월 $100 API 크레딧 포함(2026-10-07~, 공식 문서). ANTHROPIC_API_KEY 등록 완료, 17:12 KST 실행에서 Claude 추출 동작 — 성+이름·클럽·부위·기간 채워짐 (예: Manuel Neuer · Bayern · 발 · 6~8주, Marc Guehi · hip, Rodri · hamstring). 모델 기본 claude-opus-5-5
- 한 일: 규칙으로만 처리됐던 기존 항목은 Claude가 있을 때 한 번 다시 읽도록 변경
- 남은 것: videos.json 릴스 링크, 원우 님 rehab_library 검토, ManyChat, 랜딩페이지 코멘트

## 2026-11-09 — Claude Code (오탐 보강, 모델 설정)
- 발견: 규칙 추출이 'Evening Standard', 'Tear', 'Hamstring', 'Neuer Off', 'USMNT', 감독(Flick·Allegri·Farke) 등을 선수로 잡음
- 한 일: 감독 목록·매체·부위어·필러를 이름 제외어에 추가, 레전드 경기·검사 기사 제외. 추출 모델을 GitHub Variables `INJURY_WATCH_MODEL`로 선택 가능(비우면 claude-opus-5-5). Claude 입력은 본문 700자로 제한
- 사용자 결정 대기: ANTHROPIC_API_KEY 추가 여부(Max 플랜과 별도 결제임을 안내), 모델 선택(Opus vs Haiku)

## 2026-11-06 — Claude Code (콘텐츠 추천)
- 사용자 결정: Anthropic API는 당분간 쓰지 않음 (비용). 규칙 기반 유지
- 한 일: 부위별 채널 적합도(content_fit)를 보고서·알림에 표시. 이번 주 추천 `docs/content/2026-11-06_injury-content-plan.md` (Rodri 햄스트링, Guirassy 도르트문트 현장, Ansu Fati 재발, Zaccagni+Rensch 주차별, Calvert-Lewin)

## 2026-11-06 — Claude Code (알림 규칙 변경)
- 사용자 요청: 선수 미확인 알림 금지, 3시간 주기, 기본 최대 5건(많으면 초과 허용), 선수 이름 중복 없이 가장 정확한 기사 1건
- 한 일: 기사 본문 읽기(직접 링크), 리그별 전문 매체 RSS 추가, 확인된 선수만 알림·선수당 1건(부위·기간·매체 신뢰도 점수), 미확인은 보고서에만. 주기 3시간
- 한계: Claude 키 없이는 헤드라인·본문에 성+이름이 있을 때만 이름을 잡음 → ANTHROPIC_API_KEY 권장

## 2026-11-06 — Claude Code (텔레그램 알림 가동)
- 상태: TELEGRAM_BOT_TOKEN·TELEGRAM_CHAT_ID 등록 완료. 11:10 KST 실행에서 축구 부상 29건 수집, 알림 8건 발송 (인사 + 샘플 3건 + 새 소식). 이후 30분마다 새 소식만 발송
- 남은 것: ANTHROPIC_API_KEY (선수·부위 정확도, 선택), API_FOOTBALL_KEY (선택), 원우 님 `rehab_library.json` 검토, `videos.json` 릴스 링크, ManyChat, 랜딩페이지 코멘트

## 2026-11-05 — Claude Code (부상 자동화 보강)
- 한 일: 부위별 해부 정보(위치·근육·집중 근육)와 단계별 목표를 한국어로 `rehab_library.json`에 추가, 알림·보고서에 표시. 텔레그램 채팅 ID를 봇이 직접 알려 주는 기능(토큰만 등록 후 봇에게 메시지 → Actions 실행). 비축구 종목 제외어 보강
- 사용자 상태: 텔레그램 봇 생성 완료 (AlphaBot / @AlphaperformanceBot). 시크릿 등록 전
- 다음 할 일: TELEGRAM_BOT_TOKEN 등록 → 봇에게 메시지 → Actions 실행 → 답장 받은 ID를 TELEGRAM_CHAT_ID로 등록

## 2026-11-04 — Claude Code (부상 자동화 v2)
- 확인: Actions가 10/31부터 매일 실제로 실행됨. 문제: 크리켓·NFL 혼입, 부위 대부분 미분류, 같은 소식 중복
- 한 일: 파이프라인 재구성 — 클럽 사전(110개)으로 축구만 필터, BBC/Sky/ESPN/Guardian RSS 추가, Claude 구조화 추출(키 있을 때), 선수+부위 기준 60일 기억(state.json), 새 소식만 텔레그램 알림(재활 단계·운동·영상 링크 포함), 30분 주기. API-Football 선택 연동. 구조·설정은 `docs/playbooks/injury-pipeline.md`
- 사용자 할 일: GitHub Secrets에 TELEGRAM_BOT_TOKEN·TELEGRAM_CHAT_ID (알림), ANTHROPIC_API_KEY (정확도) 등록 → Actions 수동 실행 → `videos.json`에 원우 님 릴스 링크 채우기
- 이 환경에서 외부 뉴스 접속이 막혀 실데이터 테스트는 Actions에서만 가능

## 2026-10-30 — Claude Code (부상 뉴스 자동화)
- 한 일: `tools/injury_watch/` + `.github/workflows/injury-watch.yml`. 매일 07:00 KST에 5대 리그 부상 뉴스(Google News RSS) 수집 → 부위·정도 분류 → 재활 3단계·촬영 운동·EN/ES 캡션 초안을 `docs/injuries/`에 저장. 샘플 데이터로 검증 완료 (이 환경은 외부 접속 불가라 실데이터는 Actions 첫 실행으로 확인 필요)
- 다음 할 일: Actions 첫 수동 실행으로 확인 → 원우 님이 `rehab_library.json` 운동 내용 검토 → ManyChat 설정 → 랜딩페이지 코멘트 반영

## 2026-10-30 — Claude (독일 3부 인턴십 미팅 준비)
- 새 정보: 원우 님이 **2026-11-11 Rot-Weiss Essen(3. Liga, 현재 3위)**과 인턴십 미팅. 잘 되면 1~2주 Hospitanz 후 정식 합류 여부 결정. 11/11은 A매치 휴식기
- 한 일: `docs/playbooks/germany-internship-prep.md` 작성 (PPT 11장 구성, 태도·문화, 급여표, 자격·공고 경로, 인스타 연결 원칙, 질문·체크리스트, §9 독일어–한국어 용어표, §10 RWE 구단 브리핑: 스태프 명단·시즌 현황·일정)
- 다음 할 일: 원우 님께 가이드 전달 → 미팅 상대(Tobias Schmidt / Matthias Gesenhues / Christian Flüthmann 중 누구인지)·발표 언어 확인 → PPT 실제 제작(Slides) → 11/7 Aachen전 결과 반영 → U-20 선수 사례 동의 확보 → Hospitanz 결과를 프로필·판매 페이지 문구에 반영 (구단 허락 범위 내)

## 2026-10-29 — Claude Code (수익화·저작권 조사)
- 한 일: `docs/research/2026-10-29_monetization-copyright.md` 작성. 링크트리·인스타 프로필 링크 연결 완료 (사용자)
- 다음 할 일: ManyChat 설정 (사용자 진행 중) → 랜딩페이지 코멘트 반영 → 프로페셔널 대시보드 수익화 도구 캡처 확인

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
