from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup



# def all_groups_button(all_groups, page: int, total: int, per_page: int):
#     start = page * per_page
#     end = start + per_page
#     groups_page = all_groups[start:end]

#     keyboard = InlineKeyboardMarkup(inline_keyboard=[])

#     # Guruhlarni 2 tadan joylab chiqish
#     row = []
#     for i, group in enumerate(groups_page, start=1):
#         row.append(InlineKeyboardButton(
#             text=f"{group['check']} {group['title']}",
#             callback_data=f"groups_select_{group['id']}"
#         ))
#         if i % 2 == 0:
#             keyboard.inline_keyboard.append(row)
#             row = []
#     if row:
#         keyboard.inline_keyboard.append(row)

#     # Navigatsiya tugmalari
#     nav_row = []
#     if page > 0:
#         nav_row.append(InlineKeyboardButton(text="⬅️ Ortga", callback_data=f"groups_page_{page-1}"))
#     if end < total:
#         nav_row.append(InlineKeyboardButton(text="➡️ Oldinga", callback_data=f"groups_page_{page+1}"))
#     if nav_row:
#         keyboard.inline_keyboard.append(nav_row)

#     # Barchasini belgilash/o‘chirish tugmalari
#     keyboard.inline_keyboard.append([
#         InlineKeyboardButton(text="✅ Barchasini belgilash", callback_data="groups_select_all"),
#         InlineKeyboardButton(text="❌ Barchasini o‘chirish", callback_data="groups_unselect_all"),
#     ],
    
#     )
#     keyboard.inline_keyboard.append([
#         InlineKeyboardButton(text="Saqlash ♻️", callback_data="save_groups"),
#         InlineKeyboardButton(text="Bekor qilish 🔴", callback_data="cancel_groups"),
#     ])

#     return keyboard





















# =========================================
# Inline keyboard yaratish funksiyasi
# =========================================
def all_groups_button(all_groups, page: int, total: int, per_page: int):
    start = page * per_page
    end = min(start + per_page, total)
    groups_page = all_groups[start:end]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    # Guruhlarni 2 tadan joylash
    row = []
    for i, group in enumerate(groups_page, start=1):
        row.append(InlineKeyboardButton(
            text=f"{'✅' if group[2] else '❌'} {group[1]}",
            callback_data=f"groups_select_{group[0]}"
        ))
        if i % 2 == 0:
            keyboard.inline_keyboard.append(row)
            row = []
    if row:
        keyboard.inline_keyboard.append(row)

    # Navigatsiya tugmalari
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Ortga", callback_data=f"groups_page_{page-1}"))
    if end < total:
        nav_row.append(InlineKeyboardButton(text="➡️ Oldinga", callback_data=f"groups_page_{page+1}"))
    if nav_row:
        keyboard.inline_keyboard.append(nav_row)

    # Barchasini belgilash/o‘chirish tugmalari
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="✅ Barchasini belgilash", callback_data="groups_select_all"),
        InlineKeyboardButton(text="❌ Barchasini o‘chirish", callback_data="groups_unselect_all"),
    ])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="Saqlash ♻️", callback_data="save_groups"),
        InlineKeyboardButton(text="Bekor qilish 🔴", callback_data="cancel_groups"),
    ])
    return keyboard

