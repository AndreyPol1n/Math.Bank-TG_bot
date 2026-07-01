import telebot
from telebot import types
import requests
from bs4 import BeautifulSoup
import math


def get_exchange_rate(table_object, currency_code):
    if isinstance(table_object, list) and len(table_object) > 0:
        table = table_object[0]
    else:
        table = table_object
    rows = table.find_all('tr')

    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 5:
            currency_cell = cells[1].text.strip()
            if currency_cell == currency_code.upper():
                rate_cell = float(cells[4].text.strip().replace(',', '.')) / float(cells[2].text.strip())
                return rate_cell
    return None


bot = telebot.TeleBot("8791602690:AAEN_VkZmhVLM_tNz1JH_Ce1kOghG142kew")
soup_data = {}
user_functions = {}

cor = {
    "AUD": "R01010", "AZN": "R01020A", "DZD": "R01030", "GBP": "R01035",
    "AMD": "R01060", "BHD": "R01080", "BYN": "R01090B", "BGN": "R01100",
    "BOB": "R01105", "BRL": "R01115", "HUF": "R01135", "VND": "R01150",
    "HKD": "R01200", "GEL": "R01210", "DKK": "R01215", "AED": "R01230",
    "USD": "R01235", "EUR": "R01239", "EGP": "R01240", "INR": "R01270",
    "IDR": "R01280", "IRR": "R01300", "KZT": "R01335", "CAD": "R01350",
    "QAR": "R01355", "KGS": "R01370", "CNY": "R01375", "CUP": "R01395",
    "MDL": "R01500", "MNT": "R01503", "NGN": "R01520", "NZD": "R01530",
    "NOK": "R01535", "OMR": "R01540", "PLN": "R01565", "SAR": "R01580",
    "RON": "R01585F", "XDR": "R01589", "SGD": "R01625", "TJS": "R01670",
    "THB": "R01675", "BDT": "R01685", "TRY": "R01700J", "TMT": "R01710A",
    "UZS": "R01717", "UAH": "R01720", "CZK": "R01760", "SEK": "R01770",
    "CHF": "R01775", "ETB": "R01800", "RSD": "R01805F", "ZAR": "R01810",
    "KRW": "R01815", "JPY": "R01820", "MMK": "R02005"
}

FUNCTIONS = {
    'sqrt': {'name': '√x (квадратный корень)', 'func': lambda x: math.sqrt(x) if x >= 0 else None, 'vba': 'Sqr'},
    'inv': {'name': '1/x (обратная)', 'func': lambda x: 1 / x if x != 0 else None, 'vba': '1 /'},
    'exp': {'name': 'e^x (экспонента)', 'func': lambda x: math.exp(x), 'vba': 'Exp'}
}


@bot.message_handler(commands=['start'])
def main(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton('5 Задание', callback_data='5')
    btn2 = types.InlineKeyboardButton('11 Задание', callback_data='11')
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, "Выберите номер лабораторной работы:", reply_markup=markup)


def show_function_choice(chat_id, step):
    """Показывает кнопки выбора функции для уровня step (3,2,1)"""
    markup = types.InlineKeyboardMarkup(row_width=2)

    btn1 = types.InlineKeyboardButton('√x (квадратный корень)', callback_data=f'func_{step}_sqrt')
    btn2 = types.InlineKeyboardButton('1/x (обратная)', callback_data=f'func_{step}_inv')
    btn3 = types.InlineKeyboardButton('e^x (экспонента)', callback_data=f'func_{step}_exp')

    markup.add(btn1, btn2, btn3)

    if step == 3:
        text = "📌 **Выберите F₃ (самую внутреннюю функцию):**\n\n*F₃ применяется к x первой*"
    elif step == 2:
        text = "📌 **Выберите F₂ (промежуточную функцию):**\n\n*F₂ применяется к результату F₃*"
    else:
        text = "📌 **Выберите F₁ (внешнюю функцию):**\n\n*F₁ применяется к результату F₂*"

    bot.send_message(chat_id, text, reply_markup=markup, parse_mode='Markdown')


def show_summary_and_input_x(chat_id):
    """Показывает итоговую формулу и запрашивает x"""
    functions = user_functions[chat_id]['functions']

    formula_readable = f"**y = F₁(F₂(F₃(x)))**\n\nгде:\n"
    formula_readable += f"F₁ = {FUNCTIONS[functions[2]]['name']}\n"
    formula_readable += f"F₂ = {FUNCTIONS[functions[1]]['name']}\n"
    formula_readable += f"F₃ = {FUNCTIONS[functions[0]]['name']}\n\n"
    formula_readable += f"**Порядок вычисления:**\n"
    formula_readable += f"1. Вычисляем F₃(x)\n"
    formula_readable += f"2. Вычисляем F₂(результат)\n"
    formula_readable += f"3. Вычисляем F₁(результат)"

    bot.send_message(chat_id, formula_readable, parse_mode='Markdown')
    bot.send_message(chat_id, "➗ **Введите значение x:**")


