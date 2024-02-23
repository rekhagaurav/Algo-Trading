import sys
from datetime import datetime, time, timedelta
from NorenRestApiPy.NorenApi import NorenApi
from algo import app

# login page
class ShoonyaApiPy(NorenApi):
    def __init__(self):
        NorenApi.__init__(self, host='https://api.shoonya.com/NorenWClientTP/', websocket='wss://api.shoonya.com/NorenWSTP/')
        self.get = None
        global api
        api = self
import logging
import pyotp
logging.basicConfig(level=logging.DEBUG)
api = ShoonyaApiPy()

#__User input__

EntryDiffPrice  = 2     # in Rs , to buy
ExitDiffPrice   = 3     # in Rs , to sell
minBuyQty       = 1     # min qty to buy
MaxOpenPosition = 3     # Max Qty
StopLossInRs    = 10    # in rs , to book stop loss
duration        = 1     # in min

# user details

token = '7O66IG4Y23562OZ3ZC3B2Z66S5T37265'
otp = pyotp.TOTP(token).now()
user = 'FA71897'
pwd = 'Rajesh@123'
factor2 = otp
vc = 'FA71897_U'
app_key = '036e0ee3e72de505cd7fe9cbcf16c7e8'
imei = 'abc1234'
ret1 = api.login(userid=user, password=pwd, twoFA=factor2, vendor_code=vc, api_secret=app_key, imei=imei)
print(ret1)


exch  = 'NSE'
token = '3045'
ret2 = api.get_security_info(exchange='NSE', token='3045')
api.searchscrip(exchange='NSE', searchtext='REL')
print(ret2)

exch  = 'NSE'
token = '3045'
ret3 = api.get_quotes(exchange='NSE', token='3045')
print(ret3)

lastBusDay = datetime.datetime.today()
lastBusDay = lastBusDay.replace(hour=0, minute=0, second=0, microsecond=0)
ret4 = api.get_time_price_series(exchange='NSE', token='3045', starttime=lastBusDay.timestamp(), interval=5)
print(ret4)

ret5 =api.get_daily_price_series(exchange="NSE",tradingsymbol="SBIN-EQ",startdate="457401600",enddate="480556800")
print(ret5)

ret6 = api.place_order(buy_or_sell='B', product_type='C',
                        exchange='NSE', tradingsymbol='SBIN-EQ',
                        quantity=1, discloseqty=0,price_type='SL-LMT', price=200.00, trigger_price=199.50,
                        retention='DAY', remarks='my_order_001')
print(ret6)

time.sleep(0.4)

# Initialize sell order parameters
buyOrderParams = {
    "variety": "NORMAL",
    "tradingsymbol": "SBIN-EQ",
    "symboltoken": "3045",
    "transactiontype": "BUY",
    "exchange": "NSE",
    "ordertype": "MARKET",
    "producttype": "INTRADAY",
    "duration": "DAY",
    "price": "0",
    "squareoff": "0",
    "stoploss": "0",
    "quantity": minBuyQty
}
sellOrderParams = {
    "variety": "NORMAL",
    "tradingsymbol": "SBIN-EQ",
    "symboltoken": "3045",
    "transactiontype": "SELL",
    "exchange": "NSE",
    "ordertype": "MARKET",
    "producttype": "INTRADAY",
    "duration": "DAY",
    "price": "0",
    "squareoff": "0",
    "stoploss": "0",
    "quantity": minBuyQty
}


# Initial cash check
initialCash = NorenApi.rmsLimit().get("data").get("availablecash")
time.sleep(0.4)
if initialCash is None:
    initialCash = 0
print("Initial available Cash =", initialCash)

start_time = datetime.now()
EndTime = start_time + timedelta(minutes=duration)
print("EndTime:", EndTime)

#===================   start Algo trade =====================
NorenApi.placeOrder(buyOrderParams)    # buy first order
time.sleep(0.4)
orderbook = NorenApi.orderBook()
time.sleep(0.4)
for item in orderbook.get('data'):
    obStatus = item.get('orderstatus')
    obText = item.get('text')
    print("Orderbook Status=", obStatus, ", text=", obText)
