import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS groups (group_id BIGINT PRIMARY KEY, welcome_text TEXT, welcome_photo_id TEXT, admin_ids TEXT DEFAULT '[]', verified BOOLEAN DEFAULT FALSE)")
    cur.execute("CREATE TABLE IF NOT EXISTS triggers (id SERIAL PRIMARY KEY, group_id BIGINT, word TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS tasks (id SERIAL PRIMARY KEY, group_id BIGINT, task_hour INT, message_text TEXT)")
    conn.commit()
    cur.close()
    conn.close()

def get_verified_status(group_id):
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT verified FROM groups WHERE group_id = %s", (group_id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row[0] if row else False

def set_verified_status(group_id, status):
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("INSERT INTO groups (group_id, verified) VALUES (%s, %s) ON CONFLICT (group_id) DO UPDATE SET verified = excluded.verified", (group_id, status))
    conn.commit(); cur.close(); conn.close()

# ===== 【新增】获取机器人在哪些群里 =====
def get_all_authorized_groups():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT group_id FROM groups WHERE verified = TRUE")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [row[0] for row in rows]
