import selenium
from selenium import webdriver
from selenium.webdriver import ChromeOptions
import pandas as pd
import time
from bs4 import BeautifulSoup
from io import StringIO
import re
import datetime

def extract_first_value(text):
    return text.split()[0].replace('$', '')

def extract_last_value(text):
    a = text.split()[-1].replace(')', '')
    return a.replace('$', '')

def extract_info(data):
    round_count = None
    grain = None
    sku = None

    # Extract SKU
    start = data.find("SKU: ")+4
    end = data.find("Available")
    sku = data[start:end]

    #split string to list for finding round and grain size
    data = str.split(data)

    # Extract round count
    if 'Round' in data:
        round_index = data.index('Round') - 1
        round_count = data[round_index]

    # Extract grain
    if 'Grain' in data:
        grain_index = data.index('Grain') - 1
        grain = data[grain_index]


    return pd.Series([round_count, grain, sku], index=['Round Count', 'Grain', 'SKU'])


def getSgData(link, csvName):
    options = ChromeOptions()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)
    driver.get(link)
    html=driver.page_source

    soup=BeautifulSoup(html, features="lxml")
    soup_table = soup.find_all("table")[-1] #select last table on page
    tables = pd.read_html(StringIO(str(soup_table))) #turn tables into a list of dataframes
    df = tables[0] #turn dataframe into a single one
    df = df.drop('Image', axis=1) #axis 1 is the column, drops image column
    df['Cost Per Unit'] = df['Price'].apply(extract_first_value).astype(float) #convert prices to floats
    df['Cost Per Round'] = df['Price'].apply(extract_last_value).astype(float)
    df[['Round Count','Grain','SKU']] = df['Name'].apply(extract_info) #SKU doesn't work well, but the rest is ok.
    df['DateTime'] = datetime.datetime.now()
    df = df.drop('Price', axis=1)

    df.to_csv(csvName,header=False, mode='a') #Header must be manually added?

#Execution
getSgData("https://www.sgammo.com/catalog/pistol-ammo-sale/45-auto-acp-ammo", 'sgAmmo   .csv')
