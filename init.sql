CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create your table
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

CREATE TABLE SymbolMapping (
    YFSymbol TEXT PRIMARY KEY,
    TVSymbol TEXT,
    Description TEXT,
    Exchange TEXT,
    AdditionalMain TEXT,
    AdditionalSecondary TEXT
);
 
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

CREATE TABLE AlertsWatchlist (
    AlertId SERIAL PRIMARY KEY,
    Symbol TEXT,
    AlertValue DOUBLE PRECISION,
    AlertOperator BOOLEAN,
    AlertActive BOOLEAN
);

CREATE TABLE Watchlists (
    WatchlistName TEXT PRIMARY KEY,
    Symbols TEXT []
);

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


-- Create the hypertable
SELECT create_hypertable('stocks', 'time', 
    partitioning_column => 'symbol', 
    number_partitions => 10,
    chunk_time_interval => INTERVAL '1 day',
    create_default_indexes => FALSE);

-- Create indexes
CREATE INDEX ON stocks (symbol, interval, time DESC);


