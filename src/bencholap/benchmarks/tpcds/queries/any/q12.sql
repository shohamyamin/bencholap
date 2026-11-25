-- TPC-DS Q12: kit template query12.tpl with the specification's (v2.10.0, Appendix B) qualification substitution parameters
-- tpcds-kit commit 5a3a81796992b725c2a8b216767e142609966752
-- normalized: '+ N days' -> '+ interval 'N' day'
select  i_item_id
      ,i_item_desc
      ,i_category
      ,i_class
      ,i_current_price
      ,sum(ws_ext_sales_price) as itemrevenue
      ,sum(ws_ext_sales_price)*100/sum(sum(ws_ext_sales_price)) over
          (partition by i_class) as revenueratio
from
	web_sales
    	,item
    	,date_dim
where
	ws_item_sk = i_item_sk
  	and i_category in ('Sports', 'Books', 'Home')
  	and ws_sold_date_sk = d_date_sk
	and d_date between cast('1999-02-22' as date)
				and (cast('1999-02-22' as date) + interval '30' day)
group by
	i_item_id
        ,i_item_desc
        ,i_category
        ,i_class
        ,i_current_price
order by
	i_category
        ,i_class
        ,i_item_id
        ,i_item_desc
        ,revenueratio
limit 100;
