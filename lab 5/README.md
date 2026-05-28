# Лабораторна робота 5  
## Спрощена документно-орієнтована база даних для JSON-документів

Проєкт реалізує невелику документно-орієнтовану базу даних на Python.
Кожен документ зберігається як JSON-сумісний словник і має унікальне поле `id`.

## Реалізовано базовий функціонал

- додавання документа;
- видалення документа за `id` або умовою;
- оновлення документа за `id` або умовою;
- пошук за полями;
- точний збіг;
- числові порівняння `>`, `<`, `>=`, `<=`;
- перевірка існування поля;
- пошук у вкладених полях через крапку, наприклад `address.city`;
- пошук елемента у списку через `contains`;
- агрегації `count`, `sum`, `avg`, `min`, `max`;
- групування `group by`;
- збереження у JSON-файл;
- завантаження з JSON-файлу;
- обробка типових помилок.

## Додатково реалізовано

- сортування результатів пошуку;
- складні умови `AND`, `OR`, `NOT`;
- часткове оновлення вкладених полів;
- індексація окремих полів;
- підтримка кількох колекцій через клас `Database`;
- історія змін документів;
- простий консольний інтерфейс;
- unit-тести.

## Запуск програми

```bash
python json_document_db.py
```

## Запуск тестів

```bash
python -m unittest -v test_json_document_db.py
```

## Приклади команд

```text
add {"id":1,"name":"Ivan","age":21,"group":"MI-11","grades":[90,85,100],"address":{"city":"Kyiv","street":"Shevchenka"},"active":true}
add {"id":2,"name":"Olena","age":19,"group":"MI-12","grades":[75,80],"address":{"city":"Lviv"},"active":false}
add {"id":3,"name":"Petro","age":22,"group":"MI-11","grades":[100,95],"address":{"city":"Kyiv"},"active":true}

find active == true
sort age desc

find address.city == "Kyiv"
sort age

exists address.street
sort name

update 1 address.city "Odesa"

aggregate count
aggregate avg age
aggregate min age
aggregate max age

groupby group

index group
save data.json
load data.json
history
```

Команда `sort` сортує не всі документи колекції, а останні результати команд `find` або `exists`.
Тому перед сортуванням потрібно виконати пошук.

## Приклад складної умови у коді

```python
condition = {
    "and": [
        {"field": "age", "op": ">", "value": 20},
        {"or": [
            {"field": "address.city", "op": "==", "value": "Kyiv"},
            {"field": "grades", "op": "contains", "value": 100}
        ]}
    ]
}

result = collection.find(condition, sort_by="age")
```
