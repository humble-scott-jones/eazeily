import json
import os
import pathlib
import sqlite3
import subprocess
import time
from typing import Optional

import requests
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[2]
PORT = int(os.getenv("PORT", "5001"))
BASE = f"http://127.0.0.1:{PORT}"


def start_server() -> subprocess.Popen:
    """Start the Flask dev server with dev overrides enabled."""
    py = "./.venv/bin/python" if (ROOT / ".venv" / "bin" / "python").exists() else "python3"
    env = os.environ.copy()
    env.setdefault("ALLOW_DEV_DEBUG", "1")
    env.setdefault("FLASK_ENV", "development")

    try:
        requests.post(f"{BASE}/__dev__/shutdown", timeout=1)
        time.sleep(0.5)
    except Exception:
        pass
    proc = subprocess.Popen([py, "app.py"], cwd=str(ROOT), env=env)
    for _ in range(40):
        try:
            resp = requests.get(f"{BASE}/__dev__/ping", timeout=1)
            if resp.status_code == 200:
                return proc
        except Exception:
            pass
        time.sleep(0.5)
    proc.kill()
    raise RuntimeError("Server failed to start in time")


def stop_server(proc: Optional[subprocess.Popen]) -> None:
    if not proc:
        return
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def set_generation_usage(user_id: str, used: int, period: Optional[str] = None) -> None:
    if period is None:
        period = time.strftime("%Y-%m")
    db_path = ROOT / "togetherly.db"
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS generation_usage (id TEXT PRIMARY KEY, user_id TEXT, period TEXT, reels_generated INTEGER DEFAULT 0, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
        )
        cur.execute("DELETE FROM generation_usage WHERE user_id = ? AND period = ?", (user_id, period))
        cur.execute(
            "INSERT INTO generation_usage (id, user_id, period, reels_generated) VALUES (?, ?, ?, ?)",
            (str(time.time()), user_id, period, used),
        )
        conn.commit()
    finally:
        conn.close()


def test_playwright_full_flow(tmp_path):
    proc = start_server()
    session = requests.Session()
    gen_response = None
    webhook_response = None
    page = None
    context = None
    browser = None
    try:
        create_resp = session.post(
            f"{BASE}/__dev__/create_user",
            json={"email": "acceptance+dev@example.com", "is_paid": False},
            timeout=5,
        )
        create_resp.raise_for_status()
        uid = create_resp.json().get("id")
        assert uid, "Dev user did not return an id"

        headless = os.getenv("HEADLESS", "1") != "0"

        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=headless, slow_mo=50)
                context = browser.new_context()
                for name, value in session.cookies.get_dict().items():
                    context.add_cookies([{"name": name, "value": value, "url": BASE}])

                page = context.new_page()
                page.goto(BASE)

                try:
                    page.click("#modal-generate-reels")
                    time.sleep(1)
                except Exception:
                    pass

                gen_response = session.post(
                    f"{BASE}/api/generate",
                    json={"platforms": ["short_video"], "days": 1},
                    timeout=10,
                )
                assert gen_response.status_code in (401, 403), gen_response.text

                payload = {
                    "type": "checkout.session.completed",
                    "data": {
                        "object": {
                            "client_reference_id": uid,
                            "customer": "cus_test",
                            "subscription": "sub_test",
                        }
                    },
                }
                webhook_response = requests.post(f"{BASE}/api/stripe-webhook", json=payload, timeout=5)
                assert webhook_response.status_code == 200

                page.reload()
                page.wait_for_selector("#modal-generate-reels", timeout=5000)
                page.click("#modal-generate-reels")
                page.wait_for_selector(".card", timeout=10000)
                assert page.query_selector_all(".card"), "Expected generated cards after payment"

                quota = int(os.getenv("REELS_QUOTA_MONTHLY", "30"))
                set_generation_usage(uid, quota)
                blocked = session.post(
                    f"{BASE}/api/generate",
                    json={"platforms": ["short_video"], "days": 1},
                    timeout=10,
                )
                assert blocked.status_code == 403, blocked.text
        finally:
            if page is not None:
                try:
                    page.close()
                except Exception:
                    pass
            if context is not None:
                try:
                    context.close()
                except Exception:
                    pass
            if browser is not None:
                try:
                    browser.close()
                except Exception:
                    pass
    except Exception:
        failure_dir = ROOT / "tmp" / "test-outputs" / time.strftime("%Y%m%d-%H%M%S-failure")
        failure_dir.mkdir(parents=True, exist_ok=True)
        if page is not None:
            try:
                page.screenshot(path=str(failure_dir / "failure_screenshot.png"))
                (failure_dir / "failure_page.html").write_text(page.content())
            except Exception:
                pass
        if gen_response is not None:
            (failure_dir / "gen_response.txt").write_text(getattr(gen_response, "text", str(gen_response)))
        if webhook_response is not None:
            (failure_dir / "webhook_response.txt").write_text(getattr(webhook_response, "text", str(webhook_response)))
        (failure_dir / "cookies.json").write_text(json.dumps(session.cookies.get_dict(), indent=2))
        raise
    finally:
        stop_server(proc)


