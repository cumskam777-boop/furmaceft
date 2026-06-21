# -*- coding: utf-8 -*-
"""
Генератор проекта Flask: Фурмацевт.ru
Исправлено: import pickle уже добавлен в app.py.
Запуск: py -3 create_farmacevt_lab3.py
"""
from pathlib import Path
import shutil
import textwrap
import zipfile

PROJECT = Path("farmacevt_lab3")

FILES = {}

FILES["requirements.txt"] = "Flask==3.0.3\n"

FILES["app.py"] = r'''
# -*- coding: utf-8 -*-
import os
import pickle
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = "farmacevt-demo-secret-key"
DATA_FILE = "farmacevt_data.dat"

PRODUCTS = [
    {"id": 1, "name": "Перекись водорода 3% раствор для местного наружного применения флакон", "price": 78, "pic": "💧"},
    {"id": 2, "name": "Пластырь бактерицидный Верофарм тканевый 20 штук набор", "price": 148, "pic": "🩹"},
    {"id": 3, "name": "Парацетамол детский суспензия клубничная 120мг/5мл 100г", "price": 76, "pic": "🧴"},
    {"id": 4, "name": "Ибупрофен ВП суспензия для приема внутрь для детей 100мг/5мл 100мл", "price": 112, "pic": "🍶"},
    {"id": 5, "name": "Нурофен для детей суспензия клубничная 200 мл", "price": 278, "pic": "💊"},
    {"id": 6, "name": "Детский крем под подгузник с тальком 50 мл Мапсики", "price": 88, "pic": "🧴"},
    {"id": 7, "name": "Риностейн спрей назальный 10 мл", "price": 240, "pic": "🌡️"},
    {"id": 8, "name": "Гутталакс капли 7.5мг/мл 30 мл", "price": 565, "pic": "🧪"},
    {"id": 9, "name": "Тест-полоски к глюкометру CONTOUR PLUS 50 шт", "price": 659, "pic": "📦"},
    {"id": 10, "name": "Тест на беременность CLEARBLUE цифровой 1 шт", "price": 545, "pic": "📋"},
    {"id": 11, "name": "PASTILAB Пастила медовая Малиновая с семенами льна 70 г", "price": 119, "pic": "🍓"},
    {"id": 12, "name": "Олеос масло пищевое грецкого ореха 200мл", "price": 471, "pic": "🧉"},
]

class PickleStorage:
    def __init__(self, filename=DATA_FILE):
        self.filename = filename
    def load(self):
        if not os.path.exists(self.filename):
            return None
        try:
            with open(self.filename, "rb") as f:
                return pickle.load(f)
        except Exception:
            return None
    def save(self, data):
        with open(self.filename, "wb") as f:
            pickle.dump(data, f)

storage = PickleStorage()

def default_data():
    return {
        "users": {
            "lidiababushka@gmail.com": {
                "login": "Лидия Николаевна",
                "email": "lidiababushka@gmail.com",
                "password": "12345678",
                "cart": {},
                "favorites": [1,2,3,4,5,6,7,8],
                "orders": [],
                "cards": [{"num": "1234", "date": "12/28", "country": "Россия"}],
                "bonus": 1140
            }
        }
    }

def db():
    data = storage.load()
    if data is None:
        data = default_data()
        storage.save(data)
    return data

def save(data):
    storage.save(data)

def current_user():
    email = session.get("user")
    if not email:
        return None
    return db()["users"].get(email)

def require_login():
    if not current_user():
        return redirect(url_for("login"))
    return None

def product(pid):
    return next((p for p in PRODUCTS if p["id"] == int(pid)), None)

@app.context_processor
def inject():
    u = current_user()
    cart_count = sum(u.get("cart", {}).values()) if u else 0
    return dict(user=u, cart_count=cart_count, products=PRODUCTS)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/catalog")
def catalog():
    q = request.args.get("q", "").lower().strip()
    items = [p for p in PRODUCTS if q in p["name"].lower()] if q else PRODUCTS
    return render_template("catalog.html", items=items)

@app.route("/add/<int:pid>")
def add(pid):
    r = require_login()
    if r: return r
    data = db(); u = data["users"][session["user"]]
    cart = u.setdefault("cart", {})
    cart[str(pid)] = cart.get(str(pid), 0) + 1
    save(data)
    return redirect(request.referrer or url_for("catalog"))

@app.route("/minus/<int:pid>")
def minus(pid):
    r = require_login()
    if r: return r
    data = db(); u = data["users"][session["user"]]
    cart = u.setdefault("cart", {})
    if str(pid) in cart:
        cart[str(pid)] -= 1
        if cart[str(pid)] <= 0:
            del cart[str(pid)]
    save(data)
    return redirect(request.referrer or url_for("catalog"))

@app.route("/fav/<int:pid>")
def fav(pid):
    r = require_login()
    if r: return r
    data = db(); u = data["users"][session["user"]]
    favs = u.setdefault("favorites", [])
    if pid in favs: favs.remove(pid)
    else: favs.append(pid)
    save(data)
    return redirect(request.referrer or url_for("catalog"))

@app.route("/cart")
def cart():
    r = require_login()
    if r: return r
    u = current_user()
    items = []
    total = 0
    for pid, qty in u.get("cart", {}).items():
        p = product(pid)
        if p:
            items.append((p, qty, p["price"] * qty))
            total += p["price"] * qty
    return render_template("cart.html", items=items, total=total)

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    r = require_login()
    if r: return r
    data = db(); u = data["users"][session["user"]]
    if request.method == "POST":
        order_items = []
        total = 0
        for pid, qty in u.get("cart", {}).items():
            p = product(pid)
            if p:
                order_items.append({"id": p["id"], "name": p["name"], "price": p["price"], "qty": qty})
                total += p["price"] * qty
        if order_items:
            u.setdefault("orders", []).append({
                "date": datetime.now().strftime("%d.%m.%Y"),
                "items": order_items,
                "total": total,
                "address": f"{request.form.get('city','')}, {request.form.get('street','')}, {request.form.get('house','')}"
            })
            u["bonus"] = u.get("bonus", 0) + int(total * 0.05)
            u["cart"] = {}
            save(data)
        return redirect(url_for("orders"))
    total = sum(product(pid)["price"] * qty for pid, qty in u.get("cart", {}).items() if product(pid))
    return render_template("checkout.html", total=total)

@app.route("/profile")
def profile():
    r = require_login()
    if r: return r
    u = current_user()
    return render_template("profile.html", orders_count=len(u.get("orders", [])), fav_count=len(u.get("favorites", [])))

@app.route("/orders")
def orders():
    r = require_login()
    if r: return r
    return render_template("orders.html", orders=current_user().get("orders", []))

@app.route("/delete_order/<int:i>")
def delete_order(i):
    r = require_login()
    if r: return r
    data = db(); orders = data["users"][session["user"]].get("orders", [])
    if 0 <= i < len(orders):
        orders.pop(i)
        save(data)
    return redirect(url_for("orders"))

@app.route("/favorites")
def favorites():
    r = require_login()
    if r: return r
    favs = current_user().get("favorites", [])
    items = [p for p in PRODUCTS if p["id"] in favs]
    return render_template("favorites.html", items=items)

@app.route("/settings", methods=["GET", "POST"])
def settings():
    r = require_login()
    if r: return r
    data = db(); u = data["users"][session["user"]]
    if request.method == "POST":
        u["login"] = request.form.get("login", u["login"])
        save(data)
        return redirect(url_for("settings"))
    return render_template("settings.html")

@app.route("/add_card", methods=["GET", "POST"])
def add_card():
    r = require_login()
    if r: return r
    data = db(); u = data["users"][session["user"]]
    if request.method == "POST":
        num = request.form.get("num", "0000")[-4:]
        u.setdefault("cards", []).append({"num": num, "date": request.form.get("date", "12/28"), "country": "Россия"})
        save(data)
        return redirect(url_for("settings"))
    return render_template("add_card.html")

@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    r = require_login()
    if r: return r
    data = db(); u = data["users"][session["user"]]
    if request.method == "POST":
        p1 = request.form.get("p1", "")
        p2 = request.form.get("p2", "")
        if len(p1) >= 8 and p1 == p2:
            u["password"] = p1
            save(data)
            return redirect(url_for("settings"))
        flash("Пароль должен быть не менее 8 символов и совпадать")
    return render_template("change_password.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = db()
        login_or_email = request.form.get("login", "").strip()
        password = request.form.get("password", "")
        for email, u in data["users"].items():
            if (email == login_or_email or u["login"] == login_or_email) and u["password"] == password:
                session["user"] = email
                return redirect(url_for("profile"))
        flash("Неверный логин или пароль")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        data = db()
        login = request.form.get("login", "Пользователь")
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        if email and len(password) >= 8:
            data["users"][email] = {"login": login, "email": email, "password": password, "cart": {}, "favorites": [], "orders": [], "cards": [], "bonus": 0}
            save(data)
            session["user"] = email
            return redirect(url_for("profile"))
        flash("Введите почту и пароль минимум 8 символов")
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
'''

