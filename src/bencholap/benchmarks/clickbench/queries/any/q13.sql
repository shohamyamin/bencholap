-- ClickBench Q13 (Trino dialect), ClickHouse/ClickBench@1084693d5b5b trino-datalake-partitioned/queries.sql line 14
SELECT SearchPhrase, COUNT(DISTINCT UserID) AS u FROM hits WHERE SearchPhrase <> '' GROUP BY SearchPhrase ORDER BY u DESC LIMIT 10;
