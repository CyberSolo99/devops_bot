import logging
import re
import os
import paramiko
import psycopg2
import subprocess
from dotenv import load_dotenv
from telegram import Update, ForceReply
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    MessageHandler,
    Filters,
    ConversationHandler,
)

load_dotenv()

# Инициализация токена из .env
TOKEN = os.getenv("TOKEN")

SSH_HOST = os.getenv("RM_HOST")
SSH_PORT = os.getenv("RM_PORT")
SSH_USERNAME = os.getenv("RM_USER")
SSH_PASSWORD = os.getenv("RM_PASSWORD")

DB_DATABASE = os.getenv("DB_DATABASE")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
LOG_FILE_PATH = "/var/log/postgresql/postgresql.log"
# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filename="logfile.txt",  # Логи будут записываться в log.log
)

logger = logging.getLogger(__name__)


def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(
        f"Привет, бро {user.first_name}! Отправь /help, если хочешь ознакомиться с функциями бота"
    )


def helpCommand(update: Update, context):
    help_txt = """
    Посмотри список доступных команд:
    /start - Запуск бота
    /help - Получить информацию о доступных командах
    /find_phone_number - Поиск телефонных номеров в тексте 
    /find_email - Поиск email-адресов в тексте
    /verify_password - Проверка сложности пароля
    \n\nКоманды для получения информации о системы по SSH
    /get_release - Получить информацию о релизе системы
    /get_uname - Получить информацию об архитектуру процессора, имени хоста системы и версии ядра
    /get_uptime - Получить информацию о времени работы
    /get_df - Сбор информации о состоянии файловой системы
    /get_free - Сбор информации о состоянии оперативной памяти
    /get_mpstat -  Сбор информации о производительности системы
    /get_w - Сбор информации о работающих в данной системе пользователях
    /get_auths - Сбор логов (Последние 10 входов в систему)
    /get_critical - Сбор логов (Последние 5 критических событий)
    /get_ps - Сбор информации о запущенных процессах
    /get_ss - Сбор информации об используемых портах
    /get_apt_list - Сбор информации об установленных пакетах
    /get_services - Сбор информации о запущенных сервисах
    /get_repl_logs - Вывод логов 
    /get_emails - Получить email-адреса из БД
    /get_phone_numbers - Получить телефонные номера из БД
    """
    update.message.reply_text(help_txt)


def echo(update: Update, context):
    update.message.reply_text(
        "Введите желаемую команду! Ознакомиться с функционалом можно с помощью /help ."
    )


def findPhoneNymbersCommand(update: Update, context):
    update.message.reply_text("Введите текст для поиска телефонных номеров: ")
    return "find_phone_number"


def findPhoneNumbers(update: Update, context):
    user_input = (
        update.message.text
    )  # Получаю текст, который будет или не будет содержать номер(а) телефона(ов)
    phoneNumRegex = re.compile(
        r"(?:\+7|8)[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}"
    )  # регулярка для формата номера телефона
    global phoneNuberList
    phoneNuberList = phoneNumRegex.findall(user_input)  # ищу номера телефонов

    if not phoneNuberList:
        update.message.reply_text("Телефонные номера не найдены")
        return ConversationHandler.END  # завершил выполнение функции

    phoneNumbers = ""  # создал пустую строку, в нее буду записывать номера телефонов
    for i in range(len(phoneNuberList)):
        phoneNumbers += f"{i+1}. {phoneNuberList[i]}\n"
    update.message.reply_text("Найденные номера телефонов: ")
    update.message.reply_text(phoneNumbers)  # отправляю сообщение пользователю
    update.message.reply_text(
        "Записать найденные телефонные номера в базу данных?\nОтветьте да или нет"
    )
    return "save_phone_number_to_db_bot"


def findEmailCommand(update: Update, context):
    update.message.reply_text("Введите текст для поиска email-адресов: ")
    return "find_email"


def findEmailAddress(update: Update, context):
    user_input = (
        update.message.text
    )  # получаю текст, который будет или не будет содержать адрес(а) почт(ы)
    emailAddressRegex = re.compile(
        r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    )  # регулярка для формата email-адресов
    global emailAddressList
    emailAddressList = emailAddressRegex.findall(user_input)  # ищу email-адреса
    if (
        not emailAddressList
    ):  # если их нет, то завершаю функцию и вывожу сообщение для пользователя
        update.message.reply_text("Email-адреса не найдены")
        return ConversationHandler.END
    emailAddress = ""  # создал пустую строку, в которую потом запишу email-адреса
    for i in range(len(emailAddressList)):
        emailAddress += f"{i+1}. {emailAddressList[i]}\n"
    update.message.reply_text("Найденные email-адреса: ")
    update.message.reply_text(emailAddress)
    update.message.reply_text(
        "Записать найденные email адреса в базу данных?\nОтветьте да или нет"
    )
    return "save_email_to_db_bot"