FILES["templates/base.html"] = r'''
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Фурмацевт.ru</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
{% block body %}{% endblock %}
</body>
</html>
'''

FILES["templates/header.html"] = r'''
<header class="topbar">
  <div class="phone">8 915 985 14 26</div>
  <a class="logo" href="{{ url_for('home') }}">Фурмацевт<span>.ru</span></a>
  <nav>
    <a href="{{ url_for('home') }}">Главная</a>
    <a href="{{ url_for('catalog') }}">Каталог</a>
    <a href="{{ url_for('about') }}">О нас</a>
  </nav>
  <form class="search" action="{{ url_for('catalog') }}"><span>⌕</span><input name="q" placeholder="Введите название товара"></form>
  <div class="icons">
    <a href="#">▣<small>Поддержка</small></a>
    <a href="{{ url_for('cart') }}">🛒<small>Корзина</small></a>
    <a href="{{ url_for('favorites') }}">♥<small>Избранное</small></a>
    {% if user %}<a href="{{ url_for('profile') }}">♙<small>Профиль</small></a>{% else %}<a href="{{ url_for('login') }}">♙<small>Войти</small></a>{% endif %}
  </div>
</header>
'''

FILES["templates/sidebar.html"] = r'''
<aside class="side">
  <a class="logo side-logo" href="{{ url_for('home') }}">Фурмацевт<span>.ru</span></a>
  <nav class="side-nav">
    <a class="{{ 'active' if active=='profile' else '' }}" href="{{ url_for('profile') }}">Профиль</a>
    <a class="{{ 'active' if active=='orders' else '' }}" href="{{ url_for('orders') }}">Заказы</a>
    <a class="{{ 'active' if active=='favorites' else '' }}" href="{{ url_for('favorites') }}">Избранное</a>
    <a class="{{ 'active' if active=='settings' else '' }}" href="{{ url_for('settings') }}">Настройки</a>
  </nav>
  <div class="doctor small-doc">🧑‍⚕️</div>
</aside>
'''

