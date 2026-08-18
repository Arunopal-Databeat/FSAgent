from sshtunnel import SSHTunnelForwarder
import psycopg2

with SSHTunnelForwarder(
    ('ec2-13-207-88-148.ap-south-1.compute.amazonaws.com', 22),
    ssh_username='ubuntu',
    ssh_pkey=r'sf-dashboard-dev.pem',
    remote_bind_address=('localhost', 5433),
) as tunnel:
    conn = psycopg2.connect(
        host='localhost',
        port=tunnel.local_bind_port,
        database='sfdashboard_dev',
        user='sfdashboard',
        password='devpassword',
        connect_timeout=10,
    )

    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT
                c.table_schema,
                c.table_name,
                obj_description(
                    (quote_ident(c.table_schema) || '.' || quote_ident(c.table_name))::regclass,
                    'pg_class'
                ) AS table_description,
                c.column_name,
                c.data_type,
                col_description(
                    (quote_ident(c.table_schema) || '.' || quote_ident(c.table_name))::regclass,
                    c.ordinal_position
                ) AS column_description
            FROM information_schema.columns c
            WHERE c.table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY c.table_schema, c.table_name, c.ordinal_position
        """)

        current_table = None

        for row in cursor.fetchall():
            schema, table, table_desc, column, data_type, column_desc = row
            table_key = f"{schema}.{table}"

            if table_key != current_table:
                current_table = table_key
                print(f"\n{'=' * 80}")
                print(f"TABLE: {table_key}")
                print(f"DESCRIPTION: {table_desc or 'No description'}")
                print(f"{'=' * 80}")

            print(f"  {column} ({data_type})")
            print(f"    Description: {column_desc or 'No description'}")

    conn.close()