def verifyPasswordCommand(update: Update, context):
    update.message.reply_text("Введите пароль для проверки его сложности: ")
    return "verify_password"


def verifyPassword(update: Update, context):
    user_input = update.message.text

    if len(user_input) < 8:
        update.message.reply_text("Пароль простой")
        return ConversationHandler.END

    if not re.search(r"[A-Z]", user_input):
        update.message.reply_text("Пароль простой")
        return ConversationHandler.END

    if not re.search(r"[a-z]", user_input):
        update.message.reply_text("Пароль простой")
        return ConversationHandler.END

    if not re.search(r"\d", user_input):
        update.message.reply_text("Пароль простой")
        return ConversationHandler.END

    if not re.search(r"[!@#$%^&*()]", user_input):
        update.message.reply_text("Пароль простой")
        return ConversationHandler.END

    update.message.reply_text("Пароль сложный")
    return ConversationHandler.END


# задание 3
def get_release(update: Update, context):
    if SSH_HOST == "" or SSH_USERNAME == "" or SSH_PASSWORD == "":
        update.message.reply_text("Неверно заданы параметры подключения по SSH")
        return

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(
            hostname=SSH_HOST,
            port=SSH_PORT,
            username=SSH_USERNAME,
            password=SSH_PASSWORD,
        )
        stdin, stdout, stderr = ssh_client.exec_command("lsb_release -a")
        release_information = stdout.read().decode("utf-8")
        update.message.reply_text(release_information)
    except Exception as error:
        update.message.reply_text(f"Ошибка подключения: {str(error)}")
    finally:
        ssh_client.close()


def get_uname(update: Update, context):
    if SSH_HOST == "" or SSH_USERNAME == "" or SSH_PASSWORD == "":
        update.message.reply_text("Неверно заданы параметры подключения по SSH")
        return
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh_client.connect(
            hostname=SSH_HOST,
            port=SSH_PORT,
            username=SSH_USERNAME,
            password=SSH_PASSWORD,
        )
        stdin, stdout, stderr = ssh_client.exec_command("uname -a")
        uname_information = stdout.read().decode("utf-8")
        update.message.reply_text(uname_information)
    except Exception as error:
        update.message.reply_text(f"Ошибка подключения: {str(error)}")
    finally:
        ssh_client.close()


def get_uptime(update: Update, context):
    if SSH_HOST == "" or SSH_USERNAME == "" or SSH_PASSWORD == "":
        update.message.reply_text("Неверно заданы параметры подключения по SSH")
        return
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh_client.connect(
            hostname=SSH_HOST,
            port=SSH_PORT,
            username=SSH_USERNAME,
            password=SSH_PASSWORD,
        )
        stdin, stdout, stderr = ssh_client.exec_command("uptime")
        uptime_information = stdout.read().decode("utf-8")
        update.message.reply_text(uptime_information)
    except Exception as error:
        update.message.reply_text(f"Ошибка подключения: {str(error)}")
    finally:
        ssh_client.close()


def get_df(update: Update, context):
    if SSH_HOST == "" or SSH_USERNAME == "" or SSH_PASSWORD == "":
        update.message.reply_text("Неверно заданы параметры подключения по SSH")
        return
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh_client.connect(
            hostname=SSH_HOST,
            port=SSH_PORT,
            username=SSH_USERNAME,
            password=SSH_PASSWORD,
        )
        stdin, stdout, stderr = ssh_client.exec_command("df -h")
        df_information = stdout.read().decode("utf-8")
        update.message.reply_text(df_information)
    except Exception as error:
        update.message.reply_text(f"Ошибка подключения: {str(error)}")
    finally:
        ssh_client.close()


def get_free(update: Update, context):
    if SSH_HOST == "" or SSH_USERNAME == "" or SSH_PASSWORD == "":
        update.message.reply_text("Неверно заданы параметры подключения по SSH")
        return
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh_client.connect(
            hostname=SSH_HOST,
            port=SSH_PORT,
            username=SSH_USERNAME,
            password=SSH_PASSWORD,
        )
        stdin, stdout, stderr = ssh_client.exec_command("free -m")
        free_information = stdout.read().decode("utf-8")
        update.message.reply_text(free_information)
    except Exception as error:
        update.message.reply_text(f"Ошибка подключения: {str(error)}")
    finally:
        ssh_client.close()


