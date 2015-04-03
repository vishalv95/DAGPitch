library(tseries)
library(MASS)
#Load Security data
companies <- read.table('sp500-symbol-list.txt')
colnames(companies) <- c('symbol')
prices <- matrix(0, 252, 0)
for (comp in companies$symbol){
  price <- data.frame(get.hist.quote(comp, quote='Adj', start='2014-04-03'))
  colnames(price) <- comp
  max.len <- 252
  rep <- max.len - length(price[,comp])
  price <- c(price[,comp], rep(NA, if(rep > 0) rep else 0))
  prices <- cbind(prices,price)
  colnames(prices)[length(colnames(prices))] <- comp
}

regressions <- data.frame(matrix(0, 0, 3))
for(compA in colnames(prices)){
  for(compB in colnames(prices)){
    if(compA != compB){
      row <- matrix(0, 1, 3)
      row[1,1] <- compA
      row[1,2] <- compB
      row[1,3] <- cor(prices[,compA], prices[,compB])
      regressions <- rbind(regressions,row)
    }
  }
}
colnames(regressions) <- c('comp_A', 'comp_B', 'r-value')
