-- Trino override of q32 (canonical: queries/any/q32.sql)
-- reason: string literal compared with a date column; Trino has no implicit varchar-to-date coercion, so the literal is wrapped in cast(... as date).
-- compare: trinodb/trino testing/trino-benchmark-queries/src/main/resources/sql/trino/tpcds/q32.sql
-- TPC-DS Q32: kit template query32.tpl with the specification's (v2.10.0, Appendix B) qualification substitution parameters
-- tpcds-kit commit 5a3a81796992b725c2a8b216767e142609966752
-- normalized: '+ N days' -> '+ interval 'N' day'
select  sum(cs_ext_discount_amt)  as "excess discount amount"
from
   catalog_sales
   ,item
   ,date_dim
where
i_manufact_id = 977
and i_item_sk = cs_item_sk
and d_date between cast('2000-01-27' as date) and
        (cast('2000-01-27' as date) + interval '90' day)
and d_date_sk = cs_sold_date_sk
and cs_ext_discount_amt
     > (
         select
            1.3 * avg(cs_ext_discount_amt)
         from
            catalog_sales
           ,date_dim
         where
              cs_item_sk = i_item_sk
          and d_date between cast('2000-01-27' as date) and
                             (cast('2000-01-27' as date) + interval '90' day)
          and d_date_sk = cs_sold_date_sk
      )
limit 100;
