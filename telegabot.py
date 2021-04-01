import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import re
import os
import telebot
from telebot import types


bot_token = os.getenv('mail_bot_bot_token')
bot = telebot.TeleBot(bot_token)
emails_set = set()
subject = ''
text = ''


def test_emails(emails):
    pattern = re.compile(r"\"?([-a-zA-Z0-9.`?{}]+@\w+\.\w+)\"?")
    for email in emails:
        if not re.match(pattern, email):
            return email
    return True


def send_email(message, email_list, subject, mail_text):
    try:
        smtp_obj = smtplib.SMTP('smtp.gmail.com', 587)
    except Exception as e:
        bot.send_message(message.chat.id, f'Ошибка при подключении к gmail.com, ({e})')
        return False

    from_addr = os.getenv('mail_bot_from_addr')
    password = os.getenv('mail_bot_password')
    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = ",".join(email_list)
    msg['Subject'] = subject
    body = mail_text
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        smtp_obj.starttls()
        smtp_obj.login(from_addr, password)
        smtp_obj.send_message(msg)
        smtp_obj.quit()
    except smtplib.SMTPException as e:
        bot.send_message(message.chat.id, f'Ошибка при работе с SMTP сервером ({e})')
        return False
    except Exception as e:
        bot.send_message(message.chat.id, f'Ошибка. Неправильная работа SMTP сервера ({e})')
        return False
    return True


@bot.message_handler(content_types=['text'])
def start(message):
    if message.text == '/start':
        bot.send_message(message.from_user.id, "Бот позволяет отправить тектовое сообщение на указанный список \
почтовых адресов. Используйте команду /help для вывода списка команд")
    elif message.text == '/help':
        bot.send_message(message.from_user.id, "/addmail - добавляет адреса почты в список\n"
                                               "/clearmail - очищает адреса почты в списоке\n"
                                               "/mail - показывает список адресов рассылки\n"
                                               "/addsub - добавляет (изменяет) тему письма\n"
                                               "/clearsub - очищает тему письма\n"
                                               "/sub - показывает тему письма\n"
                                               "/addtext - добавляет (изменяет) текст письма\n"
                                               "/cleartext - очищает текст письма\n"
                                               "/text - показывает текст письма\n"
                                               "/clearall - стирает все данные рассылки\n"
                                               "/send - отправляет письмо")
    elif message.text == '/addmail':
        bot.send_message(message.from_user.id, "Введите адрес получателя или их список через пробел")
        bot.register_next_step_handler(message, get_emails)
    elif message.text == '/clearmail':
        emails_set.clear()
        bot.send_message(message.from_user.id, "Список адресов рассылки очищен")
    elif message.text == '/mail':
        bot.send_message(message.from_user.id, "Список адресов рассылки: " + ', '.join(emails_set))
    elif message.text == '/addsub':
        bot.send_message(message.from_user.id, "Введите тему письма")
        bot.register_next_step_handler(message, get_subject)
    elif message.text == '/clearsub':
        global subject
        subject = ''
        bot.send_message(message.from_user.id, "Заголовок письма очищен")
    elif message.text == '/sub':
        bot.send_message(message.from_user.id, "Тема письма: " + str(subject))
    elif message.text == '/addtext':
        bot.send_message(message.from_user.id, "Введите текст письма")
        bot.register_next_step_handler(message, get_text)
    elif message.text == '/cleartext':
        global text
        text = ''
        bot.send_message(message.from_user.id, "Текст письма очищен")
    elif message.text == '/text':
        bot.send_message(message.from_user.id, "Текст письма: " + str(text))
    elif message.text == '/clearall':
        subject = ''
        text = ''
        emails_set.clear()
        bot.send_message(message.from_user.id, "Все данные о рассылке очищены")

    elif message.text == '/send':
        bot.send_message(message.from_user.id, "Отправка письма")
        bot.send_message(message.from_user.id, "Список адресов рассылки: " + ', '.join(emails_set))
        bot.send_message(message.from_user.id, "Тема письма: " + str(subject))
        bot.send_message(message.from_user.id, "Текст письма: " + str(text))
        keyboard = types.InlineKeyboardMarkup()  # наша клавиатура
        key_yes = types.InlineKeyboardButton(text='Да', callback_data='yes')  # кнопка «Да»
        keyboard.add(key_yes)  # добавляем кнопку в клавиатуру
        key_no = types.InlineKeyboardButton(text='Нет', callback_data='no')
        keyboard.add(key_no)
        question = 'Отправить?'
        bot.send_message(message.from_user.id, text=question, reply_markup=keyboard)
    else:
        bot.send_message(message.from_user.id, 'Команда не верна. Для вывода списка команд напиши /help')


def get_subject(message):
    global subject
    subject = message.text
    bot.send_message(message.from_user.id, "Тема письма: " + str(subject))


def get_emails(message):
    #global emails_list
    mails_list = message.text.split()
    if len(mails_list) == 0:
        bot.send_message(message.from_user.id, 'Список адресов пустой')
    else:
        check = test_emails(mails_list)
        if check is not True:
            bot.send_message(message.from_user.id, 'Не верно записан адрес: ' + str(check))
            return
    for m in mails_list:
        emails_set.add(m)
    bot.send_message(message.from_user.id, "Список адресов рассылки: " + ', '.join(emails_set))


def get_text(message):
    global text
    text = message.text
    bot.send_message(message.from_user.id, "Текст письма: " + str(text))


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    if call.data == "yes":
        #код сохранения данных, или их обработки
        emails_list = []
        for m in emails_set:
            emails_list.append(m)
        if send_email(call.message, emails_list, subject, text):
            bot.send_message(call.from_user.id, 'Отправлено')
    elif call.data == "no":
        bot.send_message(call.from_user.id, 'Отправка отменена')


bot.polling(none_stop=True, interval=0)
