import sqlite3
import threading
from flask import Flask
import telebot
from telebot import types

# ============================================================
# VICKY SMM BOARD - MAIN CONFIG
# EDIT ONLY THIS SECTION
# ============================================================

BOT_TOKEN = "8849432779:AAHOaeoFEArwjeZCRuQqPq46QIrFfJ9MhKA"

# Add one or more Telegram numeric Admin IDs
ADMIN_IDS = [
    8700582148
]

BOT_NAME = "SMMSHOPS_Bot"
SUPPORT_USERNAME = "@Vickyffstore1"
PORT = 8080

# Default UI settings
DEFAULT_BUTTON_STYLE = "PRIMARY"

# ============================================================
# END OF MAIN CONFIG
# ============================================================

if not BOT_TOKEN or BOT_TOKEN == "PASTE_YOUR_BOT_TOKEN_HERE":
    raise RuntimeError("Please enter your BOT_TOKEN at the top of bot.py.")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ============================================================
# GLOBAL UI FONT
# All visible bot text uses this font EXCEPT the welcome text.
# Example: PRODUCT STORE -> ᴩʀᴏᴅᴜᴄᴛ ꜱᴛᴏʀᴇ
# ============================================================
_FONT_MAP = str.maketrans({
    "a":"ᴀ","b":"ʙ","c":"ᴄ","d":"ᴅ","e":"ᴇ","f":"ꜰ","g":"ɢ","h":"ʜ","i":"ɪ","j":"ᴊ",
    "k":"ᴋ","l":"ʟ","m":"ᴍ","n":"ɴ","o":"ᴏ","p":"ᴩ","q":"ǫ","r":"ʀ","s":"ꜱ","t":"ᴛ",
    "u":"ᴜ","v":"ᴠ","w":"ᴡ","x":"x","y":"ʏ","z":"ᴢ",
    "A":"ᴀ","B":"ʙ","C":"ᴄ","D":"ᴅ","E":"ᴇ","F":"ꜰ","G":"ɢ","H":"ʜ","I":"ɪ","J":"ᴊ",
    "K":"ᴋ","L":"ʟ","M":"ᴍ","N":"ɴ","O":"ᴏ","P":"ᴩ","Q":"ǫ","R":"ʀ","S":"ꜱ","T":"ᴛ",
    "U":"ᴜ","V":"ᴠ","W":"ᴡ","X":"x","Y":"ʏ","Z":"ᴢ"
})

def _font_text(text):
    if not isinstance(text, str):
        return text

    import re

    # Keep HTML tags, <code> blocks, commands and @usernames unchanged.
    protected = []

    def protect(match):
        protected.append(match.group(0))
        return f"\x00{len(protected)-1}\x00"

    text = re.sub(r"<code>.*?</code>", protect, text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]*>", protect, text)
    text = re.sub(r"(?:https?://|tg://)\S+", protect, text)
    text = re.sub(r"(?<!\w)(/[\w_]+)", protect, text)
    text = re.sub(r"(?<!\w)@[\w_]+", protect, text)

    text = text.translate(_FONT_MAP)

    for i, value in enumerate(protected):
        text = text.replace(f"\x00{i}\x00", value)

    return text

# Style all inline-button labels automatically.
_OriginalInlineKeyboardButton = types.InlineKeyboardButton
def _FontInlineKeyboardButton(text, *args, **kwargs):
    return _OriginalInlineKeyboardButton(_font_text(text), *args, **kwargs)

types.InlineKeyboardButton = _FontInlineKeyboardButton

# Style all outgoing Telegram text automatically, while leaving HOME_TITLE unchanged.
def _font_outgoing_text(text):
    try:
        if text == get_text("HOME_TITLE"):
            return text
    except Exception:
        pass
    return _font_text(text)

_original_send_message = bot.send_message
_original_edit_message_text = bot.edit_message_text
_original_reply_to = bot.reply_to
_original_answer_callback_query = bot.answer_callback_query

