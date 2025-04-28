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

