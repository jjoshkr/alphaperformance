# 부상 뉴스 → 재활 콘텐츠 자동화 (v2 구조)

## 1. 부상 정보 앱들은 어디서 데이터를 가져오나 (조사 결과, 2026-11-04)
| 계층 | 누가 쓰나 | 특징 | 우리 선택 |
|---|---|---|---|
| **공식 데이터 공급사** (Opta/Stats Perform, Sportradar) | SofaScore, FotMob, 방송사 | 선수별 구조화 데이터. 기업 계약, 매우 비쌈 | 불가 |
| **스포츠 API** (API-Football, Sportmonks) | 중소 앱, 판타지 서비스 | `/injuries` 엔드포인트: 선수·팀·사유("Hamstring Injury"). API-Football 무료는 하루 100회지만 현재 시즌 접근이 막힐 수 있음(Pro $19/월) | **선택 사용** (키 있으면 자동) |
| **집계 사이트** (Transfermarkt 부상 표, PhysioRoom, premierinjuries.com, NewsNow) | 팬, 판타지 유저 | 직접 수집·편집. 공식 API 없음, 스크래핑은 약관 위반·차단 위험 | 참고만 |
| **언론 RSS** (BBC, Sky Sports, ESPN, Guardian, 클럽 공식 사이트) | 뉴스 앱 | 가장 빠름. 헤드라인에 부위·기간이 자주 들어감 | **사용** |
| **Google News RSS** | 개인 자동화 | 키 없이 검색어별 피드. 종목이 섞여 들어와 필터 필수 | **사용** |

결론: 속도는 언론 RSS + Google News, 정확한 선수·부위는 API-Football(유료)이나 Claude 추출로 보완.

## 2. 파이프라인
```
[수집] Google News RSS 13개 검색어 + BBC/Sky/ESPN/Guardian RSS (+ API-Football)
   ↓
[필터] 부상 헤드라인만 · 축구만(리그·클럽 사전 110개 클럽) · 복귀/이적/"boost" 제외 · 중복 제거
   ↓
[추출] 선수 · 클럽 · 리그 · 부위(14종) · 정도(경미/중간/중증) · 기간
        ANTHROPIC_API_KEY 있으면 Claude(구조화 출력) / 없으면 키워드 규칙
   ↓
[기억] docs/injuries/state.json — 선수+부위 기준으로 60일간 기억, 같은 소식은 다시 알리지 않음
   ↓
[알림] 새 소식만 텔레그램 → 선수·부위·정도·기간 + 재활 단계 + 촬영할 운동 3개 + 시연 영상 링크
   ↓
[보고서] docs/injuries/날짜.md · latest.md · latest.json (캡션 EN/ES 포함)
```
- 실행 주기: GitHub Actions 30분마다 (`.github/workflows/injury-watch.yml`), 수동 실행 가능
- 파일: `tools/injury_watch/injury_watch.py`(코드) · `sources.json`(소스·클럽 사전) · `rehab_library.json`(재활 운동) · `videos.json`(운동→영상 링크)

## 3. 한 번만 하는 설정 (GitHub 저장소 → Settings → Secrets and variables → Actions → New repository secret)
| 시크릿 이름 | 용도 | 받는 법 |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | 알림 보내는 봇 | 텔레그램에서 **@BotFather** 검색 → `/newbot` → 이름 입력 → 토큰 복사 |
| `TELEGRAM_CHAT_ID` | 알림 받을 대화방 | **브라우저 불필요:** 토큰만 시크릿에 먼저 넣고, 텔레그램에서 봇(@AlphaperformanceBot)에게 아무 메시지를 보낸 뒤 Actions를 한 번 실행하면 봇이 그 대화방에 ID를 답장해 준다. 그 숫자를 시크릿으로 등록. 원우 님과 같이 받으려면 그룹을 만들고 봇을 초대한 뒤 그룹에서 메시지를 보내고 같은 방법(그룹 id는 음수) |
| `ANTHROPIC_API_KEY` | 선수·부위·기간 정확 추출 | console.anthropic.com → API Keys. 비용: 실행당 새 헤드라인 10~40개, 월 $3~10 수준 추정 |
| `API_FOOTBALL_KEY` | 구조화 부상 데이터 | api-football.com 가입. 무료 키로 먼저 테스트, 현재 시즌이 막히면 Pro |

시크릿이 없어도 돌아간다: 알림 없이 보고서만 생성하고 추출은 규칙 기반.

## 4. 알림 내용
선수·클럽·리그 → 부위·정도·기간 → 📰 출처 → 🧠 어디·무슨 근육(위치 / 근육 / 집중할 근육) → 🏃 재활 단계와 목표 + 촬영할 운동 3개(영상 링크) → 🎯 콘텐츠 각도 → ⚠️ 주의. 부위별 해부·단계 목표는 `rehab_library.json`의 `anatomy`·`goal`에 한국어로 있다.

## 5. 영상 연결
`videos.json`에 운동 이름(= `rehab_library.json`의 문구 그대로) → 원우 님 릴스 링크를 넣으면 알림과 보고서에 "영상" 링크가 붙는다. 비어 있으면 "영상 촬영 필요"로 표시되어 촬영 목록이 된다. 우선 촬영 추천: Nordic curl, Copenhagen plank, 단일 발 균형, Pogo hops, 카프 레이즈, Reverse Nordic.

## 6. 운영 흐름
1. 텔레그램 알림 도착 → 선수·부위·정도 확인
2. 원우 님이 재활 단계·운동 검토 (틀리면 `rehab_library.json` 수정 요청)
3. "촬영할 단계" 운동 3개 시연 촬영 → 릴스 업로드 → `videos.json`에 링크 추가
4. 캡션은 `latest.md`의 EN/ES 초안 사용. 경기 영상은 쓰지 않고 뉴스는 링크로만

## 7. 한계
- 헤드라인에 부위가 없으면 "미분류"로 남는다 (규칙 기반일 때 특히). Claude 키를 넣으면 크게 개선.
- 모든 운동 내용은 일반 예시. 의료 조언이 아니며 게시물에도 그 문구를 유지.
- GitHub는 60일간 저장소 활동이 없으면 예약 실행을 멈춘다.
