# Company_Analyzer

## 파일별 기능

- **modules.txt** : 프로그램을 실행 하기 위해 필요한 파이썬 모듈 명 정리 (명령어 이용하여 설치도 가능)
- **main.py** : 미국 주식 티커 받아서 거기에 맞는 모듈 호출
- **extract.py** : SEC EDGAR에서 티커 목록이랑 회사 재무 데이터(XBRL) 다운로드, 24시간 동안 유지함
- **parse.py** : SEC에서 받은 JSON 안에서 매출/순이익/자산/부채 같은 항목 뽑아서 정리함
- **calculate.py** : ROE, ROA, 듀폰분석 등 재무비율 계산하고 콘솔에 표로 출력함
- **notify.py** : 기업의 자세한 지표 테이블을 디스코드 서버의 웹 후크를 이용하여 서버로 전송해줌
- **bot.py** : tmux나 nohup과 같은 백그라운드 실행 프로그램을 이용하여 상시 실행해야 하며 디스코드 봇을 활성화 해줌

## 모듈 설치

```bash
python3 -m pip install -r modules.txt
```

## 실행

```bash
python3 main.py AAPL          # 오직 미국 주식 티커만 사용 가능
```

```bash
/재무제표 aapl                 # bot.py 를 실행한 상태에서 봇이 적용된 디스코드 서버에서만 사용 가능
```
