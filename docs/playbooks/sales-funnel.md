# 판매 동선 운영 가이드 (2026-10-29)

판매 경로는 세 가지다: ① 프로필 링크 ② 댓글 키워드 → 자동 DM ③ 스토리 링크 스티커.
모든 링크는 같은 판매 페이지로 보내고, `utm_medium`만 바꿔서 Hotjar에서 경로를 구분한다.

| 경로 | 주소 |
|---|---|
| 프로필(링크트리) | `https://alpha-performance.netlify.app/?utm_source=instagram&utm_medium=linktree&utm_campaign=bio` |
| 자동 DM | `https://alpha-performance.netlify.app/?utm_source=instagram&utm_medium=dm&utm_campaign=speed` |
| 스토리 | `https://alpha-performance.netlify.app/?utm_source=instagram&utm_medium=story&utm_campaign=<날짜 예: 1105>` |

## 1. 링크 복구 순서
1. 새 판매 페이지(`site/index.html`)를 Netlify에 배포한다. 배포 전에 링크를 걸면 예전 페이지($99 → 80% OFF)로 간다.
2. 링크트리 버튼 1개: `⚡ 6-Week Speed Program ($20)` → 위 프로필 주소
3. 인스타 앱 → 프로필 편집 → 링크 → 외부 링크 추가 → 링크트리 주소

## 2. 댓글 키워드 → 자동 DM (ManyChat)
- 2026-03 요금 변경으로 무료 플랜은 활성 연락처 25명까지. 테스트는 무료로, 실제 운영은 Essential(월 약 $15) 이상 필요.
- 준비: 인스타 프로페셔널 계정 + 인스타 설정 → 메시지 → "메시지 도구 연결 허용" 켜기
- 설정: ManyChat 가입 → Instagram 연결 → Automation → 템플릿 "Auto-DM links from comments"
  - 대상 게시물: 특정 게시물 또는 다음 게시물
  - 키워드: `SPEED`, `VELOCIDAD`, `VELOCIDADE`
  - 공개 댓글 답글 (여러 개 돌려 쓰기): "Sent you a DM 📩" / "¡Te lo envié por DM! 📩" / "Check your DMs 🔥"
  - DM 메시지 + 버튼(위 자동 DM 주소)

DM 문구 (영어)
```
Hey! Here's my 6-Week Speed Program 👇
24 sessions, no gym needed, $20 one-time.
Every drill comes with a video demo.
```
DM 문구 (스페인어, VELOCIDAD 키워드용)
```
¡Hola! Aquí tienes mi programa de velocidad de 6 semanas 👇
24 sesiones, sin gimnasio, pago único de $20.
Cada ejercicio tiene un video. (El programa está en inglés.)
```
버튼 문구: `Get the program` / `Ver el programa`

## 3. 스토리 판매
스토리 = 24시간 뒤 사라지는 게시물. 링크 스티커를 붙이면 보는 사람이 눌러서 판매 페이지로 간다.
- 주 3회, 한 번에 2~3장. 링크 스티커는 마지막 장에만.
- 월: 시연 영상 10초 + "Full 6-week plan 👇" + 링크 스티커
- 수: 투표 스티커 "Your weakness? First step / Top speed / Turning" → 다음 날 답 영상
- 금: 원우 님 코칭 현장·비하인드 + 링크 스티커
- 프로필 하이라이트 "PROGRAM"에 링크 스티커 스토리를 모아 두면 24시간 뒤에도 계속 노출됨
- 링크 스티커가 있는 스토리는 직접 올린다 (Meta Business Suite로 예약하면 스티커가 빠짐)

## 4. 업로드 시간
- 릴스·게시물: 인스타 앱 예약 기능 (최대 약 75일 앞까지). 한국 시간 화·목·금 오후 9시.
- 스토리: 직접 올리기 (위 이유)

## 5. 영어 + 스페인어 캡션 형식
- 영상 화면 글자: 영어 짧게 (동작 이름, 핵심 큐 1개)
- 캡션: 영어 블록 → 스페인어 블록 → 해시태그 (두 언어 섞기)
- 업로드 시 'Meta AI 번역(음성 번역)' 옵션이 보이면 켜기 (원우 님이 말하는 영상일 때)

캡션 예시
```
You lose the race to the ball in your first 3 steps.
3 plyometric drills to fix your start 👇
1. Pogo jumps – stiff ankles, quick contacts
2. Lateral bounds – stick the landing
3. Split-stance drive – push the ground back

💬 Comment SPEED and I'll send you my full 6-week plan.

🇪🇸 Pierdes la carrera por el balón en los primeros 3 pasos.
3 ejercicios pliométricos para mejorar tu arranque 👇
1. Saltos pogo – tobillos firmes, contactos rápidos
2. Saltos laterales – aterriza estable
3. Impulso en posición dividida – empuja el suelo hacia atrás

💬 Comenta VELOCIDAD y te envío mi plan completo de 6 semanas.

#footballtraining #speedtraining #soccerdrills #futbol #entrenamientodefutbol #velocidad
```
