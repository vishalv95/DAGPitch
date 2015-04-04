import math
import numpy
import talib
import collections

trendPeriods = 7
rsiIndicator = ta.RSI(timeperiod = trendPeriods)
dollarDelta = 1000

def initialize(context):
    secMgr = SecurityManager()
    
    # Original DAG group
    # DAG: +.96 and up positively correllated
    secMgr.Add("ACT", sid( 8572))
    secMgr.Add("AIZ", sid( 25955))
    secMgr.Add("AMP", sid( 27676))
    secMgr.Add("ECL", sid( 2427))
    secMgr.Add("ETFC",sid( 15474))
    secMgr.Add("LLL", sid( 18738))
    secMgr.Add("LMT", sid( 12691))
    secMgr.Add("LNC", sid( 4498))
    secMgr.Add("MA",  sid( 32146))
    secMgr.Add("MMC", sid( 4914))
    secMgr.Add("NOC", sid( 5387))
    secMgr.Add("PFG", sid( 23151))
    secMgr.Add("PNR", sid( 6082))
    secMgr.Add("PRU", sid( 23328))
    secMgr.Add("SNA", sid( 6976))
    secMgr.Add("TJX", sid( 7457))
    secMgr.Add("TMK", sid( 7488))
    secMgr.Add("TMO", sid( 7493))
    
    context.SecMgr = secMgr
    context.period = 0
    context.runningPnL = 0.0

    set_commission(commission.PerTrade(cost=1.0))
    set_slippage(TradeAtTheOpenSlippageModel(.1))
    
def handle_data(context, data):
    context.SecMgr.Update(data)    
    context.period += 1
    
    if (context.period < trendPeriods):
        return
#    checks to see if 1) profit since last check has exceeded dollarDelta or 2) if we aren't in any positions. If so, rebalance and reset the profit counter and order stocks based on weight.
    if (abs(context.portfolio.pnl - context.runningPnL) > dollarDelta or len(context.portfolio.positions) == 0):
        context.runningPnL = context.portfolio.pnl        
        for security in context.SecMgr.GetSecurities():
            if (security.Enabled):
                order_target_percent(security.Sid, security.Weight)
            else:
                order_target_percent(security.Sid, 0.0)
        
    #record(PnL=context.portfolio.pnl)
    record(Leverage = context.account.leverage)
    
################################################################                
class SecurityManager(object):
    '''Class to wrap securities'''

    def __init__(this):
        this.stockList = {}
        
    def __str__(this):
        toString = "\tSymbols:{0}\n".format(this.stockList.keys())
        return toString 
    
    def Count(this):
        return len(this.GetSecurities())
    
    def Add(this, symbol, sid):
         this.stockList[symbol] = Security(symbol, sid)
    
    def Update(this, data):
#    updates RSI values for each stock and picks out the maximum, minimum, and average RSI values of the portfolios.
        rsiValues = rsiIndicator(data)
        maxRsi = numpy.max(rsiValues)
        minRsi = numpy.min(rsiValues)
        avgRsi = numpy.mean(rsiValues)
        if (numpy.isnan(maxRsi) or numpy.isnan(minRsi) or numpy.isnan(avgRsi)):
            return

#     Lines 88-124 Rebalances based on extremes of RSI, sell the highest, buy the lowest.

#     Checks if the average RSI value is trending towards high, in which case we'll want to adjust weights.
        if (avgRsi > 50):
            trendAdjuster = .05
        else:
            trendAdjuster = -.05

        totalWeight = 0.0
        count = 0.0
        for sec in this.stockList.values():
            if (sec.Sid not in data):
                sec.Weight = 0.0
                sec.Enabled = False
                continue
            sec.UpdatePrices(data)
            if (numpy.isnan(rsiValues[sec.Sid])):
                continue
#        Short the stocks that have high RSI
            if (rsiValues[sec.Sid] > maxRsi - 5):
                sec.SetWeight(-.1 + trendAdjuster)
                totalWeight += abs(-.1 + trendAdjuster)
                count += 1
