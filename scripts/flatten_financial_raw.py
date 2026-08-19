import re

import psycopg2
from psycopg2.extras import execute_values
from sshtunnel import SSHTunnelForwarder

from type_inference import convert_value, infer_column_type

SSH_HOST = "ec2-13-207-88-148.ap-south-1.compute.amazonaws.com"
SSH_PORT = 22
SSH_USERNAME = "ubuntu"
SSH_PKEY = "sf-dashboard-dev.pem"
DB_REMOTE_PORT = 5433
DB_NAME = "sfdashboard_dev"
DB_USER = "sfdashboard"
DB_PASSWORD = "devpassword"

HEADER_ROW_INDEX_BY_TAB = {
    "Taktical Actual & Backlog": 0,
    "CP & portfolio lead mapped": 0,
    "MM Actual & Backlog": 1,
    "MM FY27 Plan": 1,
    "MM Target with Portfolio FY27": 1,
    "DB Actual & Backlog": 2,
    "DB FY27 Plan & Target": 2,
    "TD FY27 Plan & Target": 2,
}


def sanitize_column(name):
    col = re.sub(r"[^0-9a-zA-Z]+", "_", name).strip("_").lower()
    if not col:
        col = "col"
    if col[0].isdigit():
        col = f"_{col}"
    return col


def dedupe_columns(columns):
    seen = {}
    result = []
    for col in columns:
        if col not in seen:
            seen[col] = 0
            result.append(col)
        else:
            seen[col] += 1
            result.append(f"{col}_{seen[col]}")
    return result


def flatten_tab(cursor, tab_name, header_row_index):
    cursor.execute(
        """
        SELECT rows, sheet, snapshot_date
        FROM public.financial_financialrawtab
        WHERE tab = %s
        ORDER BY snapshot_date DESC
        LIMIT 1
        """,
        (tab_name,),
    )
    rows, sheet, snapshot_date = cursor.fetchone()
    header = rows[header_row_index]
    data = rows[header_row_index + 1:]

    columns = dedupe_columns([sanitize_column(name) for name in header])
    target_table = f"financial_{sanitize_column(tab_name)}"

    num_columns = len(columns)
    data = [(row + [""] * (num_columns - len(row)))[:num_columns] for row in data]

    column_types = [infer_column_type([row[i] for row in data]) for i in range(len(columns))]

    column_defs = ", ".join(f'"{col}" {col_type}' for col, col_type in zip(columns, column_types))

    cursor.execute(f'DROP TABLE IF EXISTS public."{target_table}"')
    cursor.execute(
        f'CREATE TABLE public."{target_table}" ({column_defs}, sheet TEXT, snapshot_date DATE)'
    )

    column_list = ", ".join(f'"{col}"' for col in columns) + ", sheet, snapshot_date"
    insert_rows = [
        tuple(convert_value(value, col_type) for value, col_type in zip(row, column_types)) + (sheet, snapshot_date)
        for row in data
    ]
    execute_values(
        cursor,
        f'INSERT INTO public."{target_table}" ({column_list}) VALUES %s',
        insert_rows,
    )

    return target_table, len(insert_rows), snapshot_date


def main():
    with SSHTunnelForwarder(
        (SSH_HOST, SSH_PORT),
        ssh_username=SSH_USERNAME,
        ssh_pkey=SSH_PKEY,
        remote_bind_address=("localhost", DB_REMOTE_PORT),
    ) as tunnel:
        conn = psycopg2.connect(
            host="localhost",
            port=tunnel.local_bind_port,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=10,
        )
        try:
            with conn.cursor() as cursor:
                for tab_name, header_row_index in HEADER_ROW_INDEX_BY_TAB.items():
                    target_table, row_count, snapshot_date = flatten_tab(cursor, tab_name, header_row_index)
                    print(f'{tab_name} -> public."{target_table}": {row_count} rows (snapshot {snapshot_date})')

            conn.commit()
        finally:
            conn.close()


if __name__ == "__main__":
    main()
