# 벤치마킹 구조와 주간 릴스 기획 자동화 (2026-11-13)

## 1. 벤치마크 계정 (팔로워는 웹 검색 스냅샷, '확인 필요'는 직접 확인 전)
| 분야 | 계정 | 팔로워 | 메모 |
|---|---|---|---|
| S&C | @coach.bluee (Lucas Dasilva) | 10M | 일반 피트니스. 축구 특화 아님 → 훅·편집 리듬만 참고 |
| S&C | @marcusriosofficial | 540K | 스페인어권 — 우리 1위 언어권(21.8%) |
| S&C | @nooch_13 (Carmen Del Mastro) | 238K | sports performance, 자체 프로그램 판매 모델 |
| S&C | @ycg_performance_official (윤청구PTC) | 198K | 한국. 피지컬+재활+물리치료 — 원우 님과 같은 겸업 포지션 |
| S&C | @tomjoycefitness | 115K | UK 축구 S&C |
| S&C | @sergiotreinador · @elimak__ · @jona.tou · @pass_official_ | 확인 필요 | 검색 미검출. 프로필 캡처 주시면 채움 |
| Rehab | @e3rehab | ~480K | 근거 기반 재활의 기준점 (신화 깨기, 단계별 진행) |
| Rehab | @medspired (Nav Singh Badesha, MD) | ~119K | 의사 계정, 의학 교육 톤 |
| Rehab+S&C | @niklas.sportphysio | 80K+ (IG+TikTok) | 독일 스포츠물리치료. **원우 님과 가장 가까운 포지션(독일·S&C+rehab)** |

## 2. '조회수가 터지는' 패턴 (가설 → 실데이터로 가중치 갱신)
파일: `tools/content_planner/benchmarks.json` → `patterns` (weight 1~5)

**S&C**
| 패턴 | 훅 예시 | 왜 |
|---|---|---|
| 프로 선수 동작 분해 → 코치 재현 ★5 | "Why {player} is faster than you (it's not genetics)" | 우리 채널 팔로우 상위 3개가 전부 이 형식 |
| 3 drills to fix X ★5 | "3 drills to fix a slow first step" | 저장·공유형, 구조 단순 |
| 측정 before/after ★4 | "We cut his 10m time by 0.2s in 4 weeks" | 숫자 = 증거 = 프로그램 판매 |
| Stop doing X ★4 | "Stop doing this if you want to get faster" | 반론형, 댓글 유도 |
| POV 실제 세션 ★4 | "POV: speed session with a U-20 international" | 신뢰 (선수 동의 필요) |
| 폭발적 비주얼 ★3 | "Plyometrics level 1→5" | 조회수↑ 팔로우 전환 중간 |

**Rehab**
| 패턴 | 훅 예시 | 왜 |
|---|---|---|
| 근거 기반 신화 깨기 ★5 | "You don't need to stretch a tight hamstring" | e3rehab 형식, 논쟁 → 공유 |
| 프로 부상 반응 + 재활 단계 ★5 | "{player} is out for {weeks} weeks. Here's what rehab looks like" | 시의성 + 전문성, 부상 알림과 직결 |
| 어디·무슨 근육 ★4 | "Where your hamstring actually tears" | 교육형, 저장 |
| 단계 사다리 Level 1→5 ★4 | "Ankle sprain rehab: level 1 to 5" | 시리즈화 |
| 셀프 테스트 ★4 | "Can you do 25 single-leg calf raises?" | 참여형 |
| 물리치료사 반응 ★3 | "Physio reacts: worst hamstring advice" | 톤 관리 필요 |

**원우 님만의 조합 (벤치마크 누구도 다 갖지 않은 것):** S&C+rehab 겸업 × 도르트문트 현지 × U-20 코칭 × 한·영·독 3개 언어. 모든 릴스는 "프로 소식(훅) → 어디·무슨 근육(전문성) → 원우 님 시연 3동작(저장) → 댓글 키워드(전환)" 순서.

## 3. 주간 자동 기획 (매주 월 07:00 KST → 텔레그램 그룹 + `docs/content/weekly/`)
- 화 · Rehab · **이번 주 프로 부상 반응** (부상 알림 데이터에서 채널 적합도 높은 선수 자동 선택)
- 목 · S&C · 패턴 순환 (최근 3주 안 쓴 것 중 가중치 높은 순)
- 금 · Rehab · 패턴 순환 (부상 반응 제외)
- 각 릴스: 훅 EN/DE/ES, 초 단위 구성(행동·한국어 대사·화면 자막), 운동 3개(세트·큐), 촬영 메모, 캡션 EN/DE/ES, 해시태그, 주의점
- Claude가 작성(ANTHROPIC_API_KEY). 키가 없거나 실패하면 템플릿 초안
- 코드: `tools/content_planner/planner.py`, 워크플로 `.github/workflows/weekly-plan.yml`

## 4. 실데이터 넣는 방법 (가설 → 검증)
인스타그램은 로그인 없이 자동 수집이 막혀 있어 두 가지 중 하나:
1. **수동(무료, 권장 시작):** 각 계정 프로필 → 릴스 탭(조회수 표시됨) 캡처 2~3장씩 → Claude Code에 보내면 `top_reels`에 `{title, views, pattern}`으로 정리해 넣고 가중치를 갱신
2. **수집 도구(유료, 약관 회색지대):** Apify 'Instagram Reel Scraper' 등으로 계정별 최근 릴스 조회수 수집 → `benchmarks.json`에 반영. 월 $5~20. 인스타 약관상 스크래핑은 계정 제재 위험이 있어 본계정과 분리된 환경에서만

데이터가 들어오면 patterns.weight를 "해당 패턴 릴스의 중앙값 조회수 / 계정 평균"으로 다시 계산해 기획 순환에 반영한다.

## 5. 다음 단계 (영상 자동화는 나중)
- 기획 → 원우 님 한국어 촬영 → Vrew 자막 → ElevenLabs 더빙(DE/EN/ES) → CapCut 마무리
- 영상 자동화 1차 후보: 기획의 대사를 ElevenLabs로 음성화 + 시연 클립 라이브러리(`videos.json`)를 CapCut 템플릿에 자동 배치
