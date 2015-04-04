There are 3 main components to this strategy:
- **regressions**: the regressionsGen.R script scrapes the past 252 trading days of adjusted closing price data and stores regressions between every combination of the securities in the regressions.csv file
- **dag**: constructs the DAG and finds its critical path
- **strat**: contains the python script we use to trade with the basket
