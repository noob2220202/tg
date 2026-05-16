import aiosqlite
from config import DB_PATH

_db: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    global _db
    if _db is None:
        _db = await aiosqlite.connect(DB_PATH)
        _db.row_factory = aiosqlite.Row
        await _db.execute("PRAGMA journal_mode=WAL")
        await _db.execute("PRAGMA foreign_keys=ON")
    return _db


async def init_db() -> None:
    db = await get_db()
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS tickets (
            user_id INTEGER PRIMARY KEY,
            topic_id INTEGER UNIQUE NOT NULL,
            category TEXT NOT NULL,
            status TEXT DEFAULT 'open',
            after_hours_notified INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            closed_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS topic_to_user (
            topic_id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS bans (
            user_id INTEGER PRIMARY KEY,
            reason TEXT,
            banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            admin_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS faqs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keywords TEXT NOT NULL,
            answer TEXT NOT NULL,
            category TEXT,
            enabled INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS archive (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT,
            opened_at TIMESTAMP,
            closed_at TIMESTAMP,
            message_count INTEGER
        );
    """)
    await db.commit()


async def close_db() -> None:
    global _db
    if _db:
        await _db.close()
        _db = None


# ── ticket helpers ──────────────────────────────────────────────────────────

async def get_ticket(user_id: int) -> aiosqlite.Row | None:
    db = await get_db()
    async with db.execute(
        "SELECT * FROM tickets WHERE user_id = ? AND status = 'open'", (user_id,)
    ) as cur:
        return await cur.fetchone()


async def get_ticket_by_topic(topic_id: int) -> aiosqlite.Row | None:
    db = await get_db()
    async with db.execute(
        "SELECT t.* FROM tickets t JOIN topic_to_user m ON t.user_id = m.user_id "
        "WHERE m.topic_id = ?",
        (topic_id,),
    ) as cur:
        return await cur.fetchone()


async def create_ticket(user_id: int, topic_id: int, category: str) -> None:
    db = await get_db()
    await db.execute(
        "INSERT OR REPLACE INTO tickets (user_id, topic_id, category, status) VALUES (?,?,?,'open')",
        (user_id, topic_id, category),
    )
    await db.execute(
        "INSERT OR REPLACE INTO topic_to_user (topic_id, user_id) VALUES (?,?)",
        (topic_id, user_id),
    )
    await db.commit()


async def close_ticket(user_id: int) -> None:
    db = await get_db()
    ticket = await get_ticket(user_id)
    if not ticket:
        return
    await db.execute(
        "UPDATE tickets SET status='closed', closed_at=CURRENT_TIMESTAMP WHERE user_id=?",
        (user_id,),
    )
    async with db.execute(
        "SELECT COUNT(*) as cnt FROM archive WHERE user_id=?", (user_id,)
    ) as cur:
        pass
    await db.execute(
        "INSERT INTO archive (user_id, category, opened_at, closed_at) "
        "VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
        (user_id, ticket["category"], ticket["created_at"]),
    )
    await db.commit()


async def set_after_hours_notified(user_id: int) -> None:
    db = await get_db()
    await db.execute(
        "UPDATE tickets SET after_hours_notified=1 WHERE user_id=?", (user_id,)
    )
    await db.commit()


# ── ban helpers ─────────────────────────────────────────────────────────────

async def is_banned(user_id: int) -> bool:
    db = await get_db()
    async with db.execute("SELECT 1 FROM bans WHERE user_id=?", (user_id,)) as cur:
        return await cur.fetchone() is not None


async def ban_user(user_id: int, reason: str = "") -> None:
    db = await get_db()
    await db.execute(
        "INSERT OR REPLACE INTO bans (user_id, reason) VALUES (?,?)", (user_id, reason)
    )
    await db.commit()


async def unban_user(user_id: int) -> bool:
    db = await get_db()
    cur = await db.execute("DELETE FROM bans WHERE user_id=?", (user_id,))
    await db.commit()
    return cur.rowcount > 0


# ── note helpers ────────────────────────────────────────────────────────────

async def add_note(user_id: int, admin_id: int, content: str) -> None:
    db = await get_db()
    await db.execute(
        "INSERT INTO notes (user_id, admin_id, content) VALUES (?,?,?)",
        (user_id, admin_id, content),
    )
    await db.commit()


async def get_recent_notes(user_id: int, limit: int = 5) -> list[aiosqlite.Row]:
    db = await get_db()
    async with db.execute(
        "SELECT * FROM notes WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit),
    ) as cur:
        return await cur.fetchall()


# ── archive/stats helpers ────────────────────────────────────────────────────

async def get_archive_count(user_id: int) -> tuple[int, str | None]:
    db = await get_db()
    async with db.execute(
        "SELECT COUNT(*) as cnt, MAX(closed_at) as last FROM archive WHERE user_id=?",
        (user_id,),
    ) as cur:
        row = await cur.fetchone()
        return (row["cnt"] if row else 0, row["last"] if row else None)


# ── faq helpers ─────────────────────────────────────────────────────────────

async def get_faqs(category: str | None = None) -> list[aiosqlite.Row]:
    db = await get_db()
    if category:
        async with db.execute(
            "SELECT * FROM faqs WHERE enabled=1 AND (category=? OR category IS NULL)",
            (category,),
        ) as cur:
            return await cur.fetchall()
    async with db.execute("SELECT * FROM faqs WHERE enabled=1") as cur:
        return await cur.fetchall()


async def add_faq(keywords: str, answer: str, category: str | None) -> int:
    db = await get_db()
    cur = await db.execute(
        "INSERT INTO faqs (keywords, answer, category) VALUES (?,?,?)",
        (keywords, answer, category),
    )
    await db.commit()
    return cur.lastrowid


async def delete_faq(faq_id: int) -> bool:
    db = await get_db()
    cur = await db.execute("DELETE FROM faqs WHERE id=?", (faq_id,))
    await db.commit()
    return cur.rowcount > 0


async def toggle_faq(faq_id: int) -> bool | None:
    db = await get_db()
    async with db.execute("SELECT enabled FROM faqs WHERE id=?", (faq_id,)) as cur:
        row = await cur.fetchone()
    if not row:
        return None
    new_val = 0 if row["enabled"] else 1
    await db.execute("UPDATE faqs SET enabled=? WHERE id=?", (new_val, faq_id))
    await db.commit()
    return bool(new_val)


async def list_all_faqs() -> list[aiosqlite.Row]:
    db = await get_db()
    async with db.execute("SELECT * FROM faqs ORDER BY id") as cur:
        return await cur.fetchall()