def _send_message_font(chat_id, text, *args, **kwargs):
    return _original_send_message(chat_id, _font_outgoing_text(text), *args, **kwargs)

def _edit_message_text_font(text, *args, **kwargs):
    return _original_edit_message_text(_font_outgoing_text(text), *args, **kwargs)

def _reply_to_font(message, text, *args, **kwargs):
    return _original_reply_to(message, _font_outgoing_text(text), *args, **kwargs)

def _answer_callback_query_font(callback_query_id, text=None, *args, **kwargs):
    if text is not None:
        text = _font_outgoing_text(text)
    return _original_answer_callback_query(callback_query_id, text, *args, **kwargs)

bot.send_message = _send_message_font
bot.edit_message_text = _edit_message_text_font
bot.reply_to = _reply_to_font
bot.answer_callback_query = _answer_callback_query_font
DB = "smm_board.db"
app = Flask(__name__)


# =========================
# DATABASE
# =========================
def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db()
    con.executescript("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        emoji TEXT DEFAULT '',
        description TEXT DEFAULT '',
        button_style TEXT DEFAULT 'PRIMARY',
        status INTEGER DEFAULT 1,
        position INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        emoji TEXT DEFAULT '',
        description TEXT DEFAULT '',
        price REAL DEFAULT 0,
        min_qty INTEGER DEFAULT 1,
        max_qty INTEGER DEFAULT 1000,
        button_style TEXT DEFAULT 'PRIMARY',
        status INTEGER DEFAULT 1,
        position INTEGER DEFAULT 0,
        FOREIGN KEY(category_id) REFERENCES categories(id)
    );

    CREATE TABLE IF NOT EXISTS ui_texts (
        key TEXT PRIMARY KEY,
        text TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT DEFAULT '',
        first_name TEXT DEFAULT '',
        balance REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    defaults = {
        "SHOP_TITLE": "VICKY SMM BOARD",
        "HOME_TITLE": "╔════════════════════╗\n   🏪 VICKY SMM BOARD\n╚════════════════════╝",
        "CATEGORY_TITLE": "Select a category:",
        "SERVICE_TITLE": "Select service:",
        "PROFILE_TEXT": "👤 <b>My Profile</b>",
        "BALANCE_TEXT": "💰 Your balance: ₹{balance:.2f}",
        "NO_CATEGORY": "No categories are available right now.",
        "NO_PRODUCT": "No services are available in this category.",
        "ADMIN_TITLE": "👑 <b>ADMIN PANEL</b>",
    }
    for k, v in defaults.items():
        con.execute(
            "INSERT OR IGNORE INTO ui_texts(key,text) VALUES(?,?)", (k, v)
        )

    con.commit()
    con.close()

def get_text(key, **kwargs):
    con = db()
    row = con.execute("SELECT text FROM ui_texts WHERE key=?", (key,)).fetchone()
    con.close()
    value = row["text"] if row else key
    try:
        return value.format(**kwargs)
    except Exception:
        return value

def set_text(key, value):
    con = db()
    con.execute(
        "INSERT INTO ui_texts(key,text) VALUES(?,?) "
        "ON CONFLICT(key) DO UPDATE SET text=excluded.text",
        (key, value)
    )
    con.commit()
    con.close()

def is_admin(user_id):
    return user_id in set(ADMIN_IDS)

def save_user(message):
    u = message.from_user
    con = db()
    con.execute("""
        INSERT INTO users(user_id,username,first_name)
        VALUES(?,?,?)
        ON CONFLICT(user_id) DO UPDATE SET
        username=excluded.username,
        first_name=excluded.first_name
    """, (u.id, u.username or "", u.first_name or ""))
    con.commit()
    con.close()


# =========================
# BUTTON STYLES
# =========================
# Telegram inline buttons do not support arbitrary background colors.
# These styles are logical styles; emoji/text/layout are fully configurable.
STYLES = {
    "PRIMARY": "🔵",
    "SUCCESS": "🟢",
    "DANGER": "🔴",
    "WARNING": "🟡",
    "DARK": "⚫",
    "SECONDARY": "⚪",
    "CUSTOM": ""
}

def styled_button(text, style="PRIMARY", emoji=""):
    prefix = emoji if emoji else STYLES.get(style, "")
    return f"{prefix} {text}".strip()


# =========================
# USER UI
# =========================
def home_markup():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🛒 Services", callback_data="categories"),
        types.InlineKeyboardButton("💰 Add Balance", callback_data="balance"),
    )
    kb.add(
        types.InlineKeyboardButton("📦 My Orders", callback_data="orders"),
        types.InlineKeyboardButton("👤 My Profile", callback_data="profile"),
    )
    kb.add(
        types.InlineKeyboardButton("🎁 Referral", callback_data="referral"),
        types.InlineKeyboardButton("🎧 Support", callback_data="support"),
    )
    if ADMIN_IDS:
        # Admin button is only visible to admins.
        return kb
    return kb

