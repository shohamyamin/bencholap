-- TPC-DS Q40: kit template query40.tpl with the specification's (v2.10.0, Appendix B) qualification substitution parameters
-- tpcds-kit commit 5a3a81796992b725c2a8b216767e142609966752
-- normalized: '+ N days' -> '+ interval 'N' day'
select
   w_state
  ,i_item_id
  ,sum(case when (cast(d_date as date) < cast ('2000-03-11' as date))
 		then cs_sales_price - coalesce(cr_refunded_cash,0) else 0 end) as sales_before
  ,sum(case when (cast(d_date as date) >= cast ('2000-03-11' as date))
 		then cs_sales_price - coalesce(cr_refunded_cash,0) else 0 end) as sales_after
 from
   catalog_sales left outer join catalog_returns on
       (cs_order_number = cr_order_number
        and cs_item_sk = cr_item_sk)
  ,warehouse
  ,item
  ,date_dim
 where
     i_current_price between 0.99 and 1.49
 and i_item_sk          = cs_item_sk
 and cs_warehouse_sk    = w_warehouse_sk
 and cs_sold_date_sk    = d_date_sk
 and d_date between (cast ('2000-03-11' as date) - interval '30' day)
                and (cast ('2000-03-11' as date) + interval '30' day)
 group by
    w_state,i_item_id
 order by w_state,i_item_id
limit 100;