#        Long the stocks that have low RSI   
            elif(rsiValues[sec.Sid] < minRsi + 5):
                sec.SetWeight(.1 + trendAdjuster)
                totalWeight += abs(.1 + trendAdjuster)
                count += 1
            else:
                sec.SetWeight(0)
        if (count == 0):
            return
#        Adjust weight if total weight is < 1. This way you utilize all assets at any given time        
        weightAdjustment = (1.0 - totalWeight) / count
        
        for sec in this.stockList.values():
            if (sec.Weight < 0.0):
                sec.Weight -= weightAdjustment
            elif (sec.Weight > 0.0): 
                sec.Weight += weightAdjustment
        
    def GetSecurities(this):
        return this.stockList.values()

   
#################################################################
class Security(object):
    '''Class to wrap security'''

    def __init__(this, symbol, sid):
        this.Symbol = symbol
        this.Sid = sid
        this.Weight = 0.0
        this.Enabled = True
        this.Open =  collections.deque(maxlen=trendPeriods) 
        this.High =  collections.deque(maxlen=trendPeriods) 
        this.Low =   collections.deque(maxlen=trendPeriods)  
        this.Close = collections.deque(maxlen=trendPeriods)        
            
    def __str__(this):
        toString = "\tSymbol:{0} weight:{1}\n".format(this.Symbol, this.Weight)
        return toString 
    
    def UpdatePrices(this, data):
        this.Open.append(data[this.Sid].open_price)
        this.High.append(data[this.Sid].high)
        this.Low.append(data[this.Sid].low)
        this.Close.append(data[this.Sid].close_price)
        print(this, data[this.Sid].open_price)
            
    def SetWeight(this, rsiValue):
        this.Weight = rsiValue
        this.Enabled = True
        pass
    
########################################################
#Model to account for slippage between open and close prices
class TradeAtTheOpenSlippageModel(slippage.SlippageModel):
    def __init__(this, fractionOfOpenCloseRange):
        this.fractionOfOpenCloseRange = fractionOfOpenCloseRange

    def process_order(this, trade_bar, order):
        openPrice = trade_bar.open_price
        closePrice = trade_bar.price
        ocRange = closePrice - openPrice
        ocRange = ocRange * this.fractionOfOpenCloseRange
        targetExecutionPrice = openPrice + ocRange
            
        # Create the transaction using the new price we've calculated.
        return slippage.create_transaction(
            trade_bar,
            order,
            targetExecutionPrice,
            order.amount
        )