def categories_markup():
    con = db()
    rows = con.execute(
        "SELECT * FROM categories WHERE status=1 ORDER BY position,id"
    ).fetchall()
    con.close()

    kb = types.InlineKeyboardMarkup(row_width=2)
    for r in rows:
        label = styled_button(r["name"], r["button_style"], r["emoji"])
        kb.add(types.InlineKeyboardButton(label, callback_data=f"cat:{r['id']}"))
    kb.add(types.InlineKeyboardButton("🏠 Home", callback_data="home"))
    return kb

def products_markup(category_id):
    con = db()
    rows = con.execute(
        "SELECT * FROM products WHERE category_id=? AND status=1 "
        "ORDER BY position,id", (category_id,)
    ).fetchall()
    con.close()

    kb = types.InlineKeyboardMarkup(row_width=1)
    for r in rows:
        label = styled_button(r["name"], r["button_style"], r["emoji"])
        kb.add(types.InlineKeyboardButton(label, callback_data=f"prod:{r['id']}"))
    kb.add(types.InlineKeyboardButton("⬅️ Categories", callback_data="categories"))
    return kb


@bot.message_handler(commands=["start"])
def start(message):
    save_user(message)
    bot.send_message(
        message.chat.id,
        get_text("HOME_TITLE"),
        reply_markup=home_markup()
    )


@bot.callback_query_handler(func=lambda c: c.data == "home")
def cb_home(call):
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        get_text("HOME_TITLE"),
        call.message.chat.id,
        call.message.message_id,
        reply_markup=home_markup()
    )


