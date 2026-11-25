-- Trino override of q34 (canonical: queries/any/q34.sql)
-- reason: integer / integer truncates in Trino, while the TPC-DS answers assume exact division; the dividend is cast to decimal, as in Trino's own benchmark query.
-- compare: trinodb/trino testing/trino-benchmark-queries/src/main/resources/sql/trino/tpcds/q34.sql
-- TPC-DS Q34: kit template query34.tpl with the specification's (v2.10.0, Appendix B) qualification substitution parameters
-- tpcds-kit commit 5a3a81796992b725c2a8b216767e142609966752
select c_last_name
       ,c_first_name
       ,c_salutation
       ,c_preferred_cust_flag
       ,ss_ticket_number
       ,cnt from
   (select ss_ticket_number
          ,ss_customer_sk
          ,count(*) cnt
    from store_sales,date_dim,store,household_demographics
    where store_sales.ss_sold_date_sk = date_dim.d_date_sk
    and store_sales.ss_store_sk = store.s_store_sk
    and store_sales.ss_hdemo_sk = household_demographics.hd_demo_sk
    and (date_dim.d_dom between 1 and 3 or date_dim.d_dom between 25 and 28)
    and (household_demographics.hd_buy_potential = '>10000' or
         household_demographics.hd_buy_potential = 'Unknown')
    and household_demographics.hd_vehicle_count > 0
    and (case when household_demographics.hd_vehicle_count > 0
	then cast(household_demographics.hd_dep_count as decimal(7,2))/ household_demographics.hd_vehicle_count
	else null
	end)  > 1.2
    and date_dim.d_year in (1999,1999+1,1999+2)
    and store.s_county in ('Williamson County','Williamson County','Williamson County','Williamson County',
                           'Williamson County','Williamson County','Williamson County','Williamson County')
    group by ss_ticket_number,ss_customer_sk) dn,customer
    where ss_customer_sk = c_customer_sk
      and cnt between 15 and 20
    order by c_last_name,c_first_name,c_salutation,c_preferred_cust_flag desc, ss_ticket_number;
