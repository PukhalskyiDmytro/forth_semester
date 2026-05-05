from wsgiref.simple_server import make_server
from urllib.parse import parse_qs
from http.cookies import SimpleCookie
from html import escape
import uuid


USERS = {
    "student": "1234",
    "admin": "admin"
}

SESSIONS = {}


def get_session(environ):
    cookies = SimpleCookie(environ.get("HTTP_COOKIE", ""))
    sid = None

    if "sid" in cookies:
        sid = cookies["sid"].value

    if sid not in SESSIONS:
        sid = str(uuid.uuid4())
        SESSIONS[sid] = {
            "user": None,
            "numbers": [],
            "previous": None,
            "changes": 0,
            "finished": False
        }

    return sid, SESSIONS[sid]


def read_post(environ):
    size = int(environ.get("CONTENT_LENGTH", 0) or 0)
    body = environ["wsgi.input"].read(size).decode("utf-8")
    return parse_qs(body)


def send(start_response, sid, body, status="200 OK"):
    headers = [
        ("Content-Type", "text/html; charset=utf-8"),
        ("Set-Cookie", f"sid={sid}; Path=/")
    ]
    start_response(status, headers)
    return [body.encode("utf-8")]


def redirect(start_response, sid, location):
    headers = [
        ("Location", location),
        ("Set-Cookie", f"sid={sid}; Path=/")
    ]
    start_response("302 Found", headers)
    return [b""]


def page(title, content):
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            width: 800px;
            margin: 30px auto;
            background: #f4f4f4;
        }}
        .box {{
            background: white;
            padding: 25px;
            border: 1px solid #ccc;
            border-radius: 8px;
        }}
        input {{
            padding: 7px;
            margin: 4px;
        }}
        button {{
            padding: 8px 14px;
            margin: 5px;
        }}
        .error {{
            color: red;
            font-weight: bold;
        }}
        .ok {{
            color: green;
            font-weight: bold;
        }}
    </style>
</head>
<body>
<div class="box">
{content}
</div>
</body>
</html>
"""


def login_page(error=""):
    error_html = f"<p class='error'>{escape(error)}</p>" if error else ""

    return page("Вхід", f"""
<h2>Лабораторна робота №4</h2>
<h3>Задача 27.4</h3>

{error_html}

<form method="post" action="/login">
    <p>
        <label>Логін:</label><br>
        <input type="text" name="login">
    </p>
    <p>
        <label>Пароль:</label><br>
        <input type="password" name="password">
    </p>
    <button type="submit">Увійти</button>
</form>

<p>Логін: <b>student</b>, пароль: <b>1234</b></p>
""")


def start_page(user):
    return page("Задача 27.4", f"""
<h2>Вітаю, {escape(user)}!</h2>

<h3>Задача 27.4</h3>

<p>
Задана непорожня послідовність ненульових цілих чисел, за якою йде 0.
Потрібно визначити кількість змін знаку в цій послідовності.
</p>

<p>
Наприклад, у послідовності <b>1, -34, 8, 14, -5, 0</b>
знак змінюється <b>3</b> рази.
</p>

<a href="/task">Перейти до введення послідовності</a><br>
<a href="/logout">Вийти</a>
""")


def task_page(session, error=""):
    numbers_text = ", ".join(str(x) for x in session["numbers"])

    if numbers_text == "":
        numbers_text = "ще не введено"

    error_html = f"<p class='error'>{escape(error)}</p>" if error else ""

    if session["finished"]:
        result_html = f"""
<p class="ok">Введення завершено.</p>
<p><b>Кількість змін знаку:</b> {session["changes"]}</p>
"""
    else:
        result_html = f"""
<p><b>Поточна кількість змін знаку:</b> {session["changes"]}</p>
"""

    return page("Введення послідовності", f"""
<h2>Задача 27.4</h2>

<p>
Вводьте елементи послідовності по одному.
Нуль завершує введення.
</p>

{error_html}

<form method="post" action="/task">
    <input type="text" name="number" autofocus>
    <button type="submit" name="action" value="add">Обробити</button>
    <button type="submit" name="action" value="reset">Почати заново</button>
</form>

<p><b>Введені елементи:</b> {escape(numbers_text)}</p>

{result_html}

<a href="/start">Назад</a>
""")


def process_number(session, params):
    action = params.get("action", ["add"])[0]

    if action == "reset":
        session["numbers"] = []
        session["previous"] = None
        session["changes"] = 0
        session["finished"] = False
        return ""

    if session["finished"]:
        return "Послідовність уже завершено. Натисніть «Почати заново»."

    value = params.get("number", [""])[0].strip()

    if value == "":
        return "Поле не може бути порожнім."

    try:
        number = int(value)
    except ValueError:
        return "Потрібно ввести ціле число."

    if number == 0:
        if len(session["numbers"]) == 0:
            return "Послідовність має бути непорожньою."

        session["finished"] = True
        return ""

    previous = session["previous"]

    if previous is not None:
        if previous > 0 and number < 0:
            session["changes"] += 1
        elif previous < 0 and number > 0:
            session["changes"] += 1

    session["numbers"].append(number)
    session["previous"] = number

    return ""


def app(environ, start_response):
    sid, session = get_session(environ)
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")

    if path == "/":
        return send(start_response, sid, login_page())

    if path == "/login" and method == "POST":
        params = read_post(environ)
        login = params.get("login", [""])[0]
        password = params.get("password", [""])[0]

        if login in USERS and USERS[login] == password:
            session["user"] = login
            return redirect(start_response, sid, "/start")

        return send(start_response, sid, login_page("Неправильний логін або пароль."))

    if path == "/logout":
        session["user"] = None
        return redirect(start_response, sid, "/")

    if session["user"] is None:
        return redirect(start_response, sid, "/")

    if path == "/start":
        return send(start_response, sid, start_page(session["user"]))

    if path == "/task":
        if method == "POST":
            params = read_post(environ)
            error = process_number(session, params)
            return send(start_response, sid, task_page(session, error))

        return send(start_response, sid, task_page(session))

    return send(start_response, sid, page("404", """
<h2>Сторінку не знайдено</h2>
<a href="/start">На головну</a>
"""), "404 Not Found")


if __name__ == "__main__":
    server = make_server("", 8001, app)
    print("Сервер задачі 27.4 запущено: http://localhost:8001")
    server.serve_forever()