'''
Archive

    # Original DAG group
    # DAG: +.96 and up positively correllated
    #secMgr.Add("ACT", sid( 8572))
    #secMgr.Add("AIZ", sid( 25955))
    #secMgr.Add("AMP", sid( 27676))
    #secMgr.Add("ECL", sid( 2427))
    #secMgr.Add("ETFC",sid( 15474))
    #secMgr.Add("LLL", sid( 18738))
    #secMgr.Add("LMT", sid( 12691))
    #secMgr.Add("LNC", sid( 4498))
    #secMgr.Add("MA",  sid( 32146))
    #secMgr.Add("MMC", sid( 4914))
    #secMgr.Add("NOC", sid( 5387))
    #secMgr.Add("PFG", sid( 23151))
    #secMgr.Add("PNR", sid( 6082))
    #secMgr.Add("PRU", sid( 23328))
    #secMgr.Add("SNA", sid( 6976))
    #secMgr.Add("TJX", sid( 7457))
    #secMgr.Add("TMK", sid( 7488))
    #secMgr.Add("TMO", sid( 7493))

    # DAG: .92+ correlated
    #secMgr.Add("AIZ ", sid(25955))
    #secMgr.Add("AZO ", sid(693))  
    #secMgr.Add("FRX ", sid(3014)) 
    #secMgr.Add("GNW ", sid(26323))
    #secMgr.Add("HP  ", sid(3647)) 
    #secMgr.Add("HRS ", sid(3676)) 
    #secMgr.Add("IR  ", sid(4010)) 
    #secMgr.Add("JCI ", sid(4117)) 
    #secMgr.Add("MS  ", sid(17080))
    #secMgr.Add("PBI ", sid(5773)) 
    #secMgr.Add("PNR ", sid(6082)) 
    #secMgr.Add("PRGO", sid(6161)) 
    #secMgr.Add("PX  ", sid(6272)) 
    #secMgr.Add("R   ", sid(6326)) 
    #secMgr.Add("STZ ", sid(24873))
    #secMgr.Add("TJX ", sid(7457)) 
    #secMgr.Add("TMO ", sid(7493)) 
    #secMgr.Add("TYC ", sid(7679)) 
    #secMgr.Add("X   ", sid(8329)) 
    #secMgr.Add("ZMH ", sid(23047))
    
    # WealthFront ETF selection
    #secMgr.Add("VTI", sid(22739))# US Stocks
    #secMgr.Add("VEA", sid(34385))# Foreign Stocks
    #secMgr.Add("VWO", sid(27102))# Emerging Markets
    #secMgr.Add("VNQ", sid(26669))# Real Estate
    #secMgr.Add("DJP", sid(24700))# Natural Resources
    #secMgr.Add("BND", sid(33652))# Bonds
    
    # X type ETFs group
    #secMgr.Add("XLB", sid(19654)) # Materials Select Sector SPDR
    #secMgr.Add("XLE", sid(19655)) # Energy Select Sector SPDR                
    #secMgr.Add("XLF", sid(19656)) # Financial Select Sector SPDR             
    #secMgr.Add("XLI", sid(19657)) # Industrial Select Sector SPDR            
    #secMgr.Add("XLK", sid(19658)) # Technology Select Sector SPDR            
    #secMgr.Add("XLP", sid(19659)) # Consumer Staples Select Sector SPDR      
    #secMgr.Add("XLU", sid(19660)) # Utilities Select Sector SPDR             
    #secMgr.Add("XLV", sid(19661)) # Healthcare Select Sector SPDR            
    #secMgr.Add("XLY", sid(19662)) # Consumer Discretionary Select Sector SPDR
    #secMgr.Add("AGG", sid(25485)) # ISHARES CORE U.S. AGGREGATE BONDS     
    
    # DAG: Uncorrelated
    #secMgr.Add("INTC", sid(3951))
    #secMgr.Add("ITW ", sid(4080))
    #secMgr.Add("LLL ", sid(18738))
    #secMgr.Add("LO  ", sid(36346))
    #secMgr.Add("MA  ", sid(32146))
    #secMgr.Add("MO  ", sid(4954))
    #secMgr.Add("MON ", sid(22140))
    #secMgr.Add("MSFT", sid(5061))
    #secMgr.Add("MSI ", sid(4974))
    #secMgr.Add("OMC ", sid(5651))
    #secMgr.Add("PBI ", sid(5773))
    #secMgr.Add("PX  ", sid(6272))
    #secMgr.Add("ROK ", sid(6536))
    #secMgr.Add("SNA ", sid(6976))
    #secMgr.Add("STZ ", sid(24873))
    #secMgr.Add("TMK ", sid(7488))
    #secMgr.Add("TMO ", sid(7493))
    #secMgr.Add("UNM ", sid(7797))
    #secMgr.Add("VMC ", sid(7998))
    #secMgr.Add("VRSN", sid(18221))
    
    # DAG: -.65 to -.96 negatively correlated
    #secMgr.Add("AMZN", sid(16841) )
    #secMgr.Add("APC ", sid(455))
    #secMgr.Add("AVP ", sid(660))
    #secMgr.Add("CA  ", sid(1209))
    #secMgr.Add("CELG", sid(1406))
    #secMgr.Add("DGX ", sid(16348))
    #secMgr.Add("DNR ", sid(15789))
    #secMgr.Add("DO  ", sid(13635))
    #secMgr.Add("F   ", sid(2673))
    #secMgr.Add("FDO ", sid(2760))
    #secMgr.Add("FE  ", sid(17850))
    #secMgr.Add("HCN ", sid(3488))
    #secMgr.Add("HCP ", sid(3490))
    #secMgr.Add("JBL ", sid(8831))
    #secMgr.Add("JCP ", sid(4118))
    #secMgr.Add("MCD ", sid(4707))
    #secMgr.Add("NEM ", sid(5261))
    #secMgr.Add("NTAP", sid(13905))
    #secMgr.Add("TDC ", sid(34661))
    #secMgr.Add("UTX ", sid(7883))
    
    # Original DAG group
    # DAG: +.96 and up positively correllated
    #secMgr.Add("ACT", sid( 8572))
    #secMgr.Add("AIZ", sid( 25955))
    #secMgr.Add("AMP", sid( 27676))
    #secMgr.Add("ECL", sid( 2427))
    #secMgr.Add("ETFC",sid( 15474))
    #secMgr.Add("LLL", sid( 18738))
    #secMgr.Add("LMT", sid( 12691))
    #secMgr.Add("LNC", sid( 4498))
    #secMgr.Add("MA",  sid( 32146))
    #secMgr.Add("MMC", sid( 4914))
    #secMgr.Add("NOC", sid( 5387))
    #secMgr.Add("PFG", sid( 23151))
    #secMgr.Add("PNR", sid( 6082))
    #secMgr.Add("PRU", sid( 23328))
    #secMgr.Add("SNA", sid( 6976))
    #secMgr.Add("TJX", sid( 7457))
    #secMgr.Add("TMK", sid( 7488))
    #secMgr.Add("TMO", sid( 7493))

    # DAG: .92+ correlated
    #secMgr.Add("AIZ ", sid(25955))
    #secMgr.Add("AZO ", sid(693))  
    #secMgr.Add("FRX ", sid(3014)) 
    #secMgr.Add("GNW ", sid(26323))
    #secMgr.Add("HP  ", sid(3647)) 
    #secMgr.Add("HRS ", sid(3676)) 
    #secMgr.Add("IR  ", sid(4010)) 
    #secMgr.Add("JCI ", sid(4117)) 
    #secMgr.Add("MS  ", sid(17080))
    #secMgr.Add("PBI ", sid(5773)) 
    #secMgr.Add("PNR ", sid(6082)) 
    #secMgr.Add("PRGO", sid(6161)) 
    #secMgr.Add("PX  ", sid(6272)) 
    #secMgr.Add("R   ", sid(6326)) 
    #secMgr.Add("STZ ", sid(24873))
    #secMgr.Add("TJX ", sid(7457)) 
    #secMgr.Add("TMO ", sid(7493)) 
    #secMgr.Add("TYC ", sid(7679)) 
    #secMgr.Add("X   ", sid(8329)) 
    #secMgr.Add("ZMH ", sid(23047))
    
    # Alpha selection from SP250
    #secMgr.Add("FOXA",sid(12213))
    #secMgr.Add("FRX" ,sid(3014))
    #secMgr.Add("GAS" ,sid(3103))
    #secMgr.Add("GCI" ,sid(3128))
    #secMgr.Add("GD"  ,sid(3136))
    #secMgr.Add("GE"  ,sid(3149))
    #secMgr.Add("GIS" ,sid(3214))
    #secMgr.Add("GLW" ,sid(3241))
    #secMgr.Add("GPC" ,sid(3306))
    #secMgr.Add("GPS" ,sid(3321))
    #secMgr.Add("GT"  ,sid(3384))
    #secMgr.Add("GWW" ,sid(3421))
    #secMgr.Add("HAL" ,sid(3443))
    #secMgr.Add("HAS" ,sid(3460))
    #secMgr.Add("HBAN",sid(3472))
    #secMgr.Add("HCN" ,sid(3488))
    #secMgr.Add("HCP" ,sid(3490))
    #secMgr.Add("HD"  ,sid(3496))
    #secMgr.Add("HES" ,sid(216))
    #secMgr.Add("HON" ,sid(25090))
    #secMgr.Add("HP"  ,sid(3647))
'''