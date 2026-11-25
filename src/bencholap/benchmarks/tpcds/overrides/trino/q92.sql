-- Trino override of q92 (canonical: queries/any/q92.sql)
-- reason: string literal compared with a date column; Trino has no implicit varchar-to-date coercion, so the literal is wrapped in cast(... as date).
-- compare: trinodb/trino testing/trino-benchmark-queries/src/main/resources/sql/trino/tpcds/q92.sql
-- TPC-DS Q92: kit template query92.tpl with the specification's (v2.10.0, Appendix B) qualification substitution parameters
-- tpcds-kit commit 5a3a81796992b725c2a8b216767e142609966752
-- normalized: '+ N days' -> '+ interval 'N' day'
select
   sum(ws_ext_discount_amt)  as "Excess Discount Amount"
from
    web_sales
   ,item
   ,date_dim
where
i_manufact_id = 350
and i_item_sk = ws_item_sk
and d_date between cast('2000-01-27' as date) and
        (cast('2000-01-27' as date) + interval '90' day)
and d_date_sk = ws_sold_date_sk
and ws_ext_discount_amt
     > (
         SELECT
            1.3 * avg(ws_ext_discount_amt)
         FROM
            web_sales
           ,date_dim
         WHERE
              ws_item_sk = i_item_sk
          and d_date between cast('2000-01-27' as date) and
                             (cast('2000-01-27' as date) + interval '90' day)
          and d_date_sk = ws_sold_date_sk
      )
order by sum(ws_ext_discount_amt)
limit 100;
