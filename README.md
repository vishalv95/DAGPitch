#There are 3 main components to this strategy:
- **regressions**: the regressionsGen.R script scrapes the past 252 trading days of adjusted closing price data and stores regressions between every combination of the securities in the regressions.csv fiel
- **DAG**: constructs the DAG and finds its critical path
- **strat**: contains the python script we used to trade with the basket