def get_mpstat(update: Update, context):
    if SSH_HOST == "" or SSH_USERNAME == "" or SSH_PASSWORD == "":
        update.message.reply_text("Неверно заданы параметры подключения по SSH")
        return
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh_client.connect(
            hostname=SSH_HOST,
            port=SSH_PORT,
            username=SSH_USERNAME,
            password=SSH_PASSWORD,
        )
        stdin, stdout, stderr = ssh_client.exec_command("mpstat")
        mpstat_information = stdout.read().decode("utf-8")
        update.message.reply_text(mpstat_information)
    except Exception as error:
        update.message.reply_text(f"Ошибка подключения: {str(error)}")
    finally:
        ssh_client.close()


def get_w(update: Update, context):
    if SSH_HOST == "" or SSH_USERNAME == "" or SSH_PASSWORD == "":
        update.message.reply_text("Неверно заданы параметры подключения по SSH")
        return
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh_client.connect(
            hostname=SSH_HOST,
            port=SSH_PORT,
            username=SSH_USERNAME,
            password=SSH_PASSWORD,
        )
        stdin, stdout, stderr = ssh_client.exec_command("w")
        w_information = stdout.read().decode("utf-8")
        update.message.reply_text(w_information)
    except Exception as error:
        update.message.reply_text(f"Ошибка подключения: {str(error)}")
    finally:
        ssh_client.close()


def get_auths(update: Update, context):
    if SSH_HOST == "" or SSH_USERNAME == "" or SSH_PASSWORD == "":
        update.message.reply_text("Неверно заданы параметры подключения по SSH")
        return
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh_client.connect(
            hostname=SSH_HOST,
            port=SSH_PORT,
            username=SSH_USERNAME,
            password=SSH_PASSWORD,
        )
        stdin, stdout, stderr = ssh_client.exec_command("last -n 10")
        auths_information = stdout.read().decode("utf-8")
        update.message.reply_text(auths_information)
    except Exception as error:
        update.message.reply_text(f"Ошибка подключения: {str(error)}")
    finally:
        ssh_client.close()


def get_critical(update: Update, context):
    if SSH_HOST == "" or SSH_USERNAME == "" or SSH_PASSWORD == "":
        update.message.reply_text("Неверно заданы параметры подключения по SSH")
        return
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh_client.connect(
            hostname=SSH_HOST,
            port=SSH_PORT,
            username=SSH_USERNAME,
            password=SSH_PASSWORD,
        )
        stdin, stdout, stderr = ssh_client.exec_command(
            "journalctl -r -p crit -n 5 | head -n 10"
        )
        critical_information = stdout.read().decode("utf-8")
        update.message.reply_text(critical_information)
    except Exception as error:
        update.message.reply_text(f"Ошибка подключения: {str(error)}")
    finally:
        ssh_client.close()


def get_ps(update: Update, context):
    if SSH_HOST == "" or SSH_USERNAME == "" or SSH_PASSWORD == "":
        update.message.reply_text("Неверно заданы параметры подключения по SSH")
        return
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh_client.connect(
            hostname=SSH_HOST,
            port=SSH_PORT,
            username=SSH_USERNAME,
            password=SSH_PASSWORD,
        )
        stdin, stdout, stderr = ssh_client.exec_command("ps aux | head -n 10")
        ps_information = stdout.read().decode("utf-8")
        update.message.reply_text(ps_information)
    except Exception as error:
        update.message.reply_text(f"Ошибка подключения: {str(error)}")
    finally:
        ssh_client.close()


def get_ss(update: Update, context):
    if SSH_HOST == "" or SSH_USERNAME == "" or SSH_PASSWORD == "":
        update.message.reply_text("Неверно заданы параметры подключения по SSH")
        return
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh_client.connect(
            hostname=SSH_HOST,
            port=SSH_PORT,
            username=SSH_USERNAME,
            password=SSH_PASSWORD,
        )
        stdin, stdout, stderr = ssh_client.exec_command("ss -tuln")
        ss_information = stdout.read().decode("utf-8")
        update.message.reply_text(ss_information)
    except Exception as error:
        update.message.reply_text(f"Ошибка подключения: {str(error)}")
    finally:
        ssh_client.close()


def get_apt_list(update: Update, context):
    if SSH_HOST == "" or SSH_USERNAME == "" or SSH_PASSWORD == "":
        update.message.reply_text("Неверно заданы параметры подключения по SSH")
        return
    update.message.reply_text(
        "Выберите взаимодействие с командой:\n1.Вывод всех пакетов\n2.Поиск информации о пакете, который вы запросите"
    )
    return "get_apt_list_command"