time.sleep(0.4)


#----------------- check current position -------------
position = NorenApi.position()
time.sleep(0.4)
data = position.get('data')
qty = 0;
for item in data:
        qty = item.get("netqty")
        buyprice = item.get("avgnetprice")
        print("Quantity:", qty)
        print("Average Net Price:", buyprice)

# print("Initial Holding position QTY =", position)
if qty is None:
    qty = 0
print("Initial Holding position QTY =", qty)

sellOrderParams["quantity"] = minBuyQty
# Fetch LTP data
time.sleep(1)
x = NorenApi.ltpData("NSE", "SBIN-EQ", "3045")
time.sleep(0.4)
ltp = float(x.get('data').get('ltp'))
print("LTP =", ltp)

# Get position
time.sleep(0.4)
position = NorenApi.position()
time.sleep(0.4)
data = position.get('data')
for item in data:
    qty = item.get("netqty")
    buyprice = item.get("avgnetprice")
    print("Quantity:", qty)
    print("Average Net Price:", buyprice)

    if qty is None:
        qty = 0
    if buyprice is None:
        buyprice = 0

    # calculate avgPrice
if ltp < float(buyprice) - float(StopLossInRs):
    sellOrderParams["quantity"] = qty
    time.sleep(0.4)
    NorenApi.placeOrder(sellOrderParams)
    time.sleep(0.4)
    print("Stop loss hit : ", qty, "qty sold at market price")
    sys.exit()

if ltp > (float(buyprice) + float(ExitDiffPrice)) and (float(qty) > 0):  # book profit
    time.sleep(0.4)
    NorenApi.placeOrder(sellOrderParams)
    time.sleep(0.4)
    print("Profit booked : ", qty, "qty sold at =", ltp, " market price, buyprice=", buyprice, "ExitDiffPrice=",
          ExitDiffPrice)

if (ltp < (float(buyprice) - float(EntryDiffPrice))) and (float(qty) <= float(MaxOpenPosition)):
    time.sleep(0.4)
    NorenApi.placeOrder(buyOrderParams)
    time.sleep(0.4)
    print("Purchased ", qty, "at ", ltp)

# check end time
current_time = datetime.now()
if current_time > EndTime:
    timespent = current_time - start_time
    print("timespent:", timespent, "start time:", start_time, "current_time:", current_time)
    # Place sell order for all QTY
    time.sleep(0.4)
    position = NorenApi.position()
    time.sleep(0.4)
    data = position.get('data')
    for item in data:
        qty = item.get("netqty")
        buyprice = item.get("avgnetprice")
        print("Quantity:", qty)
        print("Average Net Price:", buyprice)

    if qty is None:
        qty = 0

    if float(qty) > 0:
        sellOrderParams["quantity"] = qty
        sellOrderResponse = NorenApi.placeOrder(sellOrderParams)
        time.sleep(0.4)
        if sellOrderResponse is not None and 'data' in sellOrderResponse and 'orderid' in sellOrderResponse['data']:
            order_id = sellOrderResponse['data']['orderid']
            print("End time reached , Sell order placed successfully. Order ID:", order_id)
        else:
            print("End time reached , Failed to place sell order.")
    else:
        print("End time reached , No quantity to sell.")
    sys.exit()


# End of loop
time.sleep(1)
balanceCash = NorenApi.rmsLimit().get("data").get("availablecash")
time.sleep(0.4)
if balanceCash is None:
    balanceCash = 0

print("Balance Cash =", balanceCash)

# Calculate profit
balanceCash = float(balanceCash)
initialCash = float(initialCash)
profit = balanceCash - initialCash
print("Total profit =", profit)

time.sleep(1)
# Logout
try:
    time.sleep(0.4)
    print("Logout Successful")
except Exception as e:
    print("Logout failed: {}".format(e.message))


