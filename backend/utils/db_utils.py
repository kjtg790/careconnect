from database import get_db_connection

def fetch_enum_values(table_name: str, column_name: str) -> list:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT unnest(enum_range(NULL::{table_name}.{column_name}::regtype))::text;
    """)
    values = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return values