def calculate_function_chain(x, functions):
    """Вычисляет F₁(F₂(F₃(x)))"""
    result = x
    steps = []
    step_names = {3: 'F₃', 2: 'F₂', 1: 'F₁'}

    for i, func_name in enumerate(functions, 1):
        func = FUNCTIONS[func_name]['func']
        step_num = 4 - i
        old_result = result
        result = func(result)

        if result is None:
            return None, f"❌ Ошибка в функции {step_names[step_num]}: значение {old_result} не входит в область определения"

        steps.append(f"{step_names[step_num]}({old_result:.6f}) = {result:.6f}")

    return result, steps


def generate_vba_code(functions):
    """Генерирует VBA код для вычисления F₁(F₂(F₃(x)))"""
    vba_lines = []
    vba_lines.append("' VBA код для вычисления функции y = F₁(F₂(F₃(x)))")
    vba_lines.append("' Сгенерировано автоматически")
    vba_lines.append("")
    vba_lines.append("Function CalculateFunction(x As Double) As Variant")
    vba_lines.append("    On Error GoTo ErrorHandler")
    vba_lines.append("    Dim step1 As Double")
    vba_lines.append("    Dim step2 As Double")
    vba_lines.append("    Dim step3 As Double")
    vba_lines.append("    ")

    step_vars = ['x', 'step1', 'step2']
    for i, func_name in enumerate(functions):
        step_num = i + 1

        if func_name == 'sqrt':
            vba_lines.append(f"    If {step_vars[i]} < 0 Then GoTo ErrorHandler")
            vba_lines.append(f"    step{step_num} = Sqr({step_vars[i]})")
        elif func_name == 'inv':
            vba_lines.append(f"    If {step_vars[i]} = 0 Then GoTo ErrorHandler")
            vba_lines.append(f"    step{step_num} = 1 / {step_vars[i]}")
        else:
            vba_lines.append(f"    step{step_num} = Exp({step_vars[i]})")
        vba_lines.append("    ")

    vba_lines.append("    CalculateFunction = step3")
    vba_lines.append("    Exit Function")
    vba_lines.append("    ")
    vba_lines.append("ErrorHandler:")
    vba_lines.append("    CalculateFunction = CVErr(xlErrValue)")
    vba_lines.append("End Function")

    return "\n".join(vba_lines)


# ЕДИНЫЙ обработчик всех callback запросов
@bot.callback_query_handler(func=lambda call: True)
def handle_all_callbacks(call):
    global soup_data
    chat_id = call.message.chat.id
    data = call.data

    # Обработка выбора задания
    if data == "5":
        link = "https://www.cbr.ru/currency_base/daily/"
        bot.send_message(chat_id, "Подождите загрузки данных с сайта Центрального Банка России")
        response = requests.get(link)
        print(f"Статус код: {response.status_code}")
        soup = BeautifulSoup(response.text, "lxml")
        soup_data[chat_id] = soup
        bot.send_message(chat_id, "Данные успешно загружены, Введите какую валюту вы хотите увидеть:")
        bot.register_next_step_handler(call.message, kurs)
        return

    if data == "11":
        user_functions[chat_id] = {'functions': [], 'step': 3}
        bot.send_message(chat_id, "🔧 **Конструктор математической модели** 🔧\n")
        bot.send_message(chat_id, "Строим функцию вида: **y = F₁(F₂(F₃(x)))**\n")
        bot.send_message(chat_id, "Порядок вычисления:\n"
                                  "1️⃣ Сначала F₃ применяется к x\n"
                                  "2️⃣ Затем F₂ применяется к результату F₃\n"
                                  "3️⃣ Затем F₁ применяется к результату F₂\n")
        show_function_choice(chat_id, 3)
        return

    # Обработка выбора функции (func_3_sqrt и т.д.)
    if data.startswith('func_'):
        parts = data.split('_')
        step = int(parts[1])
        func_name = parts[2]

        if chat_id not in user_functions:
            user_functions[chat_id] = {'functions': [], 'step': 3}

        user_functions[chat_id]['functions'].append(func_name)

        try:
            bot.delete_message(chat_id, call.message.message_id)
        except:
            pass

        func_display = FUNCTIONS[func_name]['name']
        bot.send_message(chat_id, f"✅ Выбрана функция F{step}: {func_display}")

        if step > 1:
            user_functions[chat_id]['step'] = step - 1
            show_function_choice(chat_id, step - 1)
        else:
            show_summary_and_input_x(chat_id)
        return

    # Обработка генерации VBA кода
    if data == 'generate_vba':
        if chat_id not in user_functions or len(user_functions[chat_id].get('functions', [])) != 3:
            bot.send_message(chat_id, "Сначала создайте функцию через 11 задание")
            return

        functions = user_functions[chat_id]['functions']
        vba_code = generate_vba_code(functions)

        bot.send_message(chat_id, "```vba\n" + vba_code + "\n```", parse_mode='Markdown')
        bot.send_message(chat_id, "📝 **Инструкция по использованию VBA кода:**\n"
                                  "1. Откройте Excel\n"
                                  "2. Нажмите Alt+F11 для открытия редактора VBA\n"
                                  "3. Вставьте код в модуль (Insert → Module)\n"
                                  "4. Используйте функцию в ячейке: `=CalculateFunction(A1)`")
        return

    # Обработка создания новой функции
    if data == 'new_function':
        user_functions[chat_id] = {'functions': [], 'step': 3}
        try:
            bot.delete_message(chat_id, call.message.message_id)
        except:
            pass
        show_function_choice(chat_id, 3)
        return


