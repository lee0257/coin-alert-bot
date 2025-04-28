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

