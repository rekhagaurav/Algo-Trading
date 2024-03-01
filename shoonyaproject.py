import sys,time
from datetime import datetime,  timedelta

import data
import results
from NorenRestApiPy.NorenApi import NorenApi


# login page
class ShoonyaApiPy(NorenApi):
    def __init__(self):
        NorenApi.__init__(self, host='https://api.shoonya.com/NorenWClientTP/', websocket='wss://api.shoonya.com/NorenWSTP/')
        self.get = None
        global api
        api = self
        print(self)

    def get_ltp_data(self, param, param1, param2):
        pass


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

token = ''
otp = pyotp.TOTP(token).now()
user = ''
pwd = ''
factor2 = otp
vc = ''
app_key = ''
imei = ''
ret1 = api.login(userid=user, password=pwd, twoFA=factor2, vendor_code=vc, api_secret=app_key, imei=imei)
print("login result=",ret1)

exch  = 'NSE'
token = '3045'
# quote = api.get_quotes(exchange='NSE', token='3045')
# print("quote=",quote)

# lastBusDay = datetime.datetime.today()
# lastBusDay = lastBusDay.replace(hour=0, minute=0, second=0, microsecond=0)
# ret4 = api.get_time_price_series(exchange='NSE', token='3045', starttime=lastBusDay.timestamp(), interval=5)
# print(ret4)
#
# ret5 =api.get_daily_price_series(exchange="NSE",tradingsymbol="SBIN-EQ",startdate="457401600",enddate="480556800")
# print(ret5)



#time.sleep(0.4)

# Initialize sell order parameters

buyOrderParams = {
    "buy_or_sell" : "B",
    "producttype": "INTRADAY",
    "exchange": "NSE",
    "tradingsymbol": "SBIN-EQ",
    'quantity': 'minBuyQty',
    'discloseqty': '0',
    "ordertype": "MARKET",
    'price':'200.00',
    'trigger_price': '199.50',
    "duration": "DAY",
    'remarks': 'my_order_001',
    "variety": "NORMAL",
    "symboltoken": "3045",
}
sellOrderParams = {
    "variety": "NORMAL",
    "tradingsymbol": "SBIN-EQ",
    "symboltoken": "3045",
    "transactiontype": "SELL",
    "exchange": "NSE",
    "ordertype": "MARKET",
    'discloseqty': '0',
    "producttype": "INTRADAY",
    "duration": "DAY",
    "price": "0",
    "squareoff": "0",
    "stoploss": "0",
    "quantity": "minBuyQty"
}


# Initial cash check
initialCash = api.get_limits()
time.sleep(0.4)
if initialCash is None:
    initialCash = 0
print("Initial available Cash =", initialCash['cash'])

start_time = datetime.now()
EndTime = start_time + timedelta(minutes=duration)
print("EndTime:", EndTime)

# orderStatus= api.place_order(buy_or_sell='B', product_type='i',
#                         exchange='NSE', tradingsymbol='SBIN-EQ',
#                         quantity=1, discloseqty=0,price_type='SL-LMT', price=200.00, trigger_price=199.50,
#                         retention='DAY', remarks='my_order_001')
# print("orderStatus=", orderStatus)
orderStatus= api.place_order(buy_or_sell='B', product_type='C',
                         exchange='NSE', tradingsymbol='SBIN-EQ',
                         quantity=1, discloseqty=0,price_type='MKT', price=500.00,
                         retention='DAY', remarks='my_order_001')
#print("orderStatus=", orderStatus)    # buy first order
print("orderStatus=", orderStatus)
time.sleep(0.4)


#===================   start Algo trade =====================

order_book = api.get_order_book()
print("order_book=", order_book)
results=[]
time.sleep(0.4)
for item in order_book:
    Status = item.get('status')
    exch = item.get('exch')
    tsym = item.get('tsym')
    qty = item.get('qty')
    rejreason = item.get('rejreason')

    result = (Status, exch, tsym, qty, rejreason)
    results.append(result)
print(results)
time.sleep(0.4)


#----------------- check current position -------------
position = api.get_positions()
time.sleep(0.4)
data = api.get_positions()
if position is not None:
    qty = 0
    results=[]
    for item in position:

        qty = item.get("Quantity")
        buyprice = item.get("avgnetprice")
        result = ("Quantity:", qty, "Average Net Price:", buyprice)
        results.append(result)
print(results)


#print("Initial Holding position QTY =", position)
if qty is None:
    qty = 0
print("Initial Holding position QTY =", qty)

sellOrderParams["quantity"] = minBuyQty
# Fetch LTP data
time.sleep(1)
x = api.get_ltp_data("NSE", "SBIN-EQ", "3045")
time.sleep(0.4)
if x is not None:
    ltp = float(x.get('data',{}).get('ltp',0))
    print("LTP =", ltp)
if position is not None:
    data = position.get('data')
    if data is not None:
        qty = 0
        results = []
        for item in data:
            qty = item.get("Quantity")
            buyprice = item.get("avgnetprice")
            result = ("Quantity:", qty, "Average Net Price:", buyprice)
            results.append(result)
        print(results)
    if qty is None:
        qty = 0
    if buyprice is None:
        buyprice = 0

    # calculate avgPrice
    if ltp < float(buyprice) - float(StopLossInRs):
        sellOrderParams["quantity"] = qty
        time.sleep(0.4)
        api.place_Order(sellOrderParams)
        time.sleep(0.4)
    print("Stop loss hit : ", qty, "qty sold at market price")
    sys.exit()

    if ltp > (float(buyprice) + float(ExitDiffPrice)) and (float(qty) > 0):  # book profit
        time.sleep(0.4)
        api.place_Order(sellOrderParams)
        time.sleep(0.4)
    print("Profit booked : ", qty, "qty sold at =", ltp, " market price, buyprice=", buyprice, "ExitDiffPrice=",
          ExitDiffPrice)

    if (ltp < (float(buyprice) - float(EntryDiffPrice))) and (float(qty) <= float(MaxOpenPosition)):
        time.sleep(0.4)
        api.placeOrder(buyOrderParams)
        time.sleep(0.4)
    print("Purchased ", qty, "at ", ltp)

# check end time
current_time = datetime.now()
if current_time > EndTime:
    timespent = current_time - start_time
    print("timespent:", timespent, "start time:", start_time, "current_time:", current_time)
    # Place sell order for all QTY
    time.sleep(0.4)
    position = api.position()
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
        sellOrderResponse = api.placeOrder(sellOrderParams)
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
limits_data = api.get_limits()

limits_data = api.get_limits()

if limits_data is not None:
    available_cash = limits_data.get("data", {}).get("availablecash")
    if available_cash is not None:
        balance_cash = float(available_cash)
        print("Available Cash =", balance_cash)
    else:
        print("Error: 'availablecash' not found in limits data.")
else:
    print("Error: Unable to fetch limits data.")


# Calculate profit
#balance_Cash = float(available_cash)
#initialCash = float(initialCash)
#profit = balance_Cash - initialCash
#print("Total profit =", profit)

#time.sleep(1)
# Logout
#try:
#    time.sleep(0.4)
#    print("Logout Successful")
#except Exception as e:
#    print("Logout failed: {}".format(e.message))


