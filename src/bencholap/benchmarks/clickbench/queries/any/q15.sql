-- ClickBench Q15 (Trino dialect), ClickHouse/ClickBench@1084693d5b5b trino-datalake-partitioned/queries.sql line 16
SELECT UserID, COUNT(*) FROM hits GROUP BY UserID ORDER BY COUNT(*) DESC LIMIT 10;
