# 운동 용품 판매 페이지 (파트너 협업) — 구조와 운영

## 1. 구조 (한 사이트, 두 페이지)
```
alpha-performance.netlify.app/          ← 6주 프로그램 판매 (기존, Payhip 결제)
alpha-performance.netlify.app/shop/     ← 용품 페이지 (신규): 제품 카드 = 시연 영상 + 태그 + 가격 + "파트너 스토어에서 구매"
alpha-performance.netlify.app/videos/   ← 직접 올리는 mp4 (Higgsfield·릴스 원본)
alpha-performance.netlify.app/img/      ← 제품 사진
```
- 결제·배송·반품은 **파트너 스토어가 담당**하고, 우리는 제품마다 파트너 링크(제휴 코드 포함)로 보낸다. 재고·결제 시스템을 만들지 않아도 되고, 환불 분쟁도 파트너 몫이다.
- 두 페이지는 서로 연결된다: 프로그램 페이지에 "Train with the gear I use" 섹션, 용품 페이지 끝에 "Get the 6-week program" CTA.
- 링크트리 버튼: ① `🔥 6-Week Speed Program ($20)` ② `🎒 Gear I use` → `https://alpha-performance.netlify.app/shop/?utm_source=instagram&utm_medium=linktree&utm_campaign=gear`
- 릴스 캡션: "Gear in bio" / 댓글 키워드 `GEAR` → ManyChat DM으로 shop 링크 (SPEED 자동화와 같은 방식)

## 2. 파트너에게 확인할 것 (답을 받으면 바로 채움)
| 질문 | 왜 필요한가 |
|---|---|
| 제휴 링크 형식·추적 코드 (예: `?ref=alpha`) | `buy_url`에 넣어야 수수료가 잡힘 |
| 수수료율, 정산 주기, 쿠키 기간 | 수익 계산 |
| 판매 가능 국가·통화 | 팔로워가 브라질·이집트·미국·스페인·아르헨티나. 배송 안 되는 나라면 페이지에 표시 |
| 제품 사진·영상 사용 허가 | 없으면 원우 님 시연 영상만 사용 |
| 할인 코드 제공 여부 (예: ALPHA10) | 전환율에 가장 큰 영향 |
| 반품·보증 처리 주체 | 푸터 문구 확정 |

## 3. 제품 추가·수정 방법
`site/shop/index.html` 맨 위 `AP_SHOP.products`에 한 덩어리씩:
```js
{ id: "aqua-bag", name: "Aqua Bag", price: "$39",
  tagline: "한 줄 설명", used_in: ["Stability","Core"], program: true,
  buy_url: "https://partner.com/aqua-bag?ref=alpha",
  video: "../videos/aquabag.mp4",   // 또는 인스타 릴스 URL, 유튜브 URL
  image: "../img/aquabag.jpg" }
```
- `video`가 `.mp4`면 사이트에서 바로 재생, 인스타 릴스 URL이면 릴스 임베드, 유튜브면 유튜브 임베드. 비어 있으면 "Demo video coming soon".
- `buy_url`에 `REPLACE`가 남아 있으면 버튼이 "Link coming soon"으로 비활성.
- 모든 구매 클릭은 Hotjar 이벤트 `gear_buy_<id>`, 유입은 `shop_src_<utm_medium>`으로 기록 (메인 페이지와 같은 Hotjar ID를 `HOTJAR_ID`에).

## 4. 영상 연동 (Higgsfield 포함)
- **Higgsfield**: AI 영상 생성 도구. 사이트와 '연동'할 API가 필요한 게 아니라, 만든 영상을 **mp4로 내보내서** `site/videos/`에 넣고 `video: "../videos/파일.mp4"`로 가리키면 된다. 제품 소개용 짧은 비주얼(제품 회전, 분위기 컷)에 쓰고, **운동 시연은 원우 님 실사**로 — 팔로우를 만든 건 실제 시연이었다.
- **인스타 릴스**: 릴스 URL을 그대로 `video`에. 임베드라 조회수가 인스타에 쌓인다.
- 용량: mp4는 1080p 15~30초, 10MB 이하 권장(모바일). Netlify 무료 대역폭 월 100GB.
- 권장 조합: 카드 1 = 원우 님 시연 릴스, 카드 2 = Higgsfield 제품 비주얼 mp4 → 어느 쪽이 구매로 이어지는지 Hotjar로 비교.

## 5. 배포
`site` 폴더 전체를 zip으로 Netlify `alpha-performance`에 드롭 (이전과 같은 방법). shop 하위 폴더가 포함돼야 하므로 index.html 한 장만 올리면 안 된다.

## 6. 주의
- 제휴 링크 공개 문구(상단 "I may earn a commission")는 유지. 인스타 캡션에도 `#ad` 또는 "affiliate link" 표시.
- 선수 이름·사진으로 제품을 홍보하지 않는다 (초상권, 10/29 조사).
- 제품에 의료 효과를 단정하지 않는다 ("부상 예방" → "재활 운동에 사용").
