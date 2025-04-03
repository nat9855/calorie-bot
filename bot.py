import os
import json
import telebot
from telebot import types

import os
from telebot import TeleBot, types

TOKEN = os.getenv("TOKEN")
bot = TeleBot(TOKEN)

# Загружаем базу продуктов
with open("products.json", "r", encoding="utf-8") as f:
    calorie_db = json.load(f)

# Временное хранилище продуктов и целей по пользователям
user_data = {}
user_goals = {}

# Главное меню
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Добавить продукты", "📊 Посчитать калории")
    markup.add("📋 Показать текущий список", "🧹 Очистить список")
    markup.add("📄 Список продуктов", "❓ Как пользоваться")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Я бот-калькулятор калорий. Выбирай действие:", reply_markup=main_menu())

@bot.message_handler(commands=['цель'])
def set_goal(message):
    parts = message.text.split()
    if len(parts) != 5:
        bot.send_message(message.chat.id, "Используй формат: /цель калории белки жиры углеводы\nПример: /цель 1500 100 50 100")
        return
    try:
        kcal, protein, fat, carb = map(float, parts[1:])
        user_goals[message.from_user.id] = {
            "kcal": kcal, "protein": protein, "fat": fat, "carb": carb
        }
        bot.send_message(message.chat.id, "Цели по калориям и БЖУ установлены ✅")
    except:
        bot.send_message(message.chat.id, "Неверный формат. Используй числа без единиц измерения.")

@bot.message_handler(func=lambda msg: msg.text == "❓ Как пользоваться")
def how_to_use(message):
    bot.send_message(message.chat.id, "1. Нажми '➕ Добавить продукты' и введи список.\n2. Потом нажми '📊 Посчитать калории'.\n3. Можно посмотреть или очистить текущий список.\n\nКоманда для установки цели: /цель калории белки жиры углеводы")

@bot.message_handler(func=lambda msg: msg.text == "📄 Список продуктов")
def show_products(message):
    product_list = "\n".join(calorie_db.keys())
    bot.send_message(message.chat.id, f"Доступные продукты:\n{product_list}")

@bot.message_handler(func=lambda msg: msg.text == "📋 Показать текущий список")
def show_current_list(message):
    uid = message.from_user.id
    if uid not in user_data or not user_data[uid]:
        bot.send_message(message.chat.id, "Список пуст.")
    else:
        current = "\n".join(user_data[uid])
        bot.send_message(message.chat.id, f"Текущий список:\n{current}")

@bot.message_handler(func=lambda msg: msg.text == "🧹 Очистить список")
def clear_list(message):
    uid = message.from_user.id
    user_data[uid] = []
    bot.send_message(message.chat.id, "Список очищен.")

@bot.message_handler(func=lambda msg: msg.text == "➕ Добавить продукты")
def request_products(message):
    bot.send_message(message.chat.id, "Введите продукты и их количество (каждый с новой строки):")
    bot.register_next_step_handler(message, save_products)

def save_products(message):
    uid = message.from_user.id
    lines = message.text.lower().split('\n')
    if uid not in user_data:
        user_data[uid] = []
    user_data[uid].extend(lines)
    bot.send_message(message.chat.id, "Продукты добавлены в список.", reply_markup=main_menu())

@bot.message_handler(func=lambda msg: msg.text == "📊 Посчитать калории")
def calculate(message):
    uid = message.from_user.id
    if uid not in user_data or not user_data[uid]:
        bot.send_message(message.chat.id, "Сначала добавь продукты.")
        return

    total_kcal = total_protein = total_fat = total_carb = 0
    for line in user_data[uid]:
        for name in calorie_db:
            if name in line:
                qty = 1
                if 'г' in line:
                    qty = int(''.join(filter(str.isdigit, line.split('г')[0])))
                    factor = qty / 100
                elif 'шт' in line:
                    qty = int(''.join(filter(str.isdigit, line.split('шт')[0])))
                    factor = qty
                else:
                    factor = 1

                data = calorie_db[name]
                total_kcal += data['kcal'] * factor
                total_protein += data['protein'] * factor
                total_fat += data['fat'] * factor
                total_carb += data['carb'] * factor

    result = (
        f"Калорийность накопленного:\n"
        f"Калории: {round(total_kcal)} ккал\n"
        f"Белки: {round(total_protein, 1)} г\n"
        f"Жиры: {round(total_fat, 1)} г\n"
        f"Углеводы: {round(total_carb, 1)} г\n"
    )

    # Если установлены цели, добавить сравнение
    if uid in user_goals:
        goals = user_goals[uid]
        result += "\n📈 Прогресс по цели:\n"
        result += f"Калории: {round(total_kcal)} / {goals['kcal']} (осталось: {round(goals['kcal'] - total_kcal)})\n"
        result += f"Белки: {round(total_protein,1)} / {goals['protein']} (осталось: {round(goals['protein'] - total_protein, 1)})\n"
        result += f"Жиры: {round(total_fat,1)} / {goals['fat']} (осталось: {round(goals['fat'] - total_fat, 1)})\n"
        result += f"Углеводы: {round(total_carb,1)} / {goals['carb']} (осталось: {round(goals['carb'] - total_carb, 1)})"

    bot.send_message(message.chat.id, result)
