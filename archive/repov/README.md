# repov 케이팝 평론 기록

repov 앱에서 내보낸 `repov_20260923_202127.xlsx`(2026-09-23)의 **음악** 카테고리 244건을 옮긴 보관소입니다. 원문은 고치지 않았습니다.

| 파일 | 내용 |
|---|---|
| `INDEX.md` | 전체 목록 (인덱스·제목·아티스트·발매일·별점) |
| `reviews/<인덱스>-<제목>.md` | 리뷰 한 건씩, 사람이 읽기 좋은 형태 |
| `repov-music.json` | 기계가 쓰기 좋은 전체 데이터 |
| `covers/<인덱스>.webp` | 표지 (repov 서버 원본 사본) |
| `tools/` | 새 내보내기 파일로 다시 만드는 스크립트 |

## repov-music.json 필드

```
id          repov 인덱스
title       제목 (앨범명 또는 곡명)
artist      아티스트
releaseDate 발매일 (정보 칸이 날짜일 때)
album       수록 앨범·출처 (정보 칸이 날짜가 아닐 때, 주로 싱글)
stars       별점 0.5~5
kind        album (트랙별 평이 있음) | single
oneline     앨범 한 줄 평 (트랙 목록 앞 문단)
tracks      [{ n, title, stars(null = "-"), pick(⭐️ 표시), review }]
quote, link, reviewedAt(repov 종료일), cover(원본 URL), coverFile
text        내용 칸 원문 전체
```

앨범 130건(트랙 751곡, ⭐️ 30곡), 싱글 114건.

## 새 내보내기로 갱신

xlsx를 압축 해제한 폴더를 넣어 실행합니다 (Node 18+).

```
node tools/parse.mjs <압축해제폴더> all.json
node tools/build.mjs all.json .
```
