-- TPCH Q15, Trino override of the canonical qgen -d text (same substitution parameters).
-- reason: Trino does not support a column list in CREATE VIEW ("create view revenue0 (supplier_no, total_revenue) as").
-- reason: Uses a common table expression with the same definition as the revenue0 view, the form used by Trino's own benchmark query (testing/trino-benchmark-queries/src/main/resources/sql/trino/tpch/q15.sql).
with revenue0 (supplier_no, total_revenue) as (
	select
		l_suppkey,
		sum(l_extendedprice * (1 - l_discount))
	from
		lineitem
	where
		l_shipdate >= date '1996-01-01'
		and l_shipdate < date '1996-01-01' + interval '3' month
	group by
		l_suppkey
)
select
	s_suppkey,
	s_name,
	s_address,
	s_phone,
	total_revenue
from
	supplier,
	revenue0
where
	s_suppkey = supplier_no
	and total_revenue = (
		select
			max(total_revenue)
		from
			revenue0
	)
order by
	s_suppkey;
