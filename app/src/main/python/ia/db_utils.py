"""Database utilities and formatters for TPV Smart IA."""
import sqlite3, os

def _db():
    """Get database connection."""
    for p in ['tpv_datos.db',
              os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tpv_datos.db')]:
        if os.path.exists(p):
            c = sqlite3.connect(p, timeout=3, check_same_thread=False)
            c.row_factory = sqlite3.Row
            return c
    return None

def q(sql, params=(), one=False):
    """Execute query and return results."""
    c = _db()
    if not c:
        return None
    try:
        cur = c.execute(sql, params)
        return cur.fetchone() if one else cur.fetchall()
    except:
        return None

def fmt_money(v):
    """Format number as currency."""
    return f"${float(v):,.2f}" if v else "$0.00"

def pct(v):
    """Format number as percentage."""
    return f"{float(v):.1f}%"
