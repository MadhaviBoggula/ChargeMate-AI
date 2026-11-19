from sqlalchemy import text

from app.database.database import engine


with engine.connect() as conn:
    conn.execute(
        text(
            """
            UPDATE recommendations
            SET confidence = 0.0
            WHERE confidence IS NULL;
            """
        )
    )

    conn.commit()

print("Fixed NULL confidence values")