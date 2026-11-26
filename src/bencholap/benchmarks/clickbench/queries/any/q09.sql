-- ClickBench Q9 (Trino dialect), ClickHouse/ClickBench@1084693d5b5b trino-datalake-partitioned/queries.sql line 10
SELECT RegionID, SUM(AdvEngineID), COUNT(*) AS c, AVG(ResolutionWidth), COUNT(DISTINCT UserID) FROM hits GROUP BY RegionID ORDER BY c DESC LIMIT 10;
