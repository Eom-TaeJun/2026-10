# 실행·보존 기록

- 날짜: 2026-11-01 UTC. 정확한 실행 시각은 dev.json/eval.json의 run_at_utc.
- 저장소: `/workspace/2026-10`, 로컬 작업 브랜치 `kb-evidence`.
- 시작 버전: `4b736274c19ae027b52c50c1ecaed4210dce76b3` (origin main에서 fetch한 공개 저장소 커밋).
- 최초 작업트리가 비어 있어 허용된 Git 원격 읽기로 main을 fetch한 뒤 FETCH_HEAD에서 작업 브랜치를 만들었다. 최초 origin/main 추적 전환은 해당 ref가 없어 실패했고 FETCH_HEAD로 정상 전환했다.
- 실행 순서: 계획과 입력/수작업 정답 → fixture_freeze.json → engine.py/run.py/test_engine.py → code_freeze.json → 단위시험 → 개발 → 평가 1회 → 문서와 검증.
- 실제 명령: `python -m unittest discover -s kb/experiments -v`, `python kb/experiments/run.py --split dev --out kb/results`, `python kb/experiments/run.py --split eval --out kb/results`, `python kb/validate_package.py`, `git diff --check`.
- 단위/개발/평가 로그와 JSON/CSV 보존. 구현은 평가 전후 SHA 동일, 평가 후 튜닝 없음. validate_package.py는 보존된 결과와 링크·패턴을 점검하며 holdout을 재실행하지 않는다.
- 외부 패키지 설치, Docker 실행, 실거래, 원격 push, 게시, Library 업로드 없음. 이번 작업에서 생성한 컨테이너 없음. 기존 실험 폴더는 수정하지 않았다.

## 공개 적합성

이 폴더에는 합성 입력·규칙·출력, 자체 요약, 공개 URL과 AI 보조 코드만 포함했다. Library 공식 다운로드 대상 폴더는 비어 있었으며 비공개 원문을 읽거나 복사하지 않았다. 기존 비공개 PoC도 포함하지 않았다. 자동 점검은 공통 자격정보 패턴/서명 전송 URL/Library 식별자/로컬 링크/고정 SHA를 검사하며 완전한 개인정보 검출기는 아니다. AI가 문서·입력·결과를 함께 검토했다. 실제 고객 이름·의료정보·실계좌 필드는 없다. 공개 가능 범위로 작성했지만 이번에는 로컬 보존만 승인되었으며 공개하지 않았다.

## 남은 차단

공식 Library materialization: 첫 연구 문서 다운로드는 `library file transfer failed: download failed`, exit 1. 준비 호출은 성공했으나 내용 소비는 실패, 두 번째 파일은 미실행. 현재 오류의 HTTP 원인 불명. 동일 실패 반복이나 우회 없음. 최신 공식 연결 복구 근거 없이는 재시도하지 않는다. 이 제한은 공개자료·합성 실험·로컬 commit 완료를 막지 않는다.

보존된 CSV는 Python csv.writer의 표준 CRLF 줄끝을 사용한다. 최초 staged diff 점검은 이를 trailing whitespace로 보고해 commit 이전에 멈췄다. 원결과/코드를 수정하지 않고 `.gitattributes`에 CSV의 CRLF 허용을 명시한 뒤 동일 점검을 통과시켰다.
