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
            "matrix": {}
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
            width: 900px;
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
        table {{
            border-collapse: collapse;
            margin-top: 15px;
            margin-bottom: 15px;
        }}
        td, th {{
            border: 1px solid #777;
            padding: 8px;
            text-align: center;
        }}
        .error {{
            color: red;
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
<h3>Задача 27.10</h3>

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
    return page("Задача 27.10", f"""
<h2>Вітаю, {escape(user)}!</h2>

<h3>Задача 27.10</h3>

<p>
Потрібно ввести дві матриці та обчислити їх добуток.
Матриці вводяться на окремих сторінках.
</p>

<p>
Якщо перша матриця має розмір <b>n × m</b>,
а друга — <b>m × k</b>, то результат матиме розмір <b>n × k</b>.
</p>

<a href="/sizes">Перейти до введення розмірів</a><br>
<a href="/logout">Вийти</a>
""")


def sizes_page(error=""):
    error_html = f"<p class='error'>{escape(error)}</p>" if error else ""

    return page("Розміри матриць", f"""
<h2>Задача 27.10</h2>
<h3>Введення розмірів матриць</h3>

{error_html}

<form method="post" action="/sizes">
    <p>
        <label>n — кількість рядків першої матриці:</label><br>
        <input type="number" name="n" min="1">
    </p>
    <p>
        <label>m — кількість стовпців першої матриці і рядків другої:</label><br>
        <input type="number" name="m" min="1">
    </p>
    <p>
        <label>k — кількість стовпців другої матриці:</label><br>
        <input type="number" name="k" min="1">
    </p>
    <button type="submit">Далі</button>
</form>

<a href="/start">Назад</a>
""")


def process_sizes(session, params):
    try:
        n = int(params.get("n", [""])[0])
        m = int(params.get("m", [""])[0])
        k = int(params.get("k", [""])[0])
    except ValueError:
        return "Усі розміри мають бути цілими числами."

    if n <= 0 or m <= 0 or k <= 0:
        return "Розміри матриць мають бути додатними."

    session["matrix"] = {
        "n": n,
        "m": m,
        "k": k,
        "A": None,
        "B": None,
        "C": None
    }

    return ""


def input_table(rows, cols, prefix, values=None):
    html = "<table>"

    for i in range(rows):
        html += "<tr>"

        for j in range(cols):
            key = f"{prefix}_{i}_{j}"
            value = ""

            if values is not None:
                value = escape(values.get(key, [""])[0])

            html += f'<td><input type="text" name="{key}" value="{value}" size="5"></td>'

        html += "</tr>"

    html += "</table>"
    return html


def matrix_a_page(session, error="", old_values=None):
    matrix = session["matrix"]

    if not matrix:
        return page("Помилка", """
<p class="error">Спочатку потрібно ввести розміри матриць.</p>
<a href="/sizes">До введення розмірів</a>
""")

    n = matrix["n"]
    m = matrix["m"]
    error_html = f"<p class='error'>{escape(error)}</p>" if error else ""

    return page("Матриця A", f"""
<h2>Задача 27.10</h2>
<h3>Введення матриці A розміру {n} × {m}</h3>

{error_html}

<form method="post" action="/matrix_a">
    {input_table(n, m, "a", old_values)}
    <button type="submit">Зберегти матрицю A</button>
</form>

<a href="/sizes">Змінити розміри</a>
""")


def matrix_b_page(session, error="", old_values=None):
    matrix = session["matrix"]

    if not matrix or matrix.get("A") is None:
        return page("Помилка", """
<p class="error">Спочатку потрібно ввести матрицю A.</p>
<a href="/sizes">До введення розмірів</a>
""")

    m = matrix["m"]
    k = matrix["k"]
    error_html = f"<p class='error'>{escape(error)}</p>" if error else ""

    return page("Матриця B", f"""
<h2>Задача 27.10</h2>
<h3>Введення матриці B розміру {m} × {k}</h3>

{error_html}

<form method="post" action="/matrix_b">
    {input_table(m, k, "b", old_values)}
    <button type="submit">Обчислити добуток</button>
</form>

<a href="/matrix_a">Повернутися до матриці A</a>
""")


def read_matrix(params, rows, cols, prefix):
    matrix = []

    for i in range(rows):
        row = []

        for j in range(cols):
            key = f"{prefix}_{i}_{j}"
            value = params.get(key, [""])[0].strip()

            if value == "":
                return None, "Усі поля матриці мають бути заповнені."

            try:
                number = float(value)
            except ValueError:
                return None, "Усі елементи матриці мають бути числами."

            row.append(number)

        matrix.append(row)

    return matrix, ""


def multiply(a, b):
    n = len(a)
    m = len(a[0])
    k = len(b[0])

    c = []

    for i in range(n):
        row = []

        for j in range(k):
            s = 0

            for t in range(m):
                s += a[i][t] * b[t][j]

            row.append(s)

        c.append(row)

    return c


def number_text(x):
    if int(x) == x:
        return str(int(x))
    return str(x)


def matrix_html(matrix, name):
    html = f"<h3>Матриця {name}</h3>"
    html += "<table>"

    for row in matrix:
        html += "<tr>"

        for value in row:
            html += f"<td>{escape(number_text(value))}</td>"

        html += "</tr>"

    html += "</table>"
    return html


def result_page(session):
    matrix = session["matrix"]

    if not matrix or matrix.get("C") is None:
        return page("Помилка", """
<p class="error">Результат ще не обчислено.</p>
<a href="/sizes">Почати введення матриць</a>
""")

    a = matrix["A"]
    b = matrix["B"]
    c = matrix["C"]

    return page("Результат", f"""
<h2>Задача 27.10</h2>
<h3>Результат множення матриць</h3>

{matrix_html(a, "A")}
{matrix_html(b, "B")}
{matrix_html(c, "C = A × B")}

<a href="/sizes">Розв’язати ще раз</a><br>
<a href="/start">Назад</a>
""")


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

    if path == "/sizes":
        if method == "POST":
            params = read_post(environ)
            error = process_sizes(session, params)

            if error:
                return send(start_response, sid, sizes_page(error))

            return redirect(start_response, sid, "/matrix_a")

        return send(start_response, sid, sizes_page())

    if path == "/matrix_a":
        if method == "POST":
            params = read_post(environ)
            matrix = session["matrix"]
            a, error = read_matrix(params, matrix["n"], matrix["m"], "a")

            if error:
                return send(start_response, sid, matrix_a_page(session, error, params))

            session["matrix"]["A"] = a
            return redirect(start_response, sid, "/matrix_b")

        return send(start_response, sid, matrix_a_page(session))

    if path == "/matrix_b":
        if method == "POST":
            params = read_post(environ)
            matrix = session["matrix"]
            b, error = read_matrix(params, matrix["m"], matrix["k"], "b")

            if error:
                return send(start_response, sid, matrix_b_page(session, error, params))

            session["matrix"]["B"] = b
            session["matrix"]["C"] = multiply(matrix["A"], b)

            return redirect(start_response, sid, "/result")

        return send(start_response, sid, matrix_b_page(session))

    if path == "/result":
        return send(start_response, sid, result_page(session))

    return send(start_response, sid, page("404", """
<h2>Сторінку не знайдено</h2>
<a href="/start">На головну</a>
"""), "404 Not Found")


if __name__ == "__main__":
    server = make_server("", 8002, app)
    print("Сервер задачі 27.10 запущено: http://localhost:8002")
    server.serve_forever()