from dotenv import load_dotenv
load_dotenv()
from services.database import get_connection
from security.auth import hash_password, verify_password


def create_user(username, email, password, full_name, phone=None, date_of_birth=None, address=None, role="CUSTOMER", customer_id=None):
    role = role.upper()
    if role not in {"CUSTOMER", "ANALYST", "QA", "ADMIN"}:
        raise ValueError("Invalid role")
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute("""INSERT INTO users (username,email,full_name,phone,date_of_birth,address,password_hash,role,active,customer_id) VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (username.strip(), email.lower().strip(), full_name.strip(), phone, date_of_birth, address, hash_password(password), role, 1, customer_id))
        conn.commit(); user_id = cur.lastrowid
        return get_user_by_id(user_id)
    except Exception:
        conn.rollback(); raise
    finally:
        conn.close()


def get_user_by_id(user_id):
    conn=get_connection(); cur=conn.cursor(); cur.execute("SELECT * FROM users WHERE id=?", (user_id,)); row=cur.fetchone(); conn.close()
    return dict(row) if row else None


def get_user_by_login(login):
    conn=get_connection(); cur=conn.cursor(); cur.execute("SELECT * FROM users WHERE lower(username)=lower(?) OR lower(email)=lower(?)", (login, login)); row=cur.fetchone(); conn.close()
    return dict(row) if row else None


def get_all_users():
    conn=get_connection(); cur=conn.cursor(); cur.execute("SELECT id,username,email,full_name,phone,date_of_birth,address,role,active,customer_id,created_at FROM users ORDER BY id DESC"); rows=cur.fetchall(); conn.close(); return [dict(r) for r in rows]


def update_user(user_id, role=None, active=None):
    fields=[]; values=[]
    if role is not None:
        role=role.upper()
        if role not in {"CUSTOMER","ANALYST","QA","ADMIN"}: raise ValueError("Invalid role")
        fields.append("role=?"); values.append(role)
    if active is not None:
        fields.append("active=?"); values.append(1 if active else 0)
    if not fields: return get_user_by_id(user_id)
    values.append(user_id)
    conn=get_connection(); cur=conn.cursor(); cur.execute(f"UPDATE users SET {', '.join(fields)} WHERE id=?", values); conn.commit(); conn.close(); return get_user_by_id(user_id)


def authenticate(login, password):
    user=get_user_by_login(login)
    if not user or not user.get("active") or not verify_password(password, user["password_hash"]):
        return None
    return user


def ensure_admin():
    import os
    username=os.getenv("ADMIN_USERNAME")
    email=os.getenv("ADMIN_EMAIL")
    password=os.getenv("ADMIN_PASSWORD")
    if not (username and email and password): return
    if get_user_by_login(username): return
    try:
        create_user(username, email, password, os.getenv("ADMIN_FULL_NAME", "OnboardAI Administrator"), role="ADMIN")
    except Exception:
        pass