FILES["templates/auth_base.html"] = r'''
{% extends "base.html" %}{% block body %}
<main class="auth-page">
  <section class="modal-card">
    <a class="close" href="{{ url_for('home') }}">⊗</a>
    <div class="logo auth-logo">Фурмацевт<span>.ru</span></div>
    {% with messages = get_flashed_messages() %}{% if messages %}<div class="msg">{{ messages[0] }}</div>{% endif %}{% endwith %}
    {% block auth %}{% endblock %}
    <div class="doctor auth-doc">🧑‍⚕️</div>
  </section>
</main>
{% endblock %}
'''

FILES["templates/login.html"] = r'''
{% extends "auth_base.html" %}{% block auth %}
<h1>Вход в аккаунт</h1>
<p class="muted">Войдите аккаунт, чтобы пользоваться<br>преимуществами</p>
<form method="post" class="auth-form">
  <label>♙ <input name="login" placeholder="Логин"></label>
  <label>▣ <input name="password" type="password" placeholder="Пароль"></label>
  <button>Войти</button>
</form>
<p>Нет аккаунта? <a href="{{ url_for('register') }}">Зарегистрироваться</a></p>
{% endblock %}
'''

FILES["templates/register.html"] = r'''
{% extends "auth_base.html" %}{% block auth %}
<h1>Регистрация</h1>
<p class="muted">Создайте аккаунт, чтобы пользоваться<br>преимуществами</p>
<form method="post" class="auth-form">
  <label>♙ <input name="login" placeholder="Логин"></label>
  <label>✉ <input name="email" placeholder="Почта"></label>
  <label>▣ <input name="password" type="password" placeholder="Пароль"></label>
  <button>Зарегистрироваться</button>
</form>
<p>Уже есть аккаунт? <a href="{{ url_for('login') }}">Войти</a></p>
{% endblock %}
'''

