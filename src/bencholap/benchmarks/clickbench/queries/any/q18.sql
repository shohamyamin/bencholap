-- ClickBench Q18 (Trino dialect), ClickHouse/ClickBench@1084693d5b5b trino-datalake-partitioned/queries.sql line 19
SELECT UserID, extract(minute FROM EventTime) AS m, SearchPhrase, COUNT(*) FROM hits GROUP BY UserID, extract(minute FROM EventTime), SearchPhrase ORDER BY COUNT(*) DESC LIMIT 10;
