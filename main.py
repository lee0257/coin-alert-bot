# 업비트 실시간 급등/급락/세력/눌림목/바닥 다지기 감지 통합 시스템 (최종 버전)

import asyncio
import websockets
import json
import time
import requests

# 업비트 WebSocket 서버 URL
UPBIT_WS_URL = "wss://api.upbit.com/websocket/v1"

# 텔레그램 봇 설정
TELEGRAM_BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
TELEGRAM_CHAT_ID = 'YOUR_CHAT_ID'

# 감시할 코인 리스트
MONITOR_COINS = ["KRW-BTC", "KRW-ETH", "KRW-SUI", "KRW-ARB", "KRW-STX", "KRW-SEI"]

# 조건 설정
VOLUME_MULTIPLIER = 2.5
BUY_RATIO_THRESHOLD = 60
RISE_LIMIT = 0.5
DROP_MAJOR = 5
DROP_ALT = 7
DROP_TIME_WINDOW = 180  # 3분
SELYAK_THRESHOLD = 140
HORIZONTAL_TIME = 1200  # 20분

# 내부 상태 저장용
ticker_data = {}
last_alert = {}

async def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    requests.post(url, data=data)

async def handle_message(msg):
    code = msg['cd']
    price = msg['tp']
    volume = msg['tv']
    timestamp = time.time()

    if code not in ticker_data:
        ticker_data[code] = {
            'start_price': price,
            'start_volume': volume,
            'start_time': timestamp,
            'max_price': price,
            'min_price': price,
            'volume_sum': volume,
            'price_list': [price]
        }
    else:
        data = ticker_data[code]
        elapsed = timestamp - data['start_time']

        # 가격/거래량 업데이트
        data['max_price'] = max(data['max_price'], price)
        data['min_price'] = min(data['min_price'], price)
        data['volume_sum'] += volume
        data['price_list'].append(price)

        # 급락 감지
        if elapsed <= DROP_TIME_WINDOW:
            drop_percent = (data['start_price'] - price) / data['start_price'] * 100
            if ('BTC' in code or 'ETH' in code) and drop_percent >= DROP_MAJOR:
                if last_alert.get(code + '_drop', 0) + 180 < timestamp:
                    await send_telegram_message(f"\ud83d\udcc8 [급락 감지] {code} 3분 이내 {drop_percent:.2f}% 급락!")
                    last_alert[code + '_drop'] = timestamp
            elif drop_percent >= DROP_ALT:
                if last_alert.get(code + '_drop', 0) + 180 < timestamp:
                    await send_telegram_message(f"\ud83d\udcc8 [급락 감지] {code} 3분 이내 {drop_percent:.2f}% 급락!")
                    last_alert[code + '_drop'] = timestamp

        # 급등 초입 포착
        recent_prices = data['price_list'][-60:]  # 최근 1분 데이터
        if len(recent_prices) >= 10:
            price_change = (price - min(recent_prices)) / min(recent_prices) * 100
            if price_change <= RISE_LIMIT and data['volume_sum'] >= VOLUME_MULTIPLIER * volume:
                if last_alert.get(code + '_rise', 0) + 300 < timestamp:
                    await send_telegram_message(f"\ud83d\udcc9 [급등 초입 포착] {code} 거래량 급증, 상승 직전 감지!")
                    last_alert[code + '_rise'] = timestamp

        # 세력 포착 (체결강도 가정, 간략화)
        if data['volume_sum'] >= SELYAK_THRESHOLD * 1000:
            if last_alert.get(code + '_se', 0) + 600 < timestamp:
                await send_telegram_message(f"\ud83d\udd2c [세력 매집 포착] {code} 거래량 급증 + 저점 매집 시도 감지!")
                last_alert[code + '_se'] = timestamp

        # 바닥 다지기 포착
        if elapsed >= HORIZONTAL_TIME:
            price_range = max(data['price_list']) - min(data['price_list'])
            if price_range / min(data['price_list']) * 100 <= 1.0:
                if last_alert.get(code + '_bottom', 0) + 1800 < timestamp:
                    await send_telegram_message(f"\ud83d\udcca [바닥 다지기 포착] {code} 저점 횡보 + 거래량 증가 감지!")
                    last_alert[code + '_bottom'] = timestamp

async def main():
    async with websockets.connect(UPBIT_WS_URL, ping_interval=None) as websocket:
        subscribe_fmt = [{
            "ticket": "test",
        }, {
            "type": "trade",
            "codes": MONITOR_COINS
        }]
        await websocket.send(json.dumps(subscribe_fmt))

        while True:
            try:
                message = await websocket.recv()
                msg = json.loads(message)
                await handle_message(msg)
            except Exception as e:
                print(f"에러 발생: {e}")
                break

