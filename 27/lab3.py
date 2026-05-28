from wsgiref.simple_server import make_server
from urllib.parse import parse_qs
from http.cookies import SimpleCookie
from html import escape
import uuid

USERS = {"student": "1234", "admin": "admin"}
SESSIONS = {}


def new_session():
    return {
        "user": None,
        "task_27_4": {"numbers": [], "previous": None, "changes": 0, "finished": False},
        "task_27_10": {"n": None, "m": None, "k": None, "A": None, "B": None, "C": None},
    }


def get_session(environ):
    cookies = SimpleCookie(environ.get("HTTP_COOKIE", ""))
    sid = cookies["sid"].value if "sid" in cookies else None
    if sid not in SESSIONS:
        sid = str(uuid.uuid4())
        SESSIONS[sid] = new_session()
    return sid, SESSIONS[sid]


def read_post(environ):
    size = int(environ.get("CONTENT_LENGTH", 0) or 0)
    body = environ["wsgi.input"].read(size).decode("utf-8")
    return parse_qs(body)


def send(start_response, sid, body, status="200 OK"):
    start_response(status, [
        ("Content-Type", "text/html; charset=utf-8"),
        ("Set-Cookie", f"sid={sid}; Path=/"),
    ])
    return [body.encode("utf-8")]


def redirect(start_response, sid, location):
    start_response("302 Found", [
        ("Location", location),
        ("Set-Cookie", f"sid={sid}; Path=/"),
    ])
    return [b""]


def page(title, content):
    return f"""
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; width: 900px; margin: 30px auto; background: #f4f4f4; }}
        .box {{ background: white; padding: 25px; border: 1px solid #ccc; border-radius: 8px; }}
        input {{ padding: 7px; margin: 4px; }}
        button, .button {{ display: inline-block; padding: 8px 14px; margin: 5px 5px 5px 0; border: 1px solid #777; border-radius: 5px; background: #eee; color: black; text-decoration: none; cursor: pointer; }}
        table {{ border-collapse: collapse; margin-top: 15px; margin-bottom: 15px; }}
        td, th {{ border: 1px solid #777; padding: 8px; text-align: center; }}
        .error {{ color: red; font-weight: bold; }}
        .ok {{ color: green; font-weight: bold; }}
        .task-card {{ border: 1px solid #ccc; border-radius: 8px; padding: 15px; margin: 15px 0; background: #fafafa; }}
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
<h2>Лабораторна робота №3</h2>
<h3>Задачі 27.4 та 27.10</h3>
{error_html}
<form method="post" action="/login">
    <p><label>Логін:</label><br><input type="text" name="login"></p>
    <p><label>Пароль:</label><br><input type="password" name="password"></p>
    <button type="submit">Увійти</button>
</form>
<p>Логін: <b>student</b>, пароль: <b>1234</b></p>
""")


def task_choice_page(user):
    return page("Вибір задачі", f"""
<h2>Лабораторна робота №3</h2>
<h3>Вітаю, {escape(user)}!</h3>
<p>Оберіть задачу, яку потрібно виконати.</p>
<div class="task-card">
    <h3>Задача 27.4</h3>
    <p>Задана непорожня послідовність ненульових цілих чисел, за якою йде 0. Потрібно визначити кількість змін знаку.</p>
    <a class="button" href="/27_4">Перейти до задачі 27.4</a>
</div>
<div class="task-card">
    <h3>Задача 27.10</h3>
    <p>Потрібно ввести дві матриці та обчислити їх добуток.</p>
    <a class="button" href="/27_10">Перейти до задачі 27.10</a>
</div>
<a href="/logout">Вийти</a>
""")


def reset_27_4(state):
    state["numbers"] = []
    state["previous"] = None
    state["changes"] = 0
    state["finished"] = False


