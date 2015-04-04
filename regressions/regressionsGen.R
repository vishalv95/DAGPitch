library(tseries)
library(zoo)

#Load symbol data for the s&p 500
companies <- read.table('S&P.txt')
colnames(companies) <- c('symbol')
#set lookback period
years <- 1 
#Scrapes the past 252*years trading days for adjusted closing price data for s&p 500 companies
prices <- matrix(0, 252 * years, 0)
beg <- Sys.Date() - floor(years*365.25)
for (comp in companies$symbol){
  #Load price data from Yahoo Finance and handle missing data
  price <- try(get.hist.quote(comp, quote='Adj', start=beg))
  if(class(price)=="try-error") 
    next
  price <- data.frame(price)
  colnames(price) <- comp
  
  #Fill missing days with NAs
  max.len <- 252 * years
  rep <- max.len - length(price[,comp])
  price <- c(price[,comp], rep(NA, if(rep > 0) rep else 0))
  
  #Bind this company's data to rest of pricing data
  prices <- cbind(prices,price)
  colnames(prices)[length(colnames(prices))] <- comp
}

#write price data to prices.csv
write.csv(data.frame(prices),'prices.csv',row.names=F)

#Generate matrix of all pair combinations of companies we have data for  
combs <- combn(colnames(prices),2)
regressions <- data.frame(matrix(0, ncol(combs), 4))
colnames(regressions) <- c('comp_A', 'comp_B', 'r_value', 'n')

#Initialize combinations on regressions data frame
regressions[,1] <- combs[1,]
regressions[,2] <- combs[2,]

#Fill in regressions 
beg <- Sys.time()
for(i in 1:ncol(combs)){
  compA <- combs[1,i]
  compB <- combs[2,i]
  regressions[i,3] <- cor(prices[,compA], prices[,compB], use="pairwise.complete.obs")
  regressions[i,4] <- min(length(na.omit(prices[,compA])), length(na.omit(prices[,compA])))
  
  #status check and backup
  #?if(i%%100==0) print(i) 
  #?if(i%%1000 == 0) print(Sys.time() - beg)
  if(i%%10000 == 0){
    write.csv(regressions, 'regressions.csv', row.names=F)
    p <- i / ncol(combs) 
    t <- (Sys.time() - beg)
    print('Writing Backup...')
    print(paste(ceiling(p * 100),'Percent Complete')) 
#     print(paste(ceiling((t / p - t) / 60),  'minutes remaining'))
  }
}
print(paste('completed in', Sys.time() - beg, 'minutes'))

# write regressions data to regressions.csv
write.csv(regressions, 'regressions.csv', row.names=F)

#Missing Symbols
write.table(colnames(prices), 'retrieved.txt', row.names=F, col.names=F, quote=F)
write.table(setdiff(companies$symbol, colnames(prices)), 'missing.txt', row.names=F, col.names=F, quote=F)

