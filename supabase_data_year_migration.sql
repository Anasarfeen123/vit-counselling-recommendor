-- Run this once in Supabase SQL Editor before importing 2026 counselling data.
-- It keeps existing rows as 2025 and lets 2026 rows coexist safely.

alter table counselling_records
add column if not exists data_year integer not null default 2025;

update counselling_records
set data_year = 2025
where data_year is null;

do $$
declare
    constraint_name text;
    index_name text;
begin
    for constraint_name in
        select con.conname
        from pg_constraint con
        join pg_class rel on rel.oid = con.conrelid
        join pg_namespace nsp on nsp.oid = rel.relnamespace
        where nsp.nspname = 'public'
          and rel.relname = 'counselling_records'
          and con.contype = 'u'
          and (
              select array_agg(att.attname order by att.attname)
              from unnest(con.conkey) as cols(attnum)
              join pg_attribute att
                on att.attrelid = con.conrelid
               and att.attnum = cols.attnum
          ) = array['branch', 'campus', 'fee', 'rank']
    loop
        execute format('alter table counselling_records drop constraint %I', constraint_name);
    end loop;

    for index_name in
        select idx.relname
        from pg_index i
        join pg_class tbl on tbl.oid = i.indrelid
        join pg_class idx on idx.oid = i.indexrelid
        join pg_namespace nsp on nsp.oid = tbl.relnamespace
        where nsp.nspname = 'public'
          and tbl.relname = 'counselling_records'
          and i.indisunique
          and (
              select array_agg(att.attname order by att.attname)
              from unnest(i.indkey) as cols(attnum)
              join pg_attribute att
                on att.attrelid = tbl.oid
               and att.attnum = cols.attnum
          ) = array['branch', 'campus', 'fee', 'rank']
    loop
        execute format('drop index if exists %I', index_name);
    end loop;
end $$;

create unique index if not exists counselling_records_year_unique
on counselling_records (rank, campus, branch, fee, data_year);