def get_apt_list_command(update: Update, context):
    user_input = update.message.text.strip()
    if user_input == "1":
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh_client.connect(
                hostname=SSH_HOST,
                port=SSH_PORT,
                username=SSH_USERNAME,
                password=SSH_PASSWORD,
            )
            stdin, stdout, stderr = ssh_client.exec_command(
                "apt list --installed | head -n 20"
            )
            apt_list_information = stdout.read().decode("utf-8")
            update.message.reply_text(apt_list_information)
        except Exception as error:
            update.message.reply_text(f"Ошибка подключения: {str(error)}")
        finally:
            ssh_client.close()
        return ConversationHandler.END
    elif user_input == "2":
        update.message.reply_text("Введите название пакета: ")
        return "apt_list"
    else:
        update.message.reply_text("Выберите 1 или 2")
        return ConversationHandler.END


def apt_list(update: Update, context):
    packet = update.message.text

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(
            hostname=SSH_HOST,
            port=SSH_PORT,
            username=SSH_USERNAME,
            password=SSH_PASSWORD,
        )
        stdin, stdout, stderr = ssh_client.exec_command(
            f"apt list --installed {packet}"
        )
        apt_list_information = stdout.read().decode("utf-8")
        update.message.reply_text(apt_list_information)
    except Exception as error:
        update.message.reply_text(f"Ошибка подключения: {str(error)}")
    finally:
        ssh_client.close()
    return ConversationHandler.END


def get_services(update: Update, context):
    if SSH_HOST == "" or SSH_USERNAME == "" or SSH_PASSWORD == "":
        update.message.reply_text("Неверно заданы параметры подключения по SSH")
        return
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh_client.connect(
            hostname=SSH_HOST,
            port=SSH_PORT,
            username=SSH_USERNAME,
            password=SSH_PASSWORD,
        )
        stdin, stdout, stderr = ssh_client.exec_command(
            "systemctl list-units --type=service --state=running"
        )
        services_information = stdout.read().decode("utf-8")
        update.message.reply_text(services_information)
    except Exception as error:
        update.message.reply_text(f"Ошибка подключения: {str(error)}")
    finally:
        ssh_client.close()


def get_repl_logs(update: Update, context: CallbackContext) -> None:
    try:
        # Выполнение команды для получения логов
        result = subprocess.run(
            ["bash", "-c", f"cat {LOG_FILE_PATH} | grep repl | tail -n 15"],
            capture_output=True,
            text=True
        )
        logs = result.stdout
        if logs:
            update.message.reply_text(f"Последние репликационные логи:\n{logs}")
        else:
            update.message.reply_text("Репликационные логи не найдены.")
    except Exception as e:
        update.message.reply_text(f"Ошибка при получении логов: {str(e)}")


def connect_to_db_bot():
    try:
        connection = psycopg2.connect(
            dbname=DB_DATABASE,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
        )
        return connection
    except psycopg2.Error as error:
        print("Не удалось подключиться к базе данных: ", error)


# функция для получения списка email из email_addresses
def get_emails(update: Update, context):
    try:
        connection = connect_to_db_bot()
        cursor = connection.cursor()
        cursor.execute("SELECT email FROM email_addresses")
        email_addresses = cursor.fetchall()
        if email_addresses:
            email_list = "\n".join([email[0] for email in email_addresses])
            update.message.reply_text(f"Список email-адресов:\n{email_list}")
        else:
            update.message.reply_text("Нет доступных email-адресов.")
    except psycopg2.Error as error:
        update.message.reply_text(
            f"Ошибка получения данных электронных почт из БД: {str(error)}"
        )
    finally:
        cursor.close()
        connection.close()


def get_phone_numbers(update: Update, context):
    try:
        connection = connect_to_db_bot()
        cursor = connection.cursor()
        cursor.execute("SELECT phone_number FROM phone_numbers")
        phone_numbers = cursor.fetchall()
        if phone_numbers:
            phone_number_list = "\n".join(
                [phone_number[0] for phone_number in phone_numbers]
            )
            update.message.reply_text(
                f"Список телефонных номеров:\n{phone_number_list}"
            )
        else:
            update.message.reply_text("Нет доступных телефонных номеров")
    except psycopg2.Error as error:
        update.message.reply_text(
            f"Ошибка получения данных телефонных номеров из БД: {str(error)}"
        )
    finally:
        cursor.close()
        connection.close()


