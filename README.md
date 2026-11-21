# Korean Tokenizer Reproducibility Kit

Standalone reproducibility kit for plain-text token counting. Released under the MIT License.
평문 토큰 수 재현을 위한 독립형 도구입니다. MIT 라이선스를 적용합니다.

## Run locally · 로컬 실행

Python 3.10+; use the same exact Python version for byte-for-byte comparison.
`tiktoken==0.12.0` is pinned; the report records its Unicode database version.
Use a fresh virtual environment and an already approved installation. On a
network-connected setup machine, the one-time setup may fetch the package
and the two official vocabulary files. No API key or paid API is required.
To provision without internet, use approved local wheels and a previously
staged vocabulary cache; do not run the fetch command on the offline machine.

Python 3.10 이상을 사용합니다. 바이트 단위 비교에는 동일한 Python 버전을
쓰세요. 최초 설정은 패키지와 공식 어휘 2종을 내려받을 수 있습니다.
오프라인 기기에는 사전 준비된 휠과 어휘 캐시를 옮기면 됩니다. API 키와
유료 API 호출은 필요하지 않습니다.

```sh
# Authorized setup only / 승인된 최초 설정만
python -m pip install -r requirements.txt
export TIKTOKEN_CACHE_DIR="$PWD/.tiktoken-cache"
python -c 'import tiktoken as t; [t.get_encoding(x) for x in ("cl100k_base","o200k_base")]'

# Offline measurement / 이 아래부터 오프라인
python measure.py --normalize none > raw.json
python measure.py --normalize NFC > nfc.json
python -B -m unittest -v
```

Set the same cache variable when running on another shell or transferring
the cache. The CLI blocks tiktoken's network fallback and fails explicitly
if its cache is missing or invalid. The test suite reports a skipped
integration test when the pinned dependency or cache is unavailable;
a skip is not verification of real token counts. Copying outputs or cache
into a release repository is unnecessary.

CLI는 캐시가 없거나 무효하면 다운로드하지 않고 종료합니다. 의존성이나
캐시가 없을 때 테스트의 실측 항목은 건너뜁니다. 건너뛴 결과를 성능 검증으로
간주하지 마세요.

## Read the report · 결과 해석

- The original plain text, normalized input (if requested), UTF-8 length,
  token IDs, count, and byte-exact round trip are reported per fixture.
- `--normalize none` preserves the input; NFC and NFD are explicit
  experiments. Compare the `ko-nfc` and `ko-nfd` fixtures.
- Only synthetic example text is bundled. This small fixture set is not a
  representative Korean benchmark. JSON includes the input: don't pass
  sensitive text if you plan to share the report.
- These counts cover plain text, not chat framing, tool schemas, images,
  API usage, or billing.

합성 예문의 원문·정규화 입력·UTF-8 길이·토큰 ID·개수·복원 여부를
기록합니다. 한국어 전체의 대표 성능을 주장하지 않습니다. 결과에 원문이
남으니 공유 예정이면 민감한 텍스트를 넣지 마세요. 채팅·도구 스키마·이미지
등을 포함한 API 사용량이나 과금 수치와는 다릅니다.

[Public Korean demo](https://tokenizer-field-notes-kr.mychoi.chatgpt.site/visualizer)
· [Official tiktoken](https://github.com/openai/tiktoken/tree/0.12.0)
· [OpenAI token counting guide](https://developers.openai.com/api/docs/guides/token-counting)
