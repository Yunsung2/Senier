from django.shortcuts import render
from django.http import JsonResponse
from datetime import datetime, timedelta
import requests
import pyupbit
import json
# dict를 통해 딕셔너리 생성
def get_chart_data(time_period):
    if time_period == 'week':
        count = 7
    elif time_period == 'month':
        count = 30
    elif time_period == 'threeMonths':
        count = 90
    else:
        count = 90 

    bitcoin_data = pyupbit.get_ohlcv("KRW-BTC", interval="day", count=count)
    ethereum_data = pyupbit.get_ohlcv("KRW-ETH", interval="day", count=count)
    ripple_data = pyupbit.get_ohlcv("KRW-XRP", interval="day", count=count)

    # Extract the closing prices from the fetched data
    bitcoin_prices = bitcoin_data['close'].tolist()
    ethereum_prices = ethereum_data['close'].tolist()
    ripple_prices = ripple_data['close'].tolist()

    # Prepare the chart data
    chart_data = {
        'labels': [(datetime.now() - timedelta(days=(count - i - 1))).strftime('%Y-%m-%d') for i in range(count)],
        'bitcoin_data': bitcoin_prices,
        'ethereum_data': ethereum_prices,
        'ripple_data': ripple_prices,
    }

    return chart_data

def usd_to_krw(url):
    response = requests.get(url)
    response_json = response.json() # [ { } ] 
    usd_price = response_json[0]['basePrice']

    return usd_price

def get_upbit_ticker(url):
    response=requests.get(url)
    response_json=response.json()
    upbit_ticker_dict={}

    for coin in response_json:
        ticker=coin['market']
        name=coin['korean_name']

        if ticker.startswith("KRW"):
            upbit_ticker_dict.update({ticker : name})
    return upbit_ticker_dict

# 업비트 api를 이용한 실시간 시세 함수

def get_upbit_price(url):
    response=requests.get(url)
    response_json=response.json()

    upbit_price_list={}
    upbit_price_rate={}
    upbit_trade_volume={}

    for i in range(len(response_json)):
        trade_price=response_json[i]['trade_price'] #현재가
        prev_closing_price=response_json[i]['prev_closing_price'] #종가
        change_rate=((trade_price-prev_closing_price)/prev_closing_price*100) #변동률
        ticker=response_json[i]['market'] #마켓 전체 코인
        acc_trade_price_24h=response_json[i]['acc_trade_price_24h']#24시간 거래량

        upbit_price_list.update({ticker : format(trade_price,',')})
        upbit_price_rate.update({ticker: round(change_rate, 2)})
        upbit_trade_volume.update({ticker: format(round(acc_trade_price_24h/1000000),',')})

    return upbit_price_list, upbit_price_rate, upbit_trade_volume

def get_bithumb_price(url): 
    response = requests.get(url)
    response_json = response.json()
    
    bithumb_price = {} # 빗썸 현재가
    bithumb_changed_rate = {} # 변동률
    bithumb_trade_volume = {} # 거래량
    data_dict = response_json['data']
    
    for ticker, price_detail in data_dict.items():
        if ticker == 'date':
            continue
        closing_price = price_detail['closing_price']
        fluctate_rate_24H = price_detail['fluctate_rate_24H']
        acc_trade_value_24H = format(round(float(price_detail['acc_trade_value_24H'])/1000000),',')
        
        bithumb_price.update({ticker : format(float(closing_price), ',')})
        bithumb_changed_rate.update({ticker : fluctate_rate_24H})
        bithumb_trade_volume.update({ticker : acc_trade_value_24H })

    return bithumb_price, bithumb_changed_rate, bithumb_trade_volume


def get_coinone_price(url):
    response = requests.get(url)
    response_json = response.json()
    
    coinone_price = {}
    coinone_changed_rate = {}
    coinone_trade_volume = {}

    for ticker,price_detail in response_json.items():
        if 'result' in ticker or 'errorCode' in ticker or 'timestamp' in ticker:
            continue # result, errorcode, timestapm 제외
        last_price = float(price_detail['last']) #현재가
        yesterday_last_price = float(price_detail['yesterday_last']) #종가
        changed_rate = round(((last_price-yesterday_last_price)/yesterday_last_price*100), 2) #변화율
        yesterday_volume = float(price_detail['yesterday_volume'])# 전일 거래가
        yesterday_volume_total = format(round((last_price*yesterday_volume)/1000000, 3),",")
        
        coinone_price.update({ticker : format(last_price, ',')})
        coinone_changed_rate.update({ticker : changed_rate})
        coinone_trade_volume.update({ticker : yesterday_volume_total})

    return coinone_price, coinone_changed_rate, coinone_trade_volume

def get_korbit_price(url):
    response = requests.get(url)
    response_json = response.json()
    
    korbit_price = {}
    korbit_changed_rate = {}
    korbit_trade_volume = {}

    for ticker,price_detail in response_json.items():
        last_price = float(price_detail['last'])
        changed_rate = price_detail['changePercent']
        trade_volume = float(price_detail['volume'])
        trade_volume_total = format(round((trade_volume*last_price)/1000000, 2),",")

        korbit_price.update({ticker : format(last_price, ',')})
        korbit_changed_rate.update({ticker : changed_rate})
        korbit_trade_volume.update({ticker : trade_volume_total})

    return korbit_price, korbit_changed_rate, korbit_trade_volume

def update_chart_data(request):
    time_period = request.GET.get('time_period', 'day')
    chart_data = get_chart_data(time_period)

    return JsonResponse(chart_data)

def index(request):
    time_period = request.GET.get('time_period', 'day')
    chart_data=get_chart_data(time_period)
    usd_price=usd_to_krw("https://quotation-api-cdn.dunamu.com/v1/forex/recent?codes=FRX.KRWUSD")
    upbit_ticker_list=get_upbit_ticker("https://api.upbit.com/v1/market/all")
    upbit_ticker_str=",".join(upbit_ticker_list)

    upbit_price, upbit_change_rate, upbit_trade_volume=get_upbit_price(f"https://api.upbit.com/v1/ticker?markets={upbit_ticker_str}")
    bithumb_price, bithumb_changed_rate, bithumb_trade_volume = get_bithumb_price("https://api.bithumb.com/public/ticker/ALL_KRW")
    coinone_price, coinone_changed_rate, coinone_trade_volume = get_coinone_price("https://api.coinone.co.kr/ticker?currency=all")
    korbit_price, korbit_changed_rate, korbit_trade_volume = get_korbit_price("https://api.korbit.co.kr/v1/ticker/detailed/all")
    context={'chart_data': json.dumps(chart_data),'usd_price' : usd_price, 'upbit_ticker_list': upbit_ticker_list, 'upbit_price': upbit_price, 'upbit_change_rate': upbit_change_rate, 'upbit_trade_volume': upbit_trade_volume, 'bithumb_price':bithumb_price, 'bithumb_changed_rate':bithumb_changed_rate, 'bithumb_trade_volume':bithumb_trade_volume,'coinone_price':coinone_price, 'coinone_changed_rate':coinone_changed_rate, 'coinone_trade_volume':coinone_trade_volume, 'korbit_price':korbit_price, 'korbit_changed_rate':korbit_changed_rate, 'korbit_trade_volume':korbit_trade_volume}
    return render(request, 'index.html', context)


def realtime(request):
    context={'abc': 'hello'}
    return render(request, "realtime.html", context)