def save_phone_number_to_db_bot(update: Update, context):
    answer = update.message.text.lower()
    if answer in ["да", "yes"]:
        global phoneNuberList

        for phone_number in phoneNuberList:
            try:
                connection = connect_to_db_bot()
                cursor = connection.cursor()
                cursor.execute(
                    "SELECT * FROM phone_numbers WHERE phone_number = %s",
                    (phone_number,),
                )
                exist_phone = cursor.fetchone()
                if exist_phone:
                    update.message.reply_text(
                        f"Номер телефона {phone_number} есть в БД"
                    )
                    continue

                cursor.execute(
                    "INSERT INTO phone_numbers (phone_number) VALUES (%s)",
                    (phone_number,),
                )
                connection.commit()
                update.message.reply_text(f"Номер телефона {phone_number} записан в БД")
            except psycopg2.Error as error:
                update.message.reply_text(
                    "Ошибка при добавлении телефонных номеров в бд: {str(error)}"
                )
            finally:
                cursor.close()
                connection.close()
    return ConversationHandler.END


def save_email_to_db_bot(update: Update, context):
    answer = update.message.text.lower()
    if answer in ["да", "yes"]:
        global emailAddressList

        for email in emailAddressList:
            try:
                connection = connect_to_db_bot()
                cursor = connection.cursor()
                cursor.execute(
                    "SELECT * FROM email_addresses WHERE email = %s",
                    (email,),
                )
                exist_email = cursor.fetchone()
                if exist_email:
                    update.message.reply_text(f"Адрес почты {email} есть в БД")
                    continue

                cursor.execute(
                    "INSERT INTO email_addresses (email) VALUES (%s)",
                    (email,),
                )
                connection.commit()
                update.message.reply_text(f"Адрес почты {email} записан в БД")
            except psycopg2.Error as error:
                update.message.reply_text(
                    "Ошибка при добавлении телефонных номеров в бд: {str(error)}"
                )
            finally:
                cursor.close()
                connection.close()
    return ConversationHandler.END


def main():
    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher

    # обработчик диалога
    convHandler = ConversationHandler(
        entry_points=[
            CommandHandler("find_phone_number", findPhoneNymbersCommand),
            CommandHandler("find_email", findEmailCommand),
            CommandHandler("verify_password", verifyPasswordCommand),
            CommandHandler("get_apt_list", get_apt_list),
        ],
        states={
            "find_phone_number": [
                MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)
            ],
            "find_email": [
                MessageHandler(Filters.text & ~Filters.command, findEmailAddress)
            ],
            "verify_password": [
                MessageHandler(Filters.text & ~Filters.command, verifyPassword)
            ],
            "get_apt_list_command": [
                MessageHandler(Filters.text & ~Filters.command, get_apt_list_command)
            ],
            "apt_list": [MessageHandler(Filters.text & ~Filters.command, apt_list)],
            "save_phone_number_to_db_bot": [
                MessageHandler(
                    Filters.text & ~Filters.command, save_phone_number_to_db_bot
                )
            ],
            "save_email_to_db_bot": [
                MessageHandler(Filters.text & ~Filters.command, save_email_to_db_bot)
            ],
        },
        fallbacks=[],
    )
    # регистрирую обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(CommandHandler("get_release", get_release))
    dp.add_handler(CommandHandler("get_uname", get_uname))
    dp.add_handler(CommandHandler("get_uptime", get_uptime))
    dp.add_handler(CommandHandler("get_df", get_df))
    dp.add_handler(CommandHandler("get_free", get_free))
    dp.add_handler(CommandHandler("get_mpstat", get_mpstat))
    dp.add_handler(CommandHandler("get_w", get_w))
    dp.add_handler(CommandHandler("get_auths", get_auths))
    dp.add_handler(CommandHandler("get_critical", get_critical))
    dp.add_handler(CommandHandler("get_ps", get_ps))
    dp.add_handler(CommandHandler("get_ss", get_ss))
    dp.add_handler(CommandHandler("get_services", get_services))
    dp.add_handler(CommandHandler("get_repl_logs", get_repl_logs))
    dp.add_handler(CommandHandler("get_emails", get_emails))
    dp.add_handler(CommandHandler("get_phone_numbers", get_phone_numbers))
    dp.add_handler(convHandler)

    dp.add_handler(
        MessageHandler(Filters.text & ~Filters.command, echo)
    )  # обработчик текстовых сообщений

    updater.start_polling()  # запуск бота

    updater.idle()  # останвливаю бота при сочетании клавиш Ctrl+c


if __name__ == "__main__":
    main()
