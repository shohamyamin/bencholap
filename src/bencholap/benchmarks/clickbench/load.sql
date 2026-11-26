-- Benchmark table from the raw table: the hits view of ClickHouse/ClickBench@1084693d5b5b
-- trino-datalake-partitioned/create.sql (EventTime, ClientEventTime and LocalEventTime are Unix seconds in the files).
-- Placeholder: {source}.
SELECT
    WatchID, JavaEnable, Title, GoodEvent,
    from_unixtime(EventTime) AS EventTime,
    EventDate,
    CounterID, ClientIP, RegionID, UserID, CounterClass, OS, UserAgent,
    URL, Referer, IsRefresh, RefererCategoryID, RefererRegionID,
    URLCategoryID, URLRegionID, ResolutionWidth, ResolutionHeight,
    ResolutionDepth, FlashMajor, FlashMinor, FlashMinor2, NetMajor, NetMinor,
    UserAgentMajor, UserAgentMinor, CookieEnable, JavascriptEnable,
    IsMobile, MobilePhone, MobilePhoneModel, Params, IPNetworkID,
    TraficSourceID, SearchEngineID, SearchPhrase, AdvEngineID, IsArtifical,
    WindowClientWidth, WindowClientHeight, ClientTimeZone,
    from_unixtime(ClientEventTime) AS ClientEventTime,
    SilverlightVersion1, SilverlightVersion2, SilverlightVersion3,
    SilverlightVersion4, PageCharset, CodeVersion, IsLink, IsDownload,
    IsNotBounce, FUniqID, OriginalURL, HID, IsOldCounter, IsEvent,
    IsParameter, DontCountHits, WithHash, HitColor,
    from_unixtime(LocalEventTime) AS LocalEventTime,
    Age, Sex, Income, Interests, Robotness, RemoteIP, WindowName,
    OpenerName, HistoryLength, BrowserLanguage, BrowserCountry,
    SocialNetwork, SocialAction, HTTPError, SendTiming, DNSTiming,
    ConnectTiming, ResponseStartTiming, ResponseEndTiming, FetchTiming,
    SocialSourceNetworkID, SocialSourcePage, ParamPrice, ParamOrderID,
    ParamCurrency, ParamCurrencyID, OpenstatServiceName, OpenstatCampaignID,
    OpenstatAdID, OpenstatSourceID, UTMSource, UTMMedium, UTMCampaign,
    UTMContent, UTMTerm, FromTag, HasGCLID, RefererHash, URLHash, CLID
FROM {source}
