# Stock Analysis

(C) 2020 Mark M. Bailey

## About
This repository contains tools for analyzing stock.

## stocks_lookup.py
This script will query the www.worldtradingdata.com API and the Tweepy API for data on a particular stock ticker symbol, and return a stock object with historic price and trading data, as well as sentiment (as measured from the most recent 100 tweets mentioning the stock of interest).  This stock object can be used for other analyses.

## Disclaimer
Note that this tool requires API tokens for both Tweepy and for World Trading Data, which have specific license limitations.  It should be used for research purposes only.
