import os

from tqdm import tqdm 
import numpy as np
import pandas as pd 

from src.logger import LOGGER
from src.date_map import DATE_MAP

def clean_financial_data(df):
    """
     Cleans the data for further processing.
      param: df - Dataframe.
      returns: Cleaned dataframe.
    """
    LOGGER.info("Cleaning the financial data.")
    df_slice = df[['Identifier (RIC)', 'Company Name', 'Date of Insolvency', 'Score',
         'Discrimination']]
    df = df.drop(['Identifier (RIC)', 'Company Name', 'Date of Insolvency', 'Score',
         'Discrimination'], axis=1)
    columns = df.columns

    def convert_string_to_float(x):
        for col in columns:
            float(str(x[col]).replace(",", "").replace(' -   ', str(0)).replace("%", "")) / 1000000 
        return x

    df.replace(to_replace='#DIV/0!', value=0, inplace=True)
    df = df.apply(convert_string_to_float, axis=1)
    return pd.concat([df, df_slice], sort=False)

def read_market_data(name):
    """
     Gets the market data from the data/market_data directory. 
     param: name - Name of the company for which we want the data.
     return: Dataframe
    """
    parentDirectory = os.path.abspath(os.getcwd())
    try:
        LOGGER.info(f"Getting market data for {name}.")
        df = pd.read_csv(os.path.join(parentDirectory, 'data/market_data', f'{name}.csv'))
        return df
    except Exception as ex:
        LOGGER.error(f"An error occurred when fetching data for {name}, {ex}")
        

class ProcessData:
    """
         A class to get the data for each of the company merged with the financia data and market data.
          param: financialDf - Financial Dataframe
          param: marketDf - Market Dataframe
          returns: A dataframe using the __iter__ method and __next__method.
    """  
    def __init__(self, financialDf):
            self.financialDf = financialDf
    
    def __iter__(self):
        self.grouped = self.financialDf.groupby('Company Name')
        self.groupby_iter = iter(self.grouped)
        return self
    
    def __next__(self):
        name, dataframe = next(self.groupby_iter)
        marketData = read_market_data(name)
        financial_data = clean_financial_data(dataframe)
        
        return merge_f_m_data(financial_data, marketData)
    
    
def merge_f_m_data(financial_df, market_df):
    """
     Merge both dataframe to get the final data. The shape of the financal df will be (2*586) while market df will be of (2000*13)
     returns the merged data.
    """
    market_df['Date'] = pd.to_datetime(market_df['Date'])
    print(market_df.shape)
    columns = financial_df.columns
    transposed_df = financial_df.T
    transposed_df['Row names'] = columns
    transposed_df['Date'] = 0
    LOGGER.info('Merging both data frames into one.')
    
    def get_dates(x):
        # Gives date to the FY-X term. 
        for key in DATE_MAP.keys():
            if x['Row names'].find(key) >= 0:
                    x['Date'] = f'1/1/{DATE_MAP[key]}'
        return x 
           
    transposed_df = transposed_df.apply(get_dates, axis=1)
    transposed_df['Date'] = transposed_df['Date'].replace(0, '1/1/2019')
    transposed_df['Date'] = pd.to_datetime(transposed_df['Date'])
    merged_df = transposed_df.merge(market_df, on='Date', how='outer')
    return merged_df