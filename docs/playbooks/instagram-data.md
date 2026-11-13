# 인스타그램 데이터 연결 — Claude가 직접 보는 방법 2가지 (2026-11-13)

## 방법 A. 공식 API로 매주 자동 수집 (권장, 무료, 계정 안전)
Instagram Graph API는 Meta가 공식 제공하는 통로다. **우리 계정의 조회·저장·공유·팔로우 증가**와, **벤치마크 계정(프로페셔널 계정이면 누구나)의 팔로워·최근 게시물 좋아요/댓글**을 가져올 수 있다. 남의 릴스 조회수는 공식 API로는 안 나오고 좋아요+댓글로 대신한다.

### 한 번만 하는 설정 (PC, 30~40분)
1. **Facebook 페이지**가 필요하다. 없으면 facebook.com → 페이지 만들기(이름: Alpha Performance). 비공개로 둬도 된다.
2. **인스타 계정을 페이지에 연결**: 인스타 앱 → 설정 → 비즈니스/크리에이터 도구 → Facebook 페이지 연결 → 1번 페이지 선택. (계정은 이미 프로페셔널이므로 전환 불필요)
3. **Meta 개발자 앱**: developers.facebook.com → 내 앱 → 앱 만들기 → 유형 "비즈니스" → 이름 `alpha-performance-insights`.
4. 앱 대시보드에서 **Instagram Graph API** 제품 추가.
5. **토큰 발급**: developers.facebook.com/tools/explorer → 위에서 만든 앱 선택 → 권한에 `instagram_basic`, `instagram_manage_insights`, `pages_show_list`, `pages_read_engagement`, `business_management` 추가 → Generate Access Token → 로그인·허용.
6. 같은 화면에서 `me/accounts?fields=instagram_business_account,name` 실행 → 결과의 `instagram_business_account.id` 숫자가 **IG_USER_ID**.
7. 토큰은 1시간짜리다. **장기 토큰(60일)** 으로 바꾸기: 브라우저 주소창에
   `https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id=앱ID&client_secret=앱시크릿&fb_exchange_token=짧은토큰`
   (앱ID·시크릿은 앱 설정 → 기본 설정). 결과의 `access_token`이 **IG_ACCESS_TOKEN**.
   - 60일마다 갱신이 귀찮으면: business.facebook.com → 비즈니스 설정 → 사용자 → **시스템 사용자** 생성 → 앱·페이지 자산 할당 → 토큰 생성(만료 없음). 이쪽을 권장.
8. GitHub → Settings → Secrets → Actions에 `IG_ACCESS_TOKEN`, `IG_USER_ID` 등록.
9. Actions → **Instagram insights** → Run workflow. `docs/insights/ig/latest.md`에 우리 계정 표와 벤치마크 표가 생기면 성공.

막히는 화면은 캡처해서 Claude Code에 보내면 그 화면 기준으로 안내한다.

### 매주 자동으로 일어나는 일
- 일요일 21:00 KST: 데이터 수집 → 패턴별 성과 계산 → `benchmarks.json` 가중치 갱신
- 월요일 07:00 KST: 주간 릴스 기획이 갱신된 가중치와 우리 계정 성과를 반영
- 데이터 파일: `docs/insights/ig/YYYY-MM-DD.json`, 요약 `latest.md`

## 방법 B. Claude가 브라우저로 직접 들어가 보기 (수동, 필요할 때)
Claude Code 클라우드 세션(지금 이 창)은 인스타에 접속할 수 없다. 대신 **사용자 컴퓨터의 브라우저**를 Claude가 쓰게 할 수 있다.
1. **Claude 데스크톱 앱** 설치 → Chrome에 **Claude in Chrome 확장** 설치 → Chrome에서 인스타 로그인
2. 데스크톱 앱의 Claude Code 탭(또는 채팅)에서 "인스타 @e3rehab 릴스 탭 열어서 조회수 상위 10개 정리해줘"라고 하면 Claude가 그 브라우저로 직접 본다
3. 결과를 `benchmarks.json`의 `top_reels`에 넣어 달라고 하면 된다
- 장점: 릴스 **조회수**까지 보인다(공식 API로는 남의 조회수 불가). 단점: 수동, 많이 하면 인스타가 비정상 활동으로 볼 수 있어 하루 수십 개 이내로.
- 클라우드 세션에서 하려면 데스크톱 앱 설정 → Claude Code → **Remote Control**로 이 컴퓨터를 연결해야 하며, 현재 이 세션에는 연결된 컴퓨터가 없다.

## 하지 말 것
- 로그인 쿠키를 복사해 서버에서 자동 스크래핑 → 계정 정지 위험. 공식 API(A)와 사람이 보는 브라우저(B)만 쓴다.
