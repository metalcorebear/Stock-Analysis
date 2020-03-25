# -*- coding: utf-8 -*-
"""
Created on Tue Dec 31 14:28:52 2019

@author: metalcorebear
"""

import requests
import numpy as np
import json
import tweepy
from textblob import TextBlob
from datetime import date as datemethod

"""
All API parameters must be in a json file.  Should be in the following
format:
    {"access_token":"XXXXX", "consumer_key":"XXXXX", 
    "access_token_secret":"XXXXX", "consumer_secret":"XXXXX", 
    "STOCK_API_KEY":"XXXXX"}

API keys for Tweepy can be generated via a Twitter developer account.
Stock API keys can be generated here: https://www.worldtradingdata.com
"""

#Tweepy functions
def get_tweets(query, api):
    
    # call twitter api to fetch tweets
    q= '$' + str(query)
    
    fetched_tweets = api.search(q, count=100)
        
    # parsing tweets one by one
    out_tweets = []
    for tweet in fetched_tweets:
        # empty dictionary to store required params of a tweet
        parsed_tweet = {}
        # saving text of tweet
        text = tweet.text
        user = tweet.user.screen_name
        date0 = tweet.created_at
        date = datemethod.strftime(date0, '%Y-%m-%d')
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        parsed_tweet = dict([('user',user), ('text',text), ('date',date), 
                             ('polarity',polarity), ('subjectivity',subjectivity), 
                             ('entities',query)])
        out_tweets.append(parsed_tweet)
    return out_tweets

def get_sentiment(out_tweets):
    polarity_measures = []
    subjectivity_measures = []
    for tweet in out_tweets:
        polarity_measures.append(tweet['polarity'])
        subjectivity_measures.append(tweet['subjectivity'])
    subjectivity_array = np.array(subjectivity_measures)
    polarity_array = np.array(polarity_measures)
    mean_subjectivity = np.mean(subjectivity_array)
    mean_polarity = np.mean(polarity_array)
    var_subjectivity = np.var(subjectivity_array)
    var_polarity = np.var(polarity_array)
    output = {'subjectivity':mean_subjectivity, 'polarity':mean_polarity, 'subjectivity_var':var_subjectivity,
              'polarity_var':var_polarity}
    return output

#Stock functions
def build_url_stock(API_KEY, TKR, range_, interval):
    base_url = 'https://intraday.worldtradingdata.com/api/v1/intraday?symbol='
    symbol = TKR
    url = base_url + symbol + '&interval=' + str(interval) + '&range=' + str(range_) + '&sort=asc&api_token=' + API_KEY
    return url
    
def get_json(url):
    page = requests.get(url)
    output = page.json()
    return output

def get_closing_prices_and_volumes(output):
    data = output['intraday']
    dates_0 = list(data.keys())
    dates_0.sort()
    dates = []
    for i in dates_0:
        dates.append(i.replace('-',''))
    closing_prices = []
    volumes = []
    for date in dates_0:
        closing_prices.append(float(data[date]['close']))
        volumes.append(float(data[date]['volume']))
    return dates, closing_prices, volumes

def beta(s,e):
    b = np.cov(s,e)[0][1] / np.var(e)
    return b

class stock_object():

    def __init__(self, key_location, TKR, range_=7, interval=60, EX='^IXIC'):
        
        with open(key_location, 'r') as json_file:
            tokens = json.load(json_file)
        
        STOCK_API_KEY = tokens['STOCK_API_KEY']
        
        # create OAuthHandler object
        auth = tweepy.OAuthHandler(tokens['consumer_key'], tokens['consumer_secret'])
        # set access token and secret
        auth.set_access_token(tokens['access_token'], tokens['access_token_secret'])
        # create tweepy API object to fetch tweets
        api = tweepy.API(auth)
        
        #Get general stock data
        self.TKR = TKR
        self.EX = EX
        s_url = build_url_stock(STOCK_API_KEY, self.TKR, range_, interval)
        e_url = build_url_stock(STOCK_API_KEY, self.EX, range_, interval)
        s_data = get_json(s_url)
        e_data = get_json(e_url)
        self.dates, self.s_close, self.s_volumes = get_closing_prices_and_volumes(s_data)
        _, self.e_close, self.e_volumes = get_closing_prices_and_volumes(e_data)
        
        #Get sentiment
        out_tweets = get_tweets(TKR, api)
        self.sentiment = get_sentiment(out_tweets)
        
        #Get ranges
        self.price_max = max(self.s_close)
        self.price_min = min(self.s_close)
        self.price_range = self.price_max - self.price_min
        
        #Get changes in price and volume
        self.delta_price = []
        self.delta_volume = []
        for i in range(len(self.s_close)):
            if i == 0:
                delta_p = 0.0
                delta_v = 0.0
            else:
                delta_p = self.s_close[i] - self.s_close[i-1]
                delta_v = self.s_volumes[i] - self.s_volumes[i-1]
            self.delta_price.append(delta_p)
            self.delta_volume.append(delta_v)
        
        #Calculate descriptive stats
        p_array = np.array(self.s_close)
        self.price_variance = np.var(p_array)
        self.price_mean = np.mean(p_array)
        
        v_array = np.array(self.s_volumes)
        self.volume_variance = np.var(v_array)
        self.volume_mean = np.mean(v_array)
        
        #Calculate beta
        self.beta = beta(self.s_close, self.e_close)
        
        all_data = {'ticker':self.TKR, 'exchange':self.EX, 'dates':self.dates, 
                    'closing_prices':self.s_close, 'closing_volumes':self.s_volumes, 
                    'beta':self.beta, 'price_range':self.price_range, 
                    'price_delta':self.delta_price, 'volume_delta':self.delta_volume, 
                    'mean_price':self.price_mean, 'mean_volume':self.volume_mean, 
                    'variance_price':self.price_variance, 
                    'variance_volume':self.volume_variance, 'max_price':self.price_max, 
                    'min_price':self.price_min, 'sentiment':self.sentiment}
        
        self.everything = all_data