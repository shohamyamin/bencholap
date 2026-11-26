-- ClickBench Q17 (Trino dialect), ClickHouse/ClickBench@1084693d5b5b trino-datalake-partitioned/queries.sql line 18
SELECT UserID, SearchPhrase, COUNT(*) FROM hits GROUP BY UserID, SearchPhrase LIMIT 10;