def task_27_4_page(session, error=""):
    state = session["task_27_4"]
    numbers_text = ", ".join(str(x) for x in state["numbers"]) or "ще не введено"
    error_html = f"<p class='error'>{escape(error)}</p>" if error else ""
    if state["finished"]:
        result_html = f"<p class='ok'>Введення завершено.</p><p><b>Кількість змін знаку:</b> {state['changes']}</p>"
    else:
        result_html = f"<p><b>Поточна кількість змін знаку:</b> {state['changes']}</p>"

    return page("Задача 27.4", f"""
<h2>Задача 27.4</h2>
<p>Вводьте елементи послідовності по одному. Нуль завершує введення.</p>
<p>Наприклад, у послідовності <b>1, -34, 8, 14, -5, 0</b> знак змінюється <b>3</b> рази.</p>
{error_html}
<form method="post" action="/27_4">
    <input type="text" name="number" autofocus>
    <button type="submit" name="action" value="add">Обробити</button>
    <button type="submit" name="action" value="reset">Почати заново</button>
</form>
<p><b>Введені елементи:</b> {escape(numbers_text)}</p>
{result_html}
<a href="/start">До вибору задачі</a>
""")


def process_task_27_4(session, params):
    state = session["task_27_4"]
    action = params.get("action", ["add"])[0]
    if action == "reset":
        reset_27_4(state)
        return ""
    if state["finished"]:
        return "Послідовність уже завершено. Натисніть «Почати заново»."
    value = params.get("number", [""])[0].strip()
    if value == "":
        return "Поле не може бути порожнім."
    try:
        number = int(value)
    except ValueError:
        return "Потрібно ввести ціле число."
    if number == 0:
        if not state["numbers"]:
            return "Послідовність має бути непорожньою."
        state["finished"] = True
        return ""
    previous = state["previous"]
    if previous is not None and ((previous > 0 and number < 0) or (previous < 0 and number > 0)):
        state["changes"] += 1
    state["numbers"].append(number)
    state["previous"] = number
    return ""


def task_27_10_start_page():
    return page("Задача 27.10", """
<h2>Задача 27.10</h2>
<p>Потрібно ввести дві матриці та обчислити їх добуток.</p>
<p>Якщо перша матриця має розмір <b>n × m</b>, а друга — <b>m × k</b>, то результат матиме розмір <b>n × k</b>.</p>
<a class="button" href="/27_10/sizes">Перейти до введення розмірів</a><br>
<a href="/start">До вибору задачі</a>
""")


