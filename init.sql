-- Drop tables if they exist
DROP TABLE IF EXISTS Stocks;
DROP TABLE IF EXISTS SymbolMapping;
DROP TABLE IF EXISTS YFSymbol;
DROP TABLE IF EXISTS AlertsWatchlist;
DROP TABLE IF EXISTS Watchlists;
DROP TABLE IF EXISTS ExchangeInfo;
DROP TABLE IF EXISTS StreamedSymbols;

-- Create Stocks table
CREATE TABLE Stocks (
    Time TIMESTAMPTZ NOT NULL,
    Symbol TEXT NOT NULL,
    Interval TEXT NOT NULL,
    Open DOUBLE PRECISION,
    High DOUBLE PRECISION,
    Low DOUBLE PRECISION,
    Close DOUBLE PRECISION,
    AdjClose DOUBLE PRECISION,
    Volume BIGINT
);

-- Create SymbolMapping table
CREATE TABLE SymbolMapping (
    YFSymbol TEXT PRIMARY KEY,
    TVSymbol TEXT,
    Description TEXT,
    Exchange TEXT,
    AdditionalMain TEXT,
    AdditionalSecondary TEXT
);

-- Create YFSymbol table
CREATE TABLE YFSymbol (
    Symbol TEXT PRIMARY KEY,
    Exchange TEXT,
    ShortName TEXT,
    QuoteType TEXT,
    IndexName TEXT,
    Score DOUBLE PRECISION,
    TypeDisp TEXT,
    LongName TEXT,
    ExchDisp TEXT,
    Sector TEXT,
    SectorDisp TEXT,
    Industry TEXT,
    IndustryDisp TEXT,
    DispSecIndFlag BOOLEAN,
    IsYahooFinance BOOLEAN
);

-- Create AlertsWatchlist table
CREATE TABLE AlertsWatchlist (
    AlertId SERIAL PRIMARY KEY,
    Symbol TEXT,
    AlertValue DOUBLE PRECISION,
    AlertOperator BOOLEAN,
    AlertTags TEXT [],
    AlertActive BOOLEAN
);

-- Create Watchlists table
CREATE TABLE Watchlists (
    WatchlistName TEXT PRIMARY KEY,
    Symbols TEXT []
);

-- Create ExchangeInfo table
CREATE TABLE ExchangeInfo (
    Exchange TEXT PRIMARY KEY,
    MarketOpen TIMETZ,
    MarketClose TIMETZ,
    BreakStart TIMETZ,
    BreakEnd TIMETZ,
    WeekMask TEXT,
    _1m INT,
    _2m INT,
    _5m INT,
    _15m INT,
    _30m INT,
    _60m INT,
    _90m INT
);

-- Create StreamedSymbols table
CREATE TABLE StreamedSymbols (
    Symbol TEXT PRIMARY KEY,
    AddedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Tags (
    TagId SERIAL PRIMARY KEY,
    TagName TEXT,
    TagColor TEXT
);

-- Create indexes
CREATE INDEX IF NOT EXISTS time_idx ON Stocks (time);
CREATE INDEX IF NOT EXISTS symbol_interval_time_idx ON Stocks (symbol, interval, time DESC);