FILES["templates/home.html"] = r'''
{% extends "base.html" %}{% block body %}
{% include "header.html" %}
<section class="hero">
  <div>
    <h1>Все хотят быть здоровыми !</h1>
    <h3>Это даже хорошо, что пока нам плохо!</h3>
  </div>
  <div class="doctor hero-doc">🧑‍⚕️</div>
</section>
<section class="pill-banner">
  <a class="big-btn" href="{{ url_for('catalog') }}">Перейти в каталог</a>
</section>
<section class="promo">
  <div>
    <h1>Лекарста с доставкой<br><br>Быстро и легко !</h1>
    <a class="blue-btn" href="{{ url_for('catalog') }}">Перейти в каталог</a>
    <a class="red-btn" href="{{ url_for('checkout') }}">Оформить заказ</a>
    <h2>Для ВАС от НАС !</h2>
    <div class="family">👵 👧 📱</div>
  </div>
  <div class="bubble">Сколько Вам лет,<br>столько <b>%</b> скидка<br>на первый заказ</div>
</section>
{% endblock %}
'''

FILES["templates/catalog.html"] = r'''
{% extends "base.html" %}{% block body %}
{% include "header.html" %}
<main class="catalog-wrap">
  <h1>Наши товары для Вашей семьи !</h1>
  <div class="grid">
  {% for p in items %}
    <article class="product">
      <div class="prod-img">{{ p.pic }}</div>
      <p class="prod-name">{{ p.name }}</p>
      <p class="price">Цена:<br><b>{{ p.price }} ₽</b></p>
      {% if user and user.cart.get(p.id|string, 0) > 0 %}
        <div class="qty"><a href="{{ url_for('minus', pid=p.id) }}">-</a><span>{{ user.cart.get(p.id|string) }}</span><a href="{{ url_for('add', pid=p.id) }}">+</a></div>
      {% else %}
        <a class="buy" href="{{ url_for('add', pid=p.id) }}">Купить</a>
      {% endif %}
      {% if user %}<a class="heart" href="{{ url_for('fav', pid=p.id) }}">{{ '♥' if p.id in user.favorites else '♡' }}</a>{% endif %}
    </article>
  {% endfor %}
  </div>
</main>
{% endblock %}
'''

FILES["templates/cart.html"] = r'''
{% extends "base.html" %}{% block body %}
{% include "header.html" %}
<main class="catalog-wrap">
  <h1>Корзина</h1>
  {% if items %}
    <div class="list-card">
    {% for p, qty, s in items %}
      <div class="cart-row"><b>{{ p.name }}</b><span>{{ qty }} шт.</span><span>{{ s }} ₽</span><a href="{{ url_for('minus', pid=p.id) }}">-</a><a href="{{ url_for('add', pid=p.id) }}">+</a></div>
    {% endfor %}
    <h2>Итого: {{ total }} ₽</h2>
    <a class="blue-btn" href="{{ url_for('checkout') }}">Оформить заказ</a>
    </div>
  {% else %}<p>Корзина пустая</p>{% endif %}
</main>
{% endblock %}
'''

