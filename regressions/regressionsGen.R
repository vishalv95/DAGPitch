library(tseries)
library(zoo)

#Load Security data
companies <- read.table('sp500-symbol-list.txt')

colnames(companies) <- c('symbol')
prices <- matrix(0, 252, 0)
for (comp in companies$symbol){
  price <- try(myghq(comp, quote='Adj', start='2014-04-03'))
  if(class(price)=="try-error") 
    next
  price <- data.frame(price)
  colnames(price) <- comp
  
  #What to do if the stock price has no data here?
  max.len <- 252
  rep <- max.len - length(price[,comp])
  price <- c(price[,comp], rep(NA, if(rep > 0) rep else 0))
  prices <- cbind(prices,price)
  colnames(prices)[length(colnames(prices))] <- comp
}

combs <- combn(colnames(prices),2)
# write.csv(data.frame(combs),'pairs.csv')
regressions <- data.frame(matrix(0, ncol(combs), 4))
# beg <- Sys.Time()
for(c in 1:ncol(combs)){
  compA <- combs[1,c]
  compB <- combs[2,c]
  regressions[c,1] <- compA
  regressions[c,2] <- compB
  regressions[c,3] <- cor(prices[,compA], prices[,compB], use="pairwise.complete.obs")
  regressions[c,4] <- min(length(na.omit(prices[,compA])), length(na.omit(prices[,compA])))
  if(c%%100==0) print(c) 
}
# end <- Sys.Time()
# print(end - beg)

colnames(regressions) <- c('comp_A', 'comp_B', 'r_value', 'n')
write.csv(regressions, 'regressions.csv', row.names=F)