from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.schema import StrOutputParser

import ast

from utils.api import search_yfinance_tickers


llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro")

prompt = PromptTemplate(
    input_variables=["trading_view_data", "yfinance_results"],
    template="""You are a trading analyst and you will be given two sets of data, one is from TradingView and the other is from Yahoo Finance.
    Your task is to compare the two sets of data. The ticker symbol names are different for both the sets of data, 
    we want to find which ticker symbol from Yahoo Finance corresponds to the ticker symbol from TradingView.
    
    An example is:
    --------------------------------------------------------------------------------
    The TradingView data is as follows: 
    {{
        'details-description': 'Apple Inc',
        'details-exchange': 'NEO',
        'details-additional-main': 'Electronic Technology',
        'details-additional-secondary': 'Telecommunications Equipment',
        'symbol': 'AAPL'
    }}
    
    The Yahoo Finance data is as follows:
    [
    {{
      "exchange": "NMS",
      "shortname": "Apple Inc.",
      "quoteType": "EQUITY",
      "symbol": "AAPL",
      "index": "quotes",
      "score": 62233,
      "typeDisp": "Equity",
      "longname": "Apple Inc.",
      "exchDisp": "NASDAQ",
      "sector": "Technology",
      "sectorDisp": "Technology",
      "industry": "Consumer Electronics",
      "industryDisp": "Consumer Electronics",
      "dispSecIndFlag": true,
      "isYahooFinance": true
    }},
    {{
      "exchange": "NEO",
      "shortname": "APPLE CDR (CAD HEDGED)",
      "quoteType": "EQUITY",
      "symbol": "AAPL.NE",
      "index": "quotes",
      "score": 20011,
      "typeDisp": "Equity",
      "longname": "Apple Inc.",
      "exchDisp": "NEO",
      "sector": "Technology",
      "sectorDisp": "Technology",
      "industry": "Consumer Electronics",
      "industryDisp": "Consumer Electronics",
      "isYahooFinance": true
    }}, ...
  ]
    
    You would be providing an output of the corresponding ticker symbol details from Yahoo Finance for the given TradingView ticker symbol which is 
    Your output is:
    {{
      "exchange": "NEO",
      "shortname": "APPLE CDR (CAD HEDGED)",
      "quoteType": "EQUITY",
      "symbol": "AAPL.NE",
      "index": "quotes",
      "score": 20011,
      "typeDisp": "Equity",
      "longname": "Apple Inc.",
      "exchDisp": "NEO",
      "sector": "Technology",
      "sectorDisp": "Technology",
      "industry": "Consumer Electronics",
      "industryDisp": "Consumer Electronics",
      "isYahooFinance": true
    }}
    
    Do not make anything up, only provide the details that are present in the Yahoo Finance data.
    Only return the answer as dictionary format which can be directly compared with the Yahoo Finance data and parsed by python directly.
    You don't have to return if you don't think the ticker symbol is present in the Yahoo Finance data. Return an empty dictionary in that case.
    --------------------------------------------------------------------------------
    
    Now you provide the output for the following data: 
    The TradingView data is as follows: 
    {trading_view_data}
    
    The Yahoo Finance data is as follows: 
    {yfinance_results}
    
    """,
)

llm_chain = (
    prompt
    | llm
    | StrOutputParser()
    | (lambda x: {"output": x})  # This wraps the output in a dict with key "output"
)


def yfinance_from_tradingview(trading_view_data):
    yfinance_results = (
        search_yfinance_tickers(trading_view_data["symbol"])[:3]
        + search_yfinance_tickers(trading_view_data["details-description"])[:3]
    )

    if not yfinance_results:
        return {}
    out = llm_chain.invoke(
        {
            "trading_view_data": trading_view_data,
            "yfinance_results": yfinance_results,
        }
    )["output"]
    return string_processing(out)


def string_processing(s):
    start, end = 0, len(s)
    while start < len(s) and s[start] != "{":
        start += 1
    while end > 0 and s[end - 1] != "}":
        end -= 1
    if end <= start:
        return {}

    try:
        return ast.literal_eval(s[start:end])
    except:
        return {}