FILES["templates/checkout.html"] = r'''
{% extends "auth_base.html" %}{% block auth %}
<h1 class="blue-title">Оформление заказа</h1>
<form method="post" class="auth-form order-form">
  <b>Адрес доставки</b>
  <label>⌂ <input name="city" placeholder="Город"></label>
  <label>⌖ <input name="street" placeholder="Улица"></label>
  <label>⌂ <input name="house" placeholder="Дом"></label>
  <label>☎ <input name="phone" placeholder="Номер телефона"></label>
  <b>Промокод</b><label><input name="promo" placeholder="Промокод"></label>
  <b>Комментарии к заказу</b><label>▤ <input name="comment" placeholder="Комментарии к заказу"></label>
  <b>Выберите способ оплаты</b><label>▣ <input name="pay" placeholder="Выберите способ оплаты"></label>
  <div class="checkout-bottom"><input value="Итого: {{ total }} ₽" readonly><button>Оформить заказ</button></div>
</form>
{% endblock %}
'''

FILES["templates/profile.html"] = r'''
{% extends "base.html" %}{% block body %}
<div class="cabinet">{% set active='profile' %}{% include "sidebar.html" %}
<main class="content">
  <div class="title-row"><h1>Личный кабинет</h1><div><span class="avatar">{{ user.login[:2].upper() }}</span> {{ user.login }}</div></div>
  <div class="stat-grid">
    <div class="stat"><small>Заказы</small><b>{{ orders_count }}</b><span>шт.</span></div>
    <div class="stat"><small>Избранное</small><b>{{ fav_count }}</b><span>шт.</span></div>
    <div class="stat"><small>Бонусные баллы</small><b>{{ user.bonus }}</b><span>руб</span></div>
  </div>
</main></div>
{% endblock %}
'''

FILES["templates/orders.html"] = r'''
{% extends "base.html" %}{% block body %}
<div class="cabinet">{% set active='orders' %}{% include "sidebar.html" %}
<main class="content"><h1>Заказы</h1><hr>
{% if orders %}
  <div class="orders-list">
  {% for o in orders %}
    <div class="order-card">
      <h2>Заказ от {{ o.date }}</h2>
      <a class="trash" href="{{ url_for('delete_order', i=loop.index0) }}">🗑</a>
      {% for it in o['items'] %}<p>{{ it.name }} <b>{{ it.qty }}</b> шт.</p>{% endfor %}
      <b>Итого: {{ o.total }} ₽</b>
    </div>
  {% endfor %}
  </div>
{% endif %}
</main></div>
{% endblock %}
'''

FILES["templates/favorites.html"] = r'''
{% extends "base.html" %}{% block body %}
<div class="cabinet">{% set active='favorites' %}{% include "sidebar.html" %}
<main class="content"><h1>Избранное</h1><hr>
  <div class="grid small-grid">
  {% for p in items %}
    <article class="product"><div class="prod-img">{{ p.pic }}</div><p>{{ p.name }}</p><b>{{ p.price }} ₽</b><a class="buy" href="{{ url_for('add', pid=p.id) }}">Купить</a></article>
  {% endfor %}
  </div>
</main></div>
{% endblock %}
'''

FILES["templates/settings.html"] = r'''
{% extends "base.html" %}{% block body %}
<div class="cabinet">{% set active='settings' %}{% include "sidebar.html" %}
<main class="content"><h1>Настройки</h1><hr>
  <h2>Личный профиль</h2>
  <form method="post" class="settings-card profile-form"><span class="avatar big">{{ user.login[:2].upper() }}</span><input name="login" value="{{ user.login }}"><input value="{{ user.email }}" readonly><button>Сохранить</button></form>
  <h2>Безопасность</h2>
  <div class="settings-card security"><div>🕵️ <b>Безопасность</b><br><small>Обновите пароль для дополнительной защиты аккаунта</small></div><a class="blue-btn" href="{{ url_for('change_password') }}">Изменить пароль</a></div>
  <div class="money"><a class="blue-btn" href="{{ url_for('add_card') }}">+ Добавить карту</a>{% for c in user.cards %}<div class="bank-card">МИР<br>***** **** **** {{ c.num }}<br>{{ c.date }}<br>{{ c.country }}</div>{% endfor %}</div>
  <div class="settings-card danger"><div>☣ <b>Удалить аккаунт</b><br><small>Удалить аккаунт и всю связанную с ним информацию</small></div><button class="red-btn">Удалить</button></div>
  <p><a href="{{ url_for('logout') }}">Выйти</a></p>
</main></div>
{% endblock %}
'''