if __name__ == "__main__":
    asyncio.run(main())
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

# 특정 코인 1분봉 2개 가져오기
def get_candle_data(market):
    url = f"https://api.upbit.com/v1/candles/minutes/1?market={market}&count=2"
    headers = {"Accept": "application/json"}
    response = requests.get(url, headers=headers)
    return response.json()

# 특정 코인의 24시간 거래대금 가져오기
def get_24h_volume(market):
    url = f"https://api.upbit.com/v1/ticker?markets={market}"
    headers = {"Accept": "application/json"}
    response = requests.get(url, headers=headers)
    data = response.json()
    if data and 'acc_trade_price_24h' in data[0]:
        return data[0]['acc_trade_price_24h']
    return 0

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
        # 거래대금 체크
        acc_trade_price_24h = get_24h_volume(market)
        if acc_trade_price_24h < 5_000_000_000:  # 5억 미만 제외
            return

        candles = get_candle_data(market)
        if len(candles) < 2:
            return

        prev = candles[1]
        current = candles[0]

        # 1분봉 거래량 변화율
        volume_change = ((current['candle_acc_trade_volume'] - prev['candle_acc_trade_volume']) / (prev['candle_acc_trade_volume'] + 1e-8)) * 100
        # 1분봉 가격 변화율
        price_change = ((current['trade_price'] - prev['trade_price']) / (prev['trade_price'] + 1e-8)) * 100

        # 급등 조짐 판단: 거래량 +50% 이상 & 가격 +1% 이상
        if volume_change >= 50 and price_change >= 1:
            message = (f"🚀 급등 조짐 포착!\n"
                       f"{korean_name} ({market})\n"
                       f"현재가: {current['trade_price']:,.0f} KRW\n"
                       f"거래량 변화율: {volume_change:.2f}%\n"
                       f"가격 변화율: {price_change:.2f}%")
            print(message)
            send_telegram_message(message)

    except Exception as e:
        print(f"에러 발생 ({market}): {e}")

# 전체 모니터링
def monitor_market():
    while True:
        tickers = get_all_krw_tickers()
        for ticker_info in tickers:
            detect_spike(ticker_info)
            time.sleep(0.2)  # API 부하 방지
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

# 특정 코인 1분봉 2개 가져오기
def get_candle_data(market):
    url = f"https://api.upbit.com/v1/candles/minutes/1?market={market}&count=2"
    headers = {"Accept": "application/json"}
    response = requests.get(url, headers=headers)
    return response.json()

# 특정 코인의 24시간 거래대금 가져오기
def get_24h_volume(market):
    url = f"https://api.upbit.com/v1/ticker?markets={market}"
    headers = {"Accept": "application/json"}
    response = requests.get(url, headers=headers)
    data = response.json()
    if data and 'acc_trade_price_24h' in data[0]:
        return data[0]['acc_trade_price_24h']
    return 0

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
        # 거래대금 체크
        acc_trade_price_24h = get_24h_volume(market)
        if acc_trade_price_24h < 5_000_000_000:  # 10억 미만 제외
            return

        candles = get_candle_data(market)
        if len(candles) < 2:
            return

        prev = candles[1]
        current = candles[0]

        # 1분봉 거래량 변화율
        volume_change = ((current['candle_acc_trade_volume'] - prev['candle_acc_trade_volume']) / (prev['candle_acc_trade_volume'] + 1e-8)) * 100
        # 1분봉 가격 변화율
        price_change = ((current['trade_price'] - prev['trade_price']) / (prev['trade_price'] + 1e-8)) * 100

        # 급등 조짐 판단: 거래량 +50% 이상 & 가격 +1% 이상
        if volume_change >= 100 and price_change >= 2:
            message = (f"🚀 급등 조짐 포착!\n"
                       f"{korean_name} ({market})\n"
                       f"현재가: {current['trade_price']:,.0f} KRW\n"
                       f"거래량 변화율: {volume_change:.2f}%\n"
                       f"가격 변화율: {price_change:.2f}%")
            print(message)
            send_telegram_message(message)

    except Exception as e:
        print(f"에러 발생 ({market}): {e}")

# 전체 모니터링
def monitor_market():
    while True:
        tickers = get_all_krw_tickers()
        for ticker_info in tickers:
            detect_spike(ticker_info)
            time.sleep(0.2)  # API 호출 부하 방지
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

