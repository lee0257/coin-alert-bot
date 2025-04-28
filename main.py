import time
import requests
import threading
from flask import Flask

# 텔레그램 설정
TELEGRAM_TOKEN = "7287889681:AAEuSd9XLyQGnXwDK8fkI40Ut-_COR7xIrY"
CHAT_ID = "1901931119"

# 업비트 전체 KRW 마켓 가져오기
def get_all_krw_tickers():
    url = "https://api.upbit.com/v1/market/all"
    headers = {"Accept": "application/json"}
    response = requests.get(url, headers=headers)
    markets = response.json()
    krw_tickers = []
    for market in markets:
        if market['market'].startswith('KRW-'):
            krw_tickers.append({
                "market": market['market'],
                "korean_name": market['korean_name']
            })
    return krw_tickers

# 특정 코인 1분봉 5개 가져오기
def get_candle_data(market):
    url = f"https://api.upbit.com/v1/candles/minutes/1?market={market}&count=5"
    headers = {"Accept": "application/json"}
    response = requests.get(url, headers=headers)
    return response.json()

# 텔레그램 메시지 보내기
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"❗ 텔레그램 전송 실패: {e}")

# 급등 조짐 감지
def detect_spike(ticker_info):
    market = ticker_info['market']
    korean_name = ticker_info['korean_name']

    try:
        candles = get_candle_data(market)
        if len(candles) < 5:
            return

        # 5분 평균 계산
        avg_volume = sum(candle['candle_acc_trade_volume'] for candle in candles[1:]) / 4
        avg_price = sum(candle['trade_price'] for candle in candles[1:]) / 4

        # 최근 1분 데이터
        current = candles[0]
        current_volume = current['candle_acc_trade_volume']
        current_price = current['trade_price']

        # 변화율 계산
        volume_change = ((current_volume - avg_volume) / avg_volume) * 100
        price_change = ((current_price - avg_price) / avg_price) * 100

        # 급등 조짐 판단 (거래량 +30% 이상 또는 가격 +2% 이상)
        if volume_change >= 30 or price_change >= 2:
            message = (f"🚀 급등 조짐 포착!\n"
                       f"{korean_name} ({market})\n"
                       f"현재가: {current_price:,.0f} KRW\n"
                       f"거래량 변화: {volume_change:.2f}%\n"
                       f"가격 변화: {price_change:.2f}%")
            print(message)
            send_telegram_message(message)

    except Exception as e:
        print(f"에러 발생({market}): {e}")

# 전체 모니터링
def monitor_market():
    while True:
        tickers = get_all_krw_tickers()
        for ticker_info in tickers:
            detect_spike(ticker_info)
            time.sleep(0.2)  # API 호출 부하 방지용 (0.2초 대기)
        time.sleep(30)  # 전체 순회 후 30초 대기

# Flask 웹서버 (Koyeb용)
app = Flask(__name__)

@app.route("/")
def home():
    return "코인 경고 봇 작동 중!"

if __name__ == "__main__":
    threading.Thread(target=monitor_market).start()
    app.run(host="0.0.0.0", port=8000)
import time
import requests
from flask import Flask

# 업비트에서 비트코인 가격 조회
UPBIT_TICKER_URL = "https://api.upbit.com/v1/ticker?markets=KRW-BTC"

# 텔레그램 봇 정보
TELEGRAM_TOKEN = "7287889681:AAEuSd9XLyQGnXwDK8fkI40Ut-_COR7xIrY"
CHAT_ID = "1901931119"  # 여기! 네 채팅 ID

def get_current_price():
    try:
        response = requests.get(UPBIT_TICKER_URL)
        response.raise_for_status()
        result = response.json()
        return result[0]['trade_price']
    except Exception as e:
        print(f"에러 발생: {e}")
        return None

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("✅ 텔레그램 메시지 전송 성공!")
        else:
            print(f"❗ 실패: {response.text}")
    except Exception as e:
        print(f"❗ 에러 발생: {e}")