FILES["templates/add_card.html"] = r'''
{% extends "base.html" %}{% block body %}
<div class="cabinet">{% set active='settings' %}{% include "sidebar.html" %}
<main class="content"><h1>Добавление карты</h1><hr>
<form method="post" class="card-form">
  <b>Номер карты</b><input name="num" placeholder="Введите номер карты">
  <div><input name="date" placeholder="ММ / ГГ"><input name="cvc" placeholder="CVC"></div>
  <b>Имя владельца карты</b><input name="name" placeholder="Введите имя владельца карты">
  <button>Добавить карту</button><a href="{{ url_for('settings') }}">Отмена</a>
</form>
</main></div>
{% endblock %}
'''

FILES["templates/change_password.html"] = r'''
{% extends "base.html" %}{% block body %}
<div class="cabinet">{% set active='settings' %}{% include "sidebar.html" %}
<main class="content"><h1>Изменение пароля</h1><hr>
{% with messages=get_flashed_messages() %}{% if messages %}<p class="msg">{{ messages[0] }}</p>{% endif %}{% endwith %}
<form method="post" class="card-form"><b>Новый пароль</b><input name="p1" type="password" placeholder="Введите новый пароль"><small>Пароль должен быть не менее 8 символов</small><b>Подтверждение пароля</b><input name="p2" type="password" placeholder="Введите новый пароль еще раз"><button>Сохранить</button><a href="{{ url_for('settings') }}">Отмена</a></form>
</main></div>
{% endblock %}
'''

FILES["templates/about.html"] = r'''
{% extends "base.html" %}{% block body %}
<div class="cabinet simple-left">
<aside class="side"><a class="logo side-logo" href="{{ url_for('home') }}">Фурмацевт<span>.ru</span></a><a class="catalog-link" href="{{ url_for('catalog') }}">Перейти в каталог</a><div class="doctor small-doc">🧑‍⚕️</div></aside>
<main class="content about"><h1>Кто мы <b>?</b></h1><hr><div class="about-grid"><p>Аптечная сеть Фурмацевт.ru — это безупречное немецкое качество и европейский сервис. Сеть основал выдающийся человек — Гений, миллиардер, плейбой, филантроп, известный под псевдонимом Парацетомол. Уникальность аптеки в том, что создатель готов лично приехать и пообщаться с каждым недовольным клиентом, чтобы решить проблему. Во всём остальном уровень обслуживания остается неизменно высоким, как в лучших традициях немецкой фармацевтики.</p><div class="nurse">👧<br>➕</div></div></main>
</div>
{% endblock %}
'''