@bot.callback_query_handler(func=lambda c: c.data == "categories")
def cb_categories(call):
    bot.answer_callback_query(call.id)
    text = get_text("CATEGORY_TITLE")
    con = db()
    count = con.execute(
        "SELECT COUNT(*) AS c FROM categories WHERE status=1"
    ).fetchone()["c"]
    con.close()
    if count == 0:
        text += "\n\n" + get_text("NO_CATEGORY")
    bot.edit_message_text(
        text, call.message.chat.id, call.message.message_id,
        reply_markup=categories_markup()
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("cat:"))
def cb_category(call):
    category_id = int(call.data.split(":")[1])
    con = db()
    cat = con.execute(
        "SELECT * FROM categories WHERE id=? AND status=1",
        (category_id,)
    ).fetchone()
    count = con.execute(
        "SELECT COUNT(*) AS c FROM products WHERE category_id=? AND status=1",
        (category_id,)
    ).fetchone()["c"]
    con.close()

    if not cat:
        bot.answer_callback_query(call.id, "Category not found.", show_alert=True)
        return

    title = styled_button(cat["name"], cat["button_style"], cat["emoji"])
    text = (
        f"╔════════════════════╗\n"
        f"   {title}\n"
        f"╚════════════════════╝\n\n"
        f"{get_text('SERVICE_TITLE')}"
    )
    if cat["description"]:
        text += f"\n\n{cat['description']}"
    if count == 0:
        text += "\n\n" + get_text("NO_PRODUCT")

    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        text, call.message.chat.id, call.message.message_id,
        reply_markup=products_markup(category_id)
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("prod:"))
def cb_product(call):
    product_id = int(call.data.split(":")[1])
    con = db()
    p = con.execute("""
        SELECT p.*, c.name AS category_name
        FROM products p JOIN categories c ON c.id=p.category_id
        WHERE p.id=? AND p.status=1
    """, (product_id,)).fetchone()
    con.close()

    if not p:
        bot.answer_callback_query(call.id, "Product not found.", show_alert=True)
        return

    title = styled_button(p["name"], p["button_style"], p["emoji"])
    text = (
        f"╔════════════════════╗\n"
        f"   {title}\n"
        f"╚════════════════════╝\n\n"
        f"{p['description']}\n\n"
        f"💵 Price: ₹{p['price']:.2f}\n"
        f"📦 Min: {p['min_qty']} | Max: {p['max_qty']}"
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(
        "🛒 Order", callback_data=f"order:{p['id']}"
    ))
    kb.add(types.InlineKeyboardButton(
        "⬅️ Back", callback_data=f"cat:{p['category_id']}"
    ))
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        text, call.message.chat.id, call.message.message_id,
        reply_markup=kb
    )


@bot.callback_query_handler(func=lambda c: c.data == "profile")
def cb_profile(call):
    con = db()
    u = con.execute("SELECT * FROM users WHERE user_id=?", (call.from_user.id,)).fetchone()
    con.close()
    balance = u["balance"] if u else 0
    text = (
        f"{get_text('PROFILE_TEXT')}\n\n"
        f"🆔 ID: <code>{call.from_user.id}</code>\n"
        f"👤 Name: {call.from_user.first_name or '-'}\n"
        f"💰 Balance: ₹{balance:.2f}"
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🏠 Home", callback_data="home"))
    bot.answer_callback_query(call.id)
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == "balance")
def cb_balance(call):
    bot.answer_callback_query(call.id)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅️ Home", callback_data="home"))
    bot.edit_message_text(
        "💰 <b>Add Balance</b>\n\nPayment gateway can be connected here.",
        call.message.chat.id, call.message.message_id, reply_markup=kb
    )


@bot.callback_query_handler(func=lambda c: c.data == "orders")
def cb_orders(call):
    bot.answer_callback_query(call.id)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🏠 Home", callback_data="home"))
    bot.edit_message_text(
        "📦 <b>My Orders</b>\n\nOrder database/API integration can be connected here.",
        call.message.chat.id, call.message.message_id, reply_markup=kb
    )


@bot.callback_query_handler(func=lambda c: c.data == "referral")
def cb_referral(call):
    bot.answer_callback_query(call.id)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🏠 Home", callback_data="home"))
    bot.edit_message_text(
        "🎁 <b>Referral</b>\n\nReferral system can be configured from Admin.",
        call.message.chat.id, call.message.message_id, reply_markup=kb
    )


@bot.callback_query_handler(func=lambda c: c.data == "support")
def cb_support(call):
    bot.answer_callback_query(call.id)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🏠 Home", callback_data="home"))
    bot.edit_message_text(
        "🎧 <b>Support</b>\n\nSet your support username/link from Admin.",
        call.message.chat.id, call.message.message_id, reply_markup=kb
    )


# =========================
# ADMIN PANEL
# =========================
def admin_markup():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📂 Categories", callback_data="adm:cats"),
        types.InlineKeyboardButton("📦 Products", callback_data="adm:products"),
    )
    kb.add(
        types.InlineKeyboardButton("📝 Text Manager", callback_data="adm:texts"),
        types.InlineKeyboardButton("😀 Emoji/UI", callback_data="adm:ui"),
    )
    kb.add(
        types.InlineKeyboardButton("👥 Users", callback_data="adm:users"),
        types.InlineKeyboardButton("⚙️ Settings", callback_data="adm:settings"),
    )
    return kb

