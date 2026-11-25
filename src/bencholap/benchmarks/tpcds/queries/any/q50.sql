-- TPC-DS Q50: kit template query50.tpl with the specification's (v2.10.0, Appendix B) qualification substitution parameters
-- tpcds-kit commit 5a3a81796992b725c2a8b216767e142609966752
-- normalized: '+ N days' -> '+ interval 'N' day'
select
   s_store_name
  ,s_company_id
  ,s_street_number
  ,s_street_name
  ,s_street_type
  ,s_suite_number
  ,s_city
  ,s_county
  ,s_state
  ,s_zip
  ,sum(case when (sr_returned_date_sk - ss_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days"
  ,sum(case when (sr_returned_date_sk - ss_sold_date_sk > 30) and
                 (sr_returned_date_sk - ss_sold_date_sk <= 60) then 1 else 0 end )  as "31- interval '60' day"
  ,sum(case when (sr_returned_date_sk - ss_sold_date_sk > 60) and
                 (sr_returned_date_sk - ss_sold_date_sk <= 90) then 1 else 0 end)  as "61- interval '90' day"
  ,sum(case when (sr_returned_date_sk - ss_sold_date_sk > 90) and
                 (sr_returned_date_sk - ss_sold_date_sk <= 120) then 1 else 0 end)  as "91- interval '120' day"
  ,sum(case when (sr_returned_date_sk - ss_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days"
from
   store_sales
  ,store_returns
  ,store
  ,date_dim d1
  ,date_dim d2
where
    d2.d_year = 2001
and d2.d_moy  = 8
and ss_ticket_number = sr_ticket_number
and ss_item_sk = sr_item_sk
and ss_sold_date_sk   = d1.d_date_sk
and sr_returned_date_sk   = d2.d_date_sk
and ss_customer_sk = sr_customer_sk
and ss_store_sk = s_store_sk
group by
   s_store_name
  ,s_company_id
  ,s_street_number
  ,s_street_name
  ,s_street_type
  ,s_suite_number
  ,s_city
  ,s_county
  ,s_state
  ,s_zip
order by s_store_name
        ,s_company_id
        ,s_street_number
        ,s_street_name
        ,s_street_type
        ,s_suite_number
        ,s_city
        ,s_county
        ,s_state
        ,s_zip
limit 100;
