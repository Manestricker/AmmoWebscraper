import selenium
from selenium import webdriver
from selenium.webdriver import ChromeOptions
import pandas as pd
from bs4 import BeautifulSoup
from io import StringIO
import datetime
import yagmail
import keyring # type: ignore
from selenium.webdriver.chrome.service import Service

def extract_first_value(text):
    a = text.split()[0].replace('$', '')
    a = a.replace(' ', '')
    a = a.replace(',', '')
    return a

def extract_last_value(text):
    a = text.split()[-1].replace(')', '')
    a = a.replace('$', '')
    a = a.replace(' ', '')
    try:
        a = float(a)
        print(a,a.isdigit())
        if a.isdigit():
            return a
    except:
        return None

def extract_info(data):
    round_count = None
    grain = None
    sku = None
    name = None

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

    # Extract Name
    #nameIndex = [index for index, char in enumerate(data) if char == '-']
    #nameIndex[0] = int(nameIndex[0]+1)
    #name = data[nameIndex[0]:nameIndex[1]]

    return pd.Series([round_count, grain, sku], index=['Round Count', 'Grain', 'SKU'])

def filterDataFrame(dataFrame, cpr, grain = 900, grainExact = False, size = 10):
    #cpr is the maximum cost per round to look for
    #grain is grain size to look for
    #grainExact looks for exactly that grain
    df = dataFrame[dataFrame['Cost Per Round'] <= cpr]
    if grainExact:
        df = df[df['Grain'] == grain]
    else:
        df = df[df['Grain'] <= grain]
    df = df.drop('DateTime', axis=1)
    df = df.sort_values(by=['Cost Per Round'])
    df = df.head(size)
    return df

def getSgData(link, csvName):
    options = ChromeOptions()
    #options = ChromiumOptions()
    options.add_argument("--headless=new")
    #driver = webdriver.Chrome(options=options)
    serv =Service(executable_path='/usr/lib/chromium-browser/chromedriver')
    driver = webdriver.Chrome(service=serv,options=options)
    #driver = webdriver.chromium(options=options)
    #driver = webdriver.Firefox()
    driver.get(link)
    html=driver.page_source

    soup=BeautifulSoup(html, features="lxml")
    soup_table = soup.find_all("table")[-1] #select last table on page
    tables = pd.read_html(StringIO(str(soup_table))) #turn tables into a list of dataframes
    df = tables[0] #turn dataframe into a single one
    df = df.drop('Image', axis=1) #axis 1 is the column, drops image column
    df['Cost Per Unit'] = df['Price'].apply(extract_first_value).astype(float) #convert prices to floats
    df[['Round Count','Grain','SKU']] = df['Name'].apply(extract_info) #SKU doesn't work well, but the rest is ok.
    df['DateTime'] = datetime.datetime.now()
    df['Grain'] = df['Grain'].astype(float)
    df = df.drop('Price', axis=1)
    df['Cost Per Round'] = df['Cost Per Unit'].div(df['Round Count'].astype(float))
    
    
    df.to_csv(csvName,header=False, mode='a') #Header must be manually added?
    driver.close()
    return df


def sendEmail(to, subject, contents, descriptions):
    body = "<p>This is an auto-generated email containing filtered data from the most recent webscrape of sgAmmo.com</p>"
    for i in range(len(contents)):
        body = body + '<hr><h2>'+descriptions[i]+'</h2>' + contents[i].to_html()
    yag = yagmail.SMTP('davidbdeltz@gmail.com', keyring.get_password("gmail","davidbdeltz")) #replace with your email account name
    yag.send(to, subject, body)
    print("\nEmail Sent, Data Recorded in CSV files")

######################################################################################################################################################
#Execution
#Put sgAmmo links and fileNames for them to be store at
sg45 = getSgData("https://www.sgammo.com/catalog/pistol-ammo-sale/45-auto-acp-ammo", 'sgAmmo45.csv')
print("45 ACP Data Aquired")
sg9 = getSgData("https://www.sgammo.com/catalog/pistol-ammo-sale/9mm-luger-ammo", 'sgAmmo9mm.csv')
print("9mm Luger Data Aquired")
sg223 = getSgData("https://www.sgammo.com/catalog/rifle-ammo-sale/223-556mm-ammo", 'sgAmmo223.csv')
print("223/556 Data Aquired")
sg22lr = getSgData("https://www.sgammo.com/catalog/rimfire-ammo-sale/22-lr-ammo", 'sgAmmo22lr.csv')
print("22LR Data Aquired")
#Name	Quantity in Stock	Cost Per Unit	Cost Per Round	Round Count	Grain	SKU	DateTime

#Filters and the descriptions they will recieve in the email generated
#filterDataFrame(dfName, CPR, grain = 900, grainExact = False)
#grain and graionExact don't need to be filled out
filterList = [filterDataFrame(sg45,0.6,185),
              filterDataFrame(sg45,0.5,230, True, size=5),
              filterDataFrame(sg9,0.25),
              filterDataFrame(sg223,0.50),
              filterDataFrame(sg22lr, .10, 40, True)]
filterDescriptions = ["45 ACP, CPR <= to $0.60, grain <= 185",
                      "45 ACP, CPR <= to $0.45, grain == 230, size =5",
                      "9mm Luger, CPR <= $0.25",
                      "223/556, CPR <= $0.50",
                      "22Lr, CPR <= $0.10, grain == 40"]
sendEmail("davidbdeltz@gmail.com", "sgAmmo Scraped Data", filterList, filterDescriptions) #replace To with whatever you account you want it sent to
