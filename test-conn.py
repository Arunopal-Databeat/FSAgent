from sshtunnel import SSHTunnelForwarder
import psycopg2

with SSHTunnelForwarder(
    ('ec2-13-207-88-148.ap-south-1.compute.amazonaws.com', 22),
    ssh_username='ubuntu',
    ssh_pkey=r'sf-dashboard-dev.pem',  # your private key path
    remote_bind_address=('localhost', 5433),  # Postgres port on the remote host
) as tunnel:
    conn = psycopg2.connect(
        host='localhost',
        port=tunnel.local_bind_port,
        database='sfdashboard_dev',
        user='sfdashboard',
        password='devpassword',
        connect_timeout=10,
    )
    print("Connected!")

    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY table_schema, table_name
        """)

        for schema, table in cursor.fetchall():
            print(f"{schema}.{table}")

    conn.close()