FILES["static/style.css"] = r'''
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@300;400;500;600&display=swap');
*{box-sizing:border-box} body{margin:0;background:#f1f4fb;font-family:Oswald,Arial,sans-serif;color:#111;font-size:24px} a{color:#0057d9;text-decoration:none} .logo{font-size:25px;color:#075dec;text-shadow:0 2px 3px #9ebcff}.logo span{color:#e50022}.topbar{height:78px;background:#eaf0ff;display:flex;align-items:center;gap:30px;padding:4px 16px;color:#003b90}.phone{position:absolute;top:4px;left:17px;background:#dbe7ff;border-radius:12px;padding:2px 10px;font-size:17px}.topbar .logo{margin-top:24px;min-width:145px}.topbar nav{display:flex;gap:35px;font-size:16px;margin-top:28px}.topbar nav a{color:#003b90}.search{width:340px;height:48px;background:#f5f8ff;border-radius:14px;margin-top:18px;display:flex;align-items:center;padding:0 12px;color:#5a8dec}.search input{border:0;background:transparent;outline:0;width:100%;font-family:inherit;color:#888;font-size:16px}.icons{margin-left:auto;display:flex;gap:23px;align-items:center}.icons a{font-size:36px;text-align:center;color:#0046a5}.icons small{display:block;font-size:15px;color:#003b90}.hero{height:175px;background:white;display:flex;align-items:flex-start;justify-content:center;gap:70px;padding-top:22px}.hero h1{color:#003b90;font-size:40px;margin:0 0 22px}.hero h3{color:#003b90;font-size:21px;margin:0}.doctor{font-size:105px;filter:saturate(1.1)}.hero-doc{font-size:118px}.pill-banner{height:425px;margin:0 10px;background:linear-gradient(135deg,#f26868,#fff 15%,#f8d957 25%,#d34141 38%,#fff 46%,#35b66a 57%,#e34f4f 70%,#2b91d9 85%);border-radius:35px;position:relative}.big-btn,.blue-btn,.red-btn,.buy,button{display:inline-block;border:0;border-radius:12px;background:#5382ee;color:white;padding:12px 28px;font-family:inherit;font-size:20px;cursor:pointer}.big-btn{position:absolute;left:25px;top:135px;font-size:35px;text-shadow:0 2px #333}.red-btn{background:#cf0000}.promo{background:white;display:grid;grid-template-columns:1.2fr .8fr;padding:30px 60px;color:#003b90}.promo h1{text-align:center;font-size:38px;font-weight:400}.promo h2{text-align:center}.family{height:330px;border-radius:8px;background:#d7efe7;font-size:80px;text-align:center;padding-top:110px}.bubble{width:360px;height:430px;border:6px solid #333;border-radius:48% 52% 55% 45%;font-size:38px;text-align:center;padding-top:80px;margin:auto;color:#003b90}.catalog-wrap{background:white;min-height:690px;padding:30px 90px}.catalog-wrap h1{color:#003b90;font-size:38px;font-weight:400}.grid{display:grid;grid-template-columns:repeat(4,1fr);border:4px solid #91b4ff}.product{height:175px;border:3px solid #91b4ff;background:white;position:relative;padding:12px 14px 8px 105px;font-size:14px;color:#4870a8}.prod-img{position:absolute;left:12px;top:20px;width:80px;height:105px;font-size:58px;display:flex;align-items:center;justify-content:center}.prod-name{min-height:70px;margin:0}.price{margin:0;font-size:14px}.price b{color:#1f62c9}.buy{padding:5px 17px;font-size:16px;border-radius:16px;background:#a8c4ff;color:#003b90}.qty{display:inline-flex;gap:14px;background:#83dfaa;border-radius:18px;padding:4px 12px;color:#003b90}.qty a{color:#003b90}.heart{position:absolute;right:8px;bottom:6px}.auth-page{min-height:100vh;background:#f1f4fb;display:flex;align-items:center;justify-content:center}.modal-card{width:515px;min-height:580px;background:white;border-radius:10px;position:relative;text-align:center;padding:38px 72px}.close{position:absolute;right:10px;top:10px;font-size:26px}.auth-logo{margin-bottom:12px}.modal-card h1{font-size:34px;font-weight:400;margin:10px}.muted{color:#b0b7c5;font-size:20px}.auth-form{display:flex;flex-direction:column;gap:26px}.auth-form label,.auth-form input{width:100%}.auth-form label{height:48px;border:1px solid #ddd;border-radius:13px;display:flex;align-items:center;padding:0 12px;color:#8fb0e9}.auth-form input{border:0;outline:0;font-family:inherit;font-size:20px;color:#777}.auth-form button{align-self:center;width:190px}.auth-doc{position:absolute;right:45px;bottom:38px;font-size:110px}.msg{color:#d00000;font-size:17px}.cabinet{display:grid;grid-template-columns:225px 1fr;min-height:100vh}.side{background:white;position:relative;padding:28px 20px}.side-logo{display:block;margin-bottom:80px}.side-nav{display:flex;flex-direction:column;gap:20px}.side-nav a{font-size:28px;color:#111;padding:3px 12px;border-radius:10px}.side-nav a.active{background:#adc6ff;color:#0060ff;border-left:10px solid #0060ff}.small-doc{position:absolute;bottom:40px;left:55px;font-size:115px}.content{padding:28px 36px}.content h1{font-size:42px;font-weight:400;margin:0 0 8px}.content hr{border:0;border-top:1px solid #111}.title-row{display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #111}.avatar{display:inline-flex;background:#0057ff;color:white;border-radius:50%;width:50px;height:50px;align-items:center;justify-content:center;margin-right:12px}.avatar.big{width:82px;height:82px;font-size:30px}.stat-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:32px;margin-top:120px}.stat{height:205px;background:white;box-shadow:0 3px 2px #bbb;padding:18px;color:#b8c0d0}.stat b{display:inline-block;color:#0057ff;font-size:70px;margin:55px 8px 0 90px;font-weight:400}.stat span{color:#0057ff}.orders-list{display:flex;gap:25px;flex-wrap:wrap;margin-top:60px}.order-card{width:235px;background:white;box-shadow:0 2px 3px #aaa;padding:10px;position:relative;font-size:14px}.order-card h2{font-size:23px;margin:0 0 15px}.trash{position:absolute;right:8px;top:8px;color:#999}.small-grid{border:0;grid-template-columns:repeat(3,210px);gap:20px}.settings-card,.card-form{background:white;border:1px solid #bbb;border-radius:10px;padding:20px;margin:10px 0 18px}.profile-form{display:grid;grid-template-columns:90px 1fr;gap:10px;align-items:center}.profile-form input,.card-form input{height:40px;border:1px solid #bbb;border-radius:10px;font-family:inherit;font-size:22px;padding:0 15px}.profile-form button{grid-column:2}.security,.danger{display:flex;align-items:center;justify-content:space-between}.money{min-height:130px;background:linear-gradient(135deg,#77a85b,#e9e9e9,#8cb36b);border-radius:10px;margin:14px 0;padding:20px;display:flex;gap:25px;align-items:center}.bank-card{margin-left:auto;background:#f5f8ff;border-radius:12px;padding:18px;width:230px;font-size:15px;color:#777}.danger .red-btn{width:175px}.card-form{max-width:760px;display:flex;flex-direction:column;gap:18px}.card-form div{display:flex;gap:12px}.card-form button{align-self:center}.blue-title{color:#003b90}.order-form{gap:10px}.checkout-bottom{display:flex;gap:20px}.about-grid{display:grid;grid-template-columns:1fr 1fr;gap:40px}.about p{font-size:24px;line-height:1.55;text-align:justify}.nurse{background:#ddd;font-size:180px;text-align:center;padding-top:120px}.catalog-link{display:block;margin-top:50px;color:#977cff}.list-card{background:white;padding:20px;border-radius:10px}.cart-row{display:grid;grid-template-columns:1fr 90px 100px 40px 40px;gap:10px;border-bottom:1px solid #ddd;padding:10px;font-size:18px}
@media(max-width:900px){.topbar{gap:10px}.search{width:220px}.grid{grid-template-columns:repeat(2,1fr)}.cabinet{grid-template-columns:180px 1fr}.stat-grid{grid-template-columns:1fr}.modal-card{width:92%;padding:30px}}
'''

def write_project():
    if PROJECT.exists():
        shutil.rmtree(PROJECT)
    for rel, content in FILES.items():
        path = PROJECT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    zip_name = PROJECT.with_suffix(".zip")
    if zip_name.exists():
        zip_name.unlink()
    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as z:
        for path in PROJECT.rglob("*"):
            if path.is_file():
                z.write(path, path.relative_to(PROJECT.parent))
    print("Готово!")
    print(f"Создана папка: {PROJECT.resolve()}")
    print(f"Создан архив: {zip_name.resolve()}")
    print("Дальше:")
    print(f"  cd /d {PROJECT.resolve()}")
    print("  py -3 -m pip install -r requirements.txt")
    print("  py -3 app.py")

if __name__ == "__main__":
    write_project()