# Обработчик ввода x после выбора всех функций
@bot.message_handler(func=lambda message: message.chat.id in user_functions and len(
    user_functions[message.chat.id].get('functions', [])) == 3)
def process_x_input(message):
    chat_id = message.chat.id

    try:
        x = float(message.text.replace(',', '.'))
        functions = user_functions[chat_id]['functions']
        result, steps = calculate_function_chain(x, functions)

        if result is None:
            bot.send_message(chat_id, steps)
            bot.send_message(chat_id, "Пожалуйста, введите другое значение x:")
            return

        bot.send_message(chat_id, "📈 **Результат вычислений:**")
        bot.send_message(chat_id, f"**x = {x}**")
        bot.send_message(chat_id, "---")

        for step in steps:
            bot.send_message(chat_id, step)

        bot.send_message(chat_id, "---")
        bot.send_message(chat_id, f"✅ **y = {result:.10f}**")

        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_vba = types.InlineKeyboardButton('💻 Сгенерировать VBA код', callback_data='generate_vba')
        btn_new = types.InlineKeyboardButton('🔄 Новая функция', callback_data='new_function')
        markup.add(btn_vba, btn_new)

        bot.send_message(chat_id, "Что делаем дальше?", reply_markup=markup)

    except ValueError:
        bot.send_message(chat_id, "❌ Ошибка! Введите число (например: 5 или 2.5)")


def kurs(message):
    input_currency = message.text.upper()
    if input_currency == "RUB":
        bot.send_message(message.chat.id, f"Вот курс {input_currency}: 1")
    elif len(input_currency) != 3:
        bot.send_message(message.chat.id, f"Ошибка, введите валюту на английском языке в сокращении(3 буквы)")
        bot.register_next_step_handler(message, kurs)
    else:
        soup = soup_data.get(message.chat.id)
        output = get_exchange_rate(soup, input_currency)
        bot.send_message(message.chat.id,
                         f"Вот курс {input_currency}: {output}, если вы хотите увидеть график, напишите дату начала в формате ДД.ММ.ГГГГ")
        bot.register_next_step_handler(message, get_graph, input_currency)


def get_graph(message, currency):
    ns = message.text.strip()
    ne = "11.04.2026"
    if len(ns) == 10 and ns[2] == '.' and ns[5] == '.':
        bot.send_message(message.chat.id,
                         f"Вот сайт с графиком: https://www.cbr.ru/currency_base/dynamics/?UniDbQuery.Posted=True&UniDbQuery.so=1&UniDbQuery.mode=2&UniDbQuery.date_req1=&UniDbQuery.date_req2=&UniDbQuery.VAL_NM_RQ={cor[currency]}&UniDbQuery.From={ns}&UniDbQuery.To={ne}")
    else:
        bot.send_message(message.chat.id, "Неверный формат даты. Используйте ДД.ММ.ГГГГ")
        bot.register_next_step_handler(message, get_graph, currency)


@bot.message_handler(func=lambda message: True)
def handle_other_messages(message):
    if message.text == '/start':
        return
    if message.chat.id in user_functions and len(user_functions[message.chat.id].get('functions', [])) < 3:
        bot.send_message(message.chat.id, "Пожалуйста, выберите функции с помощью кнопок")
    elif message.chat.id not in user_functions:
        bot.send_message(message.chat.id, "Нажмите /start для начала работы")


print("Бот запущен...")
bot.polling(none_stop=True)