@bot.message_handler(commands=["admin"])
def admin_cmd(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Access denied.")
        return
    bot.send_message(message.chat.id, get_text("ADMIN_TITLE"), reply_markup=admin_markup())

@bot.callback_query_handler(func=lambda c: c.data.startswith("adm:"))
def admin_callback(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "Access denied.", show_alert=True)
        return

    action = call.data.split(":")[1]

    if action == "cats":
        con = db()
        rows = con.execute("SELECT * FROM categories ORDER BY position,id").fetchall()
        con.close()
        text = "📂 <b>CATEGORIES</b>\n\n"
        if not rows:
            text += "No categories yet."
        for r in rows:
            text += f"#{r['id']} • {r['emoji']} {r['name']} • {'ON' if r['status'] else 'OFF'}\n"
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("➕ Add Category", callback_data="adm:addcat"))
        kb.add(types.InlineKeyboardButton("⬅️ Admin", callback_data="adm:back"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)

    elif action == "products":
        con = db()
        rows = con.execute("""
            SELECT p.*, c.name AS category_name
            FROM products p JOIN categories c ON c.id=p.category_id
            ORDER BY c.id,p.position,p.id
        """).fetchall()
        con.close()
        text = "📦 <b>PRODUCTS</b>\n\n"
        if not rows:
            text += "No products yet."
        for r in rows:
            text += f"#{r['id']} • {r['emoji']} {r['name']} • ₹{r['price']:.2f} • {r['category_name']}\n"
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("➕ Add Product", callback_data="adm:addprod"))
        kb.add(types.InlineKeyboardButton("⬅️ Admin", callback_data="adm:back"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)

    elif action == "texts":
        con = db()
        rows = con.execute("SELECT * FROM ui_texts ORDER BY key").fetchall()
        con.close()
        text = "📝 <b>TEXT MANAGER</b>\n\n"
        for r in rows:
            preview = r["text"].replace("\n", " ")[:60]
            text += f"<code>{r['key']}</code> → {preview}\n"
        text += "\nUse:\n<code>/settext KEY New text here</code>"
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("⬅️ Admin", callback_data="adm:back"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)

    elif action == "ui":
        text = (
            "😀 <b>EMOJI / UI MANAGER</b>\n\n"
            "Product/category emoji is stored per item.\n"
            "Use the Admin add commands to set custom emoji text/ID.\n\n"
            "Telegram inline buttons don't have real CSS colors; "
            "the bot uses logical styles such as PRIMARY, SUCCESS, DANGER, WARNING."
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("⬅️ Admin", callback_data="adm:back"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)

    elif action == "users":
        con = db()
        count = con.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        con.close()
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("⬅️ Admin", callback_data="adm:back"))
        bot.edit_message_text(
            f"👥 <b>USERS</b>\n\nTotal users: {count}",
            call.message.chat.id, call.message.message_id, reply_markup=kb
        )

    elif action == "settings":
        bot.edit_message_text(
            "⚙️ <b>SETTINGS</b>\n\n"
            "Environment variables:\n"
            "BOT_TOKEN\nADMIN_IDS\nPORT",
            call.message.chat.id, call.message.message_id,
            reply_markup=back_admin()
        )

    elif action == "back":
        bot.edit_message_text(
            get_text("ADMIN_TITLE"),
            call.message.chat.id, call.message.message_id,
            reply_markup=admin_markup()
        )

    elif action == "addcat":
        msg = bot.send_message(
            call.message.chat.id,
            "Send category in this format:\n\n"
            "<code>/addcat Name | CustomEmoji | Description | STYLE</code>\n\n"
            "Example:\n"
            "<code>/addcat INSTAGRAM SERVICES | 🔥 | Select Instagram service: | PRIMARY</code>"
        )
        bot.register_next_step_handler(msg, lambda m: None)

    elif action == "addprod":
        bot.send_message(
            call.message.chat.id,
            "Add product with:\n\n"
            "<code>/addprod CATEGORY_ID | Product Name | Emoji | Description | Price | Min | Max | STYLE</code>"
        )

def back_admin():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅️ Admin", callback_data="adm:back"))
    return kb


@bot.message_handler(commands=["settext"])
def cmd_settext(message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split(" ", 2)
    if len(parts) < 3:
        bot.reply_to(message, "Format: /settext KEY New text")
        return
    set_text(parts[1].upper(), parts[2])
    bot.reply_to(message, f"✅ <code>{parts[1].upper()}</code> updated.")


@bot.message_handler(commands=["addcat"])
def cmd_addcat(message):
    if not is_admin(message.from_user.id):
        return
    raw = message.text.partition(" ")[2]
    parts = [x.strip() for x in raw.split("|")]
    if len(parts) < 4:
        bot.reply_to(message, "Format: /addcat Name | Emoji | Description | STYLE")
        return
    name, emoji, desc, style = parts[:4]
    con = db()
    pos = con.execute("SELECT COALESCE(MAX(position),0)+1 AS p FROM categories").fetchone()["p"]
    con.execute(
        "INSERT INTO categories(name,emoji,description,button_style,position) VALUES(?,?,?,?,?)",
        (name, emoji, desc, style.upper(), pos)
    )
    con.commit()
    con.close()
    bot.reply_to(message, "✅ Category added.")


@bot.message_handler(commands=["addprod"])
def cmd_addprod(message):
    if not is_admin(message.from_user.id):
        return
    raw = message.text.partition(" ")[2]
    parts = [x.strip() for x in raw.split("|")]
    if len(parts) < 8:
        bot.reply_to(
            message,
            "Format:\n/addprod CATEGORY_ID | Name | Emoji | Description | Price | Min | Max | STYLE"
        )
        return
    try:
        category_id = int(parts[0])
        name, emoji, desc = parts[1:4]
        price = float(parts[4])
        min_qty = int(parts[5])
        max_qty = int(parts[6])
        style = parts[7].upper()
    except ValueError:
        bot.reply_to(message, "❌ Invalid number in product data.")
        return

    con = db()
    exists = con.execute("SELECT id FROM categories WHERE id=?", (category_id,)).fetchone()
    if not exists:
        con.close()
        bot.reply_to(message, "❌ Category ID not found.")
        return
    pos = con.execute(
        "SELECT COALESCE(MAX(position),0)+1 AS p FROM products WHERE category_id=?",
        (category_id,)
    ).fetchone()["p"]
    con.execute("""
        INSERT INTO products
        (category_id,name,emoji,description,price,min_qty,max_qty,button_style,position)
        VALUES(?,?,?,?,?,?,?,?,?)
    """, (category_id,name,emoji,desc,price,min_qty,max_qty,style,pos))
    con.commit()
    con.close()
    bot.reply_to(message, "✅ Product added.")


# =========================
# ORDER PLACEHOLDER
# =========================
@bot.callback_query_handler(func=lambda c: c.data.startswith("order:"))
def cb_order(call):
    bot.answer_callback_query(
        call.id,
        "Order/payment API can be connected here.",
        show_alert=True
    )


# =========================
# WEB KEEP-ALIVE
# =========================
@app.get("/")
def index():
    return "VICKY SMM BOARD BOT IS RUNNING"

def run_web():
    app.run(host="0.0.0.0", port=PORT, use_reloader=False)

if __name__ == "__main__":
    init_db()
    threading.Thread(target=run_web, daemon=True).start()
    print("VICKY SMM BOARD BOT RUNNING...")
    bot.infinity_polling(skip_pending=True)
