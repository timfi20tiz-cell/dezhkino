"""
Локальный сервер Дежкино: раздача статики (web/) + API товаров и заказов
"""

import http.server
import socketserver
import json
import urllib.request
import urllib.error
import html
import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PORT = 8000
BASE_DIR = os.path.dirname(__file__)
WEB_DIR = os.path.join(BASE_DIR, "web")
DATA_FILE = os.path.join(BASE_DIR, "data", "products.json")

BOT_TOKEN = "8977077034:AAF0N-kUmFkIn717Y4esrS6VEoBD2nKC2uY"
ADMIN_CHAT_ID = "6374158037"
ADMIN_PIN = "3484"


def load_products():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_products(products):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)


class DezhkinoHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_GET(self):
        if self.path == "/api/products":
            products = load_products()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(json.dumps(products, ensure_ascii=False).encode("utf-8"))
        else:
            super().do_GET()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"

        # 1. Авторизация админки по PIN
        if self.path == "/api/admin/login":
            try:
                data = json.loads(raw_body)
                pin = str(data.get("pin", "")).strip()
                if pin == ADMIN_PIN:
                    self.send_json_response(200, {"ok": True, "token": "session_admin_dezhkino"})
                else:
                    self.send_json_response(401, {"ok": False, "error": "Неверный PIN-код"})
            except Exception as e:
                self.send_json_response(400, {"ok": False, "error": str(e)})

        # 2. Обновление списка товаров (Требует строгой проверки заголовка PIN)
        elif self.path == "/api/products":
            pin_header = self.headers.get("X-Admin-PIN", "").strip()
            if pin_header != ADMIN_PIN:
                self.send_json_response(401, {"ok": False, "error": "Доступ запрещен: требуется PIN администратора"})
                return

            try:
                data = json.loads(raw_body)
                if isinstance(data, list):
                    save_products(data)
                    self.send_json_response(200, {"ok": True, "products": data})
                elif isinstance(data, dict):
                    products = load_products()
                    prod_id = data.get("id")
                    found = False
                    for idx, p in enumerate(products):
                        if p["id"] == prod_id:
                            products[idx].update(data)
                            found = True
                            break
                    if not found:
                        products.append(data)
                    save_products(products)
                    self.send_json_response(200, {"ok": True, "products": products})
            except Exception as e:
                self.send_json_response(500, {"ok": False, "error": str(e)})

        # 3. Отправка заказа в Telegram
        elif self.path == "/api/order":
            try:
                data = json.loads(raw_body)
                client = data.get("client", {})
                items = data.get("items", [])
                total = data.get("total", 0)

                # Безопасное экранирование всех пользовательских полей от HTML/Markdown инъекций
                name = html.escape(str(client.get("name", "Не указано")))
                phone = html.escape(str(client.get("phone", "Не указано")))
                address = html.escape(str(client.get("address", "Не указано")))
                comment = html.escape(str(client.get("comment", "")))

                items_text = "\n".join([f"• {html.escape(i['name'])} ({i['qty']} шт.) = {i['subtotal']} ₽" for i in items])
                comment_block = f"\n💬 <b>Пожелания:</b> {comment}" if comment else ""

                tg_message = (
                    "🔔 <b>НОВЫЙ ЗАКАЗ ИЗ ДЕЖКИНО!</b>\n\n"
                    f"👤 <b>Покупатель:</b> {name}\n"
                    f"📞 <b>Телефон:</b> {phone}\n"
                    f"📍 <b>Адрес / доставка:</b> {address}"
                    f"{comment_block}\n\n"
                    f"🛒 <b>Состав заказа:</b>\n{items_text}\n\n"
                    f"💰 <b>Итого (ориентир):</b> ~{total} ₽\n"
                    "<i>⚖️ Точный вес и расчет тушек/мяса при взвешивании</i>"
                )

                req_data = json.dumps({
                    "chat_id": ADMIN_CHAT_ID,
                    "text": tg_message,
                    "parse_mode": "HTML"
                }).encode("utf-8")

                req = urllib.request.Request(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    data=req_data,
                    headers={"Content-Type": "application/json"}
                )

                with urllib.request.urlopen(req) as resp:
                    print(f"[OK] Заказ безопасно отправлен в Telegram: {name}")

                self.send_json_response(200, {"ok": True})

            except Exception as e:
                print(f"[!] Ошибка отправки заказа: {e}")
                self.send_json_response(500, {"ok": False, "error": str(e)})

        else:
            self.send_error(404, "Not Found")

    def send_json_response(self, code, payload):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    with ReusableTCPServer(("", PORT), DezhkinoHandler) as httpd:
        print(f"[OK] Веб-сервер Дежкино с API и Админкой запущен: http://localhost:{PORT}")
        httpd.serve_forever()
