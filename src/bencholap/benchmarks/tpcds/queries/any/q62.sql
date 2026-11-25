-- TPC-DS Q62: kit template query62.tpl with the specification's (v2.10.0, Appendix B) qualification substitution parameters
-- tpcds-kit commit 5a3a81796992b725c2a8b216767e142609966752
-- normalized: '+ N days' -> '+ interval 'N' day'
select
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,web_name
  ,sum(case when (ws_ship_date_sk - ws_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days"
  ,sum(case when (ws_ship_date_sk - ws_sold_date_sk > 30) and
                 (ws_ship_date_sk - ws_sold_date_sk <= 60) then 1 else 0 end )  as "31- interval '60' day"
  ,sum(case when (ws_ship_date_sk - ws_sold_date_sk > 60) and
                 (ws_ship_date_sk - ws_sold_date_sk <= 90) then 1 else 0 end)  as "61- interval '90' day"
  ,sum(case when (ws_ship_date_sk - ws_sold_date_sk > 90) and
                 (ws_ship_date_sk - ws_sold_date_sk <= 120) then 1 else 0 end)  as "91- interval '120' day"
  ,sum(case when (ws_ship_date_sk - ws_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days"
from
   web_sales
  ,warehouse
  ,ship_mode
  ,web_site
  ,date_dim
where
    d_month_seq between 1200 and 1200 + 11
and ws_ship_date_sk   = d_date_sk
and ws_warehouse_sk   = w_warehouse_sk
and ws_ship_mode_sk   = sm_ship_mode_sk
and ws_web_site_sk    = web_site_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,web_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
       ,web_name
limit 100;
