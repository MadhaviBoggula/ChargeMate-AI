from sqlalchemy import text

from app.database.database import engine


def check_table():
    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'recommendations'
                ORDER BY ordinal_position;
                """
            )
        )

        rows = result.fetchall()

        if not rows:
            print("No recommendations table found")
        else:
            print("Recommendations table columns:")
            for row in rows:
                print(row)


if __name__ == "__main__":
    check_table()