def monitor_price():
    last_price = get_current_price()
    if last_price is None:
        print("초기 가격 불러오기 실패")
        return

    print(f"🚀 시작 가격: {last_price} KRW")

    while True:
        current_price = get_current_price()
        if current_price:
            change_rate = ((current_price - last_price) / last_price) * 100
            print(f"현재가: {current_price} KRW, 변동률: {change_rate:.2f}%")

            if change_rate >= 3.0:  # 3% 이상 급등 감지
                alert_message = f"🚀 급등 감지!\n현재 가격: {current_price} KRW\n변동률: {change_rate:.2f}%"
                send_telegram_message(alert_message)

            last_price = current_price

        time.sleep(30)  # 30초마다 가격 체크

# 웹서버
app = Flask(__name__)

@app.route("/")
def home():
    return "코인 경고 봇 작동 중!"

if __name__ == "__main__":
    import threading
    threading.Thread(target=monitor_price).start()

    app.run(host="0.0.0.0", port=8000)
import time
import requests
from flask import Flask

# 업비트에서 비트코인 가격 조회
UPBIT_TICKER_URL = "https://api.upbit.com/v1/ticker?markets=KRW-BTC"

# 텔레그램 봇 정보
TELEGRAM_TOKEN = "7287889681:AAEuSd9XLyQGnXwDK8fkI40Ut-_COR7xIrY"
CHAT_ID = "1901931119"  # 너의 텔레그램 ID

def get_current_price():
    try:
        response = requests.get(UPBIT_TICKER_URL)
        response.raise_for_status()
        result = response.json()
        return result[0]['trade_price']
    except Exception as e:
        print(f"에러 발생: {e}")
        return None

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("✅ 텔레그램 메시지 전송 성공!")
        else:
            print(f"❗ 실패: {response.text}")
    except Exception as e:
        print(f"❗ 에러 발생: {e}")

def monitor_price():
    last_price = get_current_price()
    if last_price is None:
        print("초기 가격 불러오기 실패")
        return

    print(f"🚀 시작 가격: {last_price} KRW")

    while True:
        current_price = get_current_price()
        if current_price:
            change_rate = ((current_price - last_price) / last_price) * 100
            print(f"현재가: {current_price} KRW, 변동률: {change_rate:.2f}%")

            if change_rate >= 3.0:  # ✅ 3% 이상 급등 감지
                alert_message = f"🚀 급등 감지!\n현재 가격: {current_price} KRW\n변동률: {change_rate:.2f}%"
                send_telegram_message(alert_message)

            last_price = current_price

        time.sleep(30)  # 30초마다 가격 체크

# 웹서버
app = Flask(__name__)

@app.route("/")
def home():
    return "코인 경고 봇 작동 중!"

if __name__ == "__main__":
    import threading
    threading.Thread(target=monitor_price).start()

    app.run(host="0.0.0.0", port=8000)
import time
import requests

UPBIT_TICKER_URL = "https://api.upbit.com/v1/ticker?markets=KRW-BTC"

def get_current_price():
    try:
        response = requests.get(UPBIT_TICKER_URL)
        response.raise_for_status()
        result = response.json()
        return result[0]['trade_price']
    except Exception as e:
        print(f"에러 발생: {e}")
        return None

def main():
    last_price = get_current_price()
    if last_price is None:
        print("초기 가격 불러오기 실패")
        return

    print(f"시작 가격: {last_price} KRW")
    
    while True:
        current_price = get_current_price()
        if current_price:
            change_rate = ((current_price - last_price) / last_price) * 100
            print(f"현재가: {current_price} KRW, 변동률: {change_rate:.2f}%")

            if change_rate >= 1.5:  # 1.5% 이상 급등 감지
                print("🚀 급등 감지!")

            last_price = current_price

        time.sleep(30)  # 30초마다 체크

if __name__ == "__main__":
    from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "코인 경고 봇 작동 중!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

