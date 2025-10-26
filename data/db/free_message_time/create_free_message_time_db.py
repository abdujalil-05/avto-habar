from ..connection.connection import get_pool

async def create_free_message_time_db():
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            # Jadvalni yaratish
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS free_time (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    time INT DEFAULT 240 NOT NULL
                )
            """)
            await conn.commit()

            # Jadval bo‘shligini tekshirish
            await cursor.execute("SELECT * FROM free_time")
            check = await cursor.fetchall()
            if not check:
                await cursor.execute("""
                    INSERT INTO free_time (time)
                    VALUES (%s)
                """, (240,))
                await conn.commit()