def sizes_page(error=""):
    error_html = f"<p class='error'>{escape(error)}</p>" if error else ""
    return page("Розміри матриць", f"""
<h2>Задача 27.10</h2>
<h3>Введення розмірів матриць</h3>
{error_html}
<form method="post" action="/27_10/sizes">
    <p><label>n — кількість рядків першої матриці:</label><br><input type="number" name="n" min="1"></p>
    <p><label>m — кількість стовпців першої матриці і рядків другої:</label><br><input type="number" name="m" min="1"></p>
    <p><label>k — кількість стовпців другої матриці:</label><br><input type="number" name="k" min="1"></p>
    <button type="submit">Далі</button>
</form>
<a href="/27_10">Назад</a>
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
    session["task_27_10"] = {"n": n, "m": m, "k": k, "A": None, "B": None, "C": None}
    return ""


def input_table(rows, cols, prefix, values=None):
    html = "<table>"
    for i in range(rows):
        html += "<tr>"
        for j in range(cols):
            key = f"{prefix}_{i}_{j}"
            value = escape(values.get(key, [""])[0]) if values else ""
            html += f'<td><input type="text" name="{key}" value="{value}" size="5"></td>'
        html += "</tr>"
    html += "</table>"
    return html


def matrix_a_page(session, error="", old_values=None):
    matrix = session["task_27_10"]
    if not matrix or matrix.get("n") is None:
        return page("Помилка", "<p class='error'>Спочатку потрібно ввести розміри матриць.</p><a href='/27_10/sizes'>До введення розмірів</a>")
    error_html = f"<p class='error'>{escape(error)}</p>" if error else ""
    return page("Матриця A", f"""
<h2>Задача 27.10</h2>
<h3>Введення матриці A розміру {matrix['n']} × {matrix['m']}</h3>
{error_html}
<form method="post" action="/27_10/matrix_a">
    {input_table(matrix['n'], matrix['m'], 'a', old_values)}
    <button type="submit">Зберегти матрицю A</button>
</form>
<a href="/27_10/sizes">Змінити розміри</a>
""")


def matrix_b_page(session, error="", old_values=None):
    matrix = session["task_27_10"]
    if not matrix or matrix.get("A") is None:
        return page("Помилка", "<p class='error'>Спочатку потрібно ввести матрицю A.</p><a href='/27_10/sizes'>До введення розмірів</a>")
    error_html = f"<p class='error'>{escape(error)}</p>" if error else ""
    return page("Матриця B", f"""
<h2>Задача 27.10</h2>
<h3>Введення матриці B розміру {matrix['m']} × {matrix['k']}</h3>
{error_html}
<form method="post" action="/27_10/matrix_b">
    {input_table(matrix['m'], matrix['k'], 'b', old_values)}
    <button type="submit">Обчислити добуток</button>
</form>
<a href="/27_10/matrix_a">Повернутися до матриці A</a>
""")


def read_matrix(params, rows, cols, prefix):
    matrix = []
    for i in range(rows):
        row = []
        for j in range(cols):
            value = params.get(f"{prefix}_{i}_{j}", [""])[0].strip()
            if value == "":
                return None, "Усі поля матриці мають бути заповнені."
            try:
                row.append(float(value))
            except ValueError:
                return None, "Усі елементи матриці мають бути числами."
        matrix.append(row)
    return matrix, ""


def multiply(a, b):
    return [[sum(a[i][t] * b[t][j] for t in range(len(a[0]))) for j in range(len(b[0]))] for i in range(len(a))]


def number_text(x):
    return str(int(x)) if int(x) == x else str(x)


def matrix_html(matrix, name):
    html = f"<h3>Матриця {name}</h3><table>"
    for row in matrix:
        html += "<tr>" + "".join(f"<td>{escape(number_text(value))}</td>" for value in row) + "</tr>"
    html += "</table>"
    return html


def result_page(session):
    matrix = session["task_27_10"]
    if not matrix or matrix.get("C") is None:
        return page("Помилка", "<p class='error'>Результат ще не обчислено.</p><a href='/27_10/sizes'>Почати введення матриць</a>")
    return page("Результат", f"""
<h2>Задача 27.10</h2>
<h3>Результат множення матриць</h3>
{matrix_html(matrix['A'], 'A')}
{matrix_html(matrix['B'], 'B')}
{matrix_html(matrix['C'], 'C = A × B')}
<a href="/27_10/sizes">Розв’язати ще раз</a><br>
<a href="/start">До вибору задачі</a>
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
        return send(start_response, sid, task_choice_page(session["user"]))
    if path == "/27_4":
        if method == "POST":
            params = read_post(environ)
            error = process_task_27_4(session, params)
            return send(start_response, sid, task_27_4_page(session, error))
        return send(start_response, sid, task_27_4_page(session))
    if path == "/27_10":
        return send(start_response, sid, task_27_10_start_page())
    if path == "/27_10/sizes":
        if method == "POST":
            params = read_post(environ)
            error = process_sizes(session, params)
            if error:
                return send(start_response, sid, sizes_page(error))
            return redirect(start_response, sid, "/27_10/matrix_a")
        return send(start_response, sid, sizes_page())
    if path == "/27_10/matrix_a":
        if method == "POST":
            params = read_post(environ)
            matrix = session["task_27_10"]
            a, error = read_matrix(params, matrix["n"], matrix["m"], "a")
            if error:
                return send(start_response, sid, matrix_a_page(session, error, params))
            matrix["A"] = a
            return redirect(start_response, sid, "/27_10/matrix_b")
        return send(start_response, sid, matrix_a_page(session))
    if path == "/27_10/matrix_b":
        if method == "POST":
            params = read_post(environ)
            matrix = session["task_27_10"]
            b, error = read_matrix(params, matrix["m"], matrix["k"], "b")
            if error:
                return send(start_response, sid, matrix_b_page(session, error, params))
            matrix["B"] = b
            matrix["C"] = multiply(matrix["A"], b)
            return redirect(start_response, sid, "/27_10/result")
        return send(start_response, sid, matrix_b_page(session))
    if path == "/27_10/result":
        return send(start_response, sid, result_page(session))
    return send(start_response, sid, page("404", "<h2>Сторінку не знайдено</h2><a href='/start'>На головну</a>"), "404 Not Found")


if __name__ == "__main__":
    server = make_server("", 8001, app)
    print("Сервер лабораторної №3 запущено: http://localhost:8001")
    server.serve_forever()
