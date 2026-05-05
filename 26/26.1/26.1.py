import re
import urllib.request
import urllib.parse
from html.parser import HTMLParser
from datetime import datetime, date

MONTHS = {
    "січня": 1,
    "лютого": 2,
    "березня": 3,
    "квітня": 4,
    "травня": 5,
    "червня": 6,
    "липня": 7,
    "серпня": 8,
    "вересня": 9,
    "жовтня": 10,
    "листопада": 11,
    "грудня": 12,
}


def load_page(city):
    city = city.strip()

    if city.startswith("http://") or city.startswith("https://"):
        urls = [city]
    else:
        urls = [
            "https://sinoptik.ua/" + urllib.parse.quote("погода-" + city),
            "https://sinoptik.ua/pohoda/" + urllib.parse.quote(city),
        ]

    last_error = None

    for url in urls:
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0"}
            )

            with urllib.request.urlopen(request) as response:
                return response.read().decode("utf-8", errors="ignore")

        except Exception as error:
            last_error = error

    raise last_error


def clear_html(text):
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def make_date(day, month_name):
    today = date.today()
    month = MONTHS[month_name]

    result = date(today.year, month, day)

    if result < today:
        result = date(today.year + 1, month, day)

    return result


def take_next_5(items):
    today = date.today()
    result = []

    for item in items:
        if item[0] > today:
            result.append(item)

    return result[:5]


def clean_temperature(value):
    value = value.replace("°", "")
    value = value.replace("+", "")
    value = value.replace("−", "-")
    value = value.replace("–", "-")
    return int(value)


def parse_with_regex(html):
    text = clear_html(html)

    days = r"понеділок|вівторок|середа|четвер|п[’'ʼ]?ятниця|субота|неділя"
    months = "|".join(MONTHS.keys())

    pattern = re.compile(
        rf"({days})\s+(\d{{1,2}})\s+({months})\s+"
        rf"мін\.?\s*([+-−–]?\d+)°?\s+"
        rf"макс\.?\s*([+-−–]?\d+)°?",
        re.IGNORECASE
    )

    forecasts = []

    for found in pattern.findall(text):
        day_number = int(found[1])
        month_name = found[2]
        min_temp = clean_temperature(found[3])
        max_temp = clean_temperature(found[4])

        forecast_date = make_date(day_number, month_name)
        forecasts.append((forecast_date, min_temp, max_temp))

    return take_next_5(forecasts)


class WeatherParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_a = False
        self.current_text = ""
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.in_a = True
            self.current_text = ""

    def handle_data(self, data):
        if self.in_a:
            self.current_text += " " + data.strip()

    def handle_endtag(self, tag):
        if tag == "a" and self.in_a:
            text = " ".join(self.current_text.split())

            if "мін" in text and "макс" in text:
                self.blocks.append(text)

            self.current_text = ""
            self.in_a = False


def find_number_after_word(words, word):
    for i in range(len(words) - 1):
        if words[i].startswith(word):
            return clean_temperature(words[i + 1])

    return None


def parse_one_block(text):
    words = text.split()

    day_number = None
    month_name = None

    for i in range(len(words) - 1):
        if words[i].isdigit() and words[i + 1] in MONTHS:
            day_number = int(words[i])
            month_name = words[i + 1]
            break

    if day_number is None:
        return None

    min_temp = find_number_after_word(words, "мін")
    max_temp = find_number_after_word(words, "макс")

    if min_temp is None or max_temp is None:
        return None

    forecast_date = make_date(day_number, month_name)

    return forecast_date, min_temp, max_temp


def parse_with_htmlparser(html):
    parser = WeatherParser()
    parser.feed(html)

    forecasts = []

    for block in parser.blocks:
        item = parse_one_block(block)

        if item is not None:
            forecasts.append(item)

    return take_next_5(forecasts)


def save_to_excel(filename, city, forecasts):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            content = file.read()
    except FileNotFoundError:
        content = """
<html>
<head>
<meta charset="utf-8">
</head>
<body>
<table border="1">
<tr>
    <th>Дата запису</th>
    <th>Місто</th>
    <th>День 1</th>
    <th>Мін 1</th>
    <th>Макс 1</th>
    <th>День 2</th>
    <th>Мін 2</th>
    <th>Макс 2</th>
    <th>День 3</th>
    <th>Мін 3</th>
    <th>Макс 3</th>
    <th>День 4</th>
    <th>Мін 4</th>
    <th>Макс 4</th>
    <th>День 5</th>
    <th>Мін 5</th>
    <th>Макс 5</th>
</tr>
</table>
</body>
</html>
"""

    row = "<tr>"
    row += f"<td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>"
    row += f"<td>{city}</td>"

    for forecast_date, min_temp, max_temp in forecasts:
        row += f"<td>{forecast_date}</td>"
        row += f"<td>{min_temp}</td>"
        row += f"<td>{max_temp}</td>"

    row += "</tr>\n"

    content = content.replace("</table>", row + "</table>")

    with open(filename, "w", encoding="utf-8") as file:
        file.write(content)


def main():
    city = input("Введіть місто: ")
    method = input("Метод 1 - регулярні вирази, 2 - HTMLParser: ")

    html = load_page(city)

    if method == "1":
        forecasts = parse_with_regex(html)
    else:
        forecasts = parse_with_htmlparser(html)

    if len(forecasts) < 5:
        print("Не вдалося отримати прогноз на 5 днів.")
        return

    save_to_excel("weather.xls", city, forecasts)

    print("Дані збережено у файл weather.xls")

    for forecast_date, min_temp, max_temp in forecasts:
        print(f"{forecast_date}: мін. {min_temp}°C, макс. {max_temp}°C")

if __name__ == "__main__":
    main()