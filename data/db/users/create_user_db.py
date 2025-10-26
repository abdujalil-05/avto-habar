from ..connection.connection import get_pool


async def create_user_db():
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            # Users jadvali
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    telegram_id BIGINT NOT NULL UNIQUE,
                    username VARCHAR(255),
                    phone_number VARCHAR(20),
                    name VARCHAR(255) NOT NULL,
                    status VARCHAR(50),
                    free_message DATETIME,
                    user_start_bot DATETIME DEFAULT CURRENT_TIMESTAMP,
                    paket_start_time DATETIME,
                    paket_end_time DATETIME,
                    user_balance DECIMAL(15,2) DEFAULT 0.00,
                    messages_id VARCHAR(300),
                    channel_group_date_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    channel_count INT DEFAULT 0,
                    group_count INT DEFAULT 0,
                    user_status BOOLEAN DEFAULT False NOT NULL,
                    userSession TEXT,
                    user_groups TEXT
                )
            """)