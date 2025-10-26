from ..connection.connection import get_pool


async def create_message_db():
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    message TEXT NOT NULL,
                    message_interval INT DEFAULT 5,
                    file_reference TEXT,
                    groups_id TEXT,
                    user_id BIGINT NOT NULL, 
                    end_time DATETIME,
                    message_status BOOLEAN DEFAULT TRUE,
                    session TEXT,
                    last_message_time DATETIME,
                    channel_photo_id BIGINT,
                    last_reference_time DATETIME,
                    end_reference_time DATETIME,
                    photo_id BIGINT,
                    access_hash BIGINT
                )
            """)






# @router.message(F.photo)
# async def handle_photo(message: Message):
#     file_id = message.photo[-1].file_id
#     msg_id = message.message_id
#     user_id = message.from_user.id

#     print(f"📸 Rasm kelib tushdi! file_id={file_id}, msg_id={msg_id}, user_id={user_id}")

#     # Shu msg_id ni DB ga saqlaysan




# from telethon import TelegramClient

# async def forward_to_saved_and_get_reference(client: TelegramClient, bot_id: int, message_id: int):
#     """
#     Bot bilan chatdagi xabarni saqlangan habarlarga forward qiladi
#     va yangi file_reference ni qaytaradi.
#     """
#     try:
#         # Bot bilan dialogni olamiz
#         bot_entity = await client.get_entity(bot_id)

#         # Forward qilish
#         forwarded_msg = await client.forward_messages("me", message_id, bot_entity)
#         print("✅ Forward qilindi -> Saved Messages")

#         # File reference olish
#         if forwarded_msg.photo:
#             ref = forwarded_msg.photo.file_reference
#         elif forwarded_msg.document:
#             ref = forwarded_msg.document.file_reference
#         else:
#             ref = None

#         print(f"🆔 file_reference: {ref}")

#         # Forward qilingan xabarni o‘chiramiz
#         await client.delete_messages("me", [forwarded_msg.id])
#         print("🗑️ Forward qilingan xabar o‘chirildi")

#         return ref

#     except Exception as e:
#         print(f"❌ Xato: {e}")
#         return None
