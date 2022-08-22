import asyncio
from tabulate import tabulate
from os import getenv
from qbot.db.database import Database
from qbot.market.tinvest import Tinvest
from qbot.logger import logger
from qbot.helpers import path_db
from qbot.interval_actions import interval_polling, interval_news
from telegram.ext import (
    Filters,
    Updater,
    CommandHandler,
    MessageHandler,
)

tinkoff = Tinvest()
db = Database()

updater = Updater(token=getenv("TELE_TOKEN"))
dispatcher = updater.dispatcher


def start(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"QuoteBeholder это бот, который информирует об резких изменениях котировок.\nУкажите команду после '/'",
    )
    db.add_new_user_to_db(update.effective_user.id, update.effective_user.name)


def subscribe(update, context):
    if not db.check_user(update.effective_user.id):
        context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"Сначала нужно нажать /start"
        )
        return
    if context.args:
        sub_tickers = list()
        for ticker in context.args:
            if not db.check_ticker(ticker, update.effective_user.id):
                try:
                    tinkoff.subscribe_ticker(
                        ticker,
                        update.effective_user.name,
                        update.effective_user.id
                    )
                    sub_tickers.append(ticker)
                except ValueError:
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=f"Тикер {ticker} не найден.",
                    )
            else:
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"Вы уже подписаны на тикер {ticker} .",
                )
        if sub_tickers:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Вы успешно подписались на {', '.join(sub_tickers)}",
            )
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Не указаны тикеры, запустите команду так: /subscribe <TIK> или так /subscribe <TIK> <TIK> <TIK>",
        )
        return


def unsubscribe(update, context):
    if not db.check_user(update.effective_user.id):
        context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"Сначала нужно нажать /start"
        )
        return
    if context.args:
        sub_tickers = list()
        for ticker in context.args:
            if db.check_ticker(ticker, update.effective_user.id):
                db.delete_subscribed_ticker(
                    ticker,
                    update.effective_user.name,
                    update.effective_user.id
                )
                sub_tickers.append(ticker)
            else:
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"Тикер {ticker} не найден в подписке.",
                )
        if sub_tickers:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"{', '.join(sub_tickers)} удалены из подписки",
            )
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Не указаны тикеры, запустите команду так: /del_subscribe <TIK> или так /subscribe <TIK> <TIK> <TIK>",
        )
        return


def subscribe_pf(update, context):
    if not db.check_user(update.effective_user.id):
        context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"Сначала нужно нажать /start"
        )
        return
    if context.args:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Для этой функции недоступны аргументы, запустите её без них.",
        )
        return
    if update.effective_user.id == 176549646:
        tinkoff.subscribe_portfolio(
            tinkoff.get_portfolio(update.effective_user.id),
            update.effective_user.name,
            update.effective_user.id
        )
        context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"Подписка на портфель оформлена"
        )
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Эта функция, к сожалению не доступна для вас.",
        )


def unsubscribe_pf(update, context):
    if not db.check_user(update.effective_user.id):
        context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"Сначала нужно нажать /start"
        )
        return
    if context.args:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Для этой функции недоступны аргументы, запустите её без них.",
        )
        return
    if update.effective_user.id == 176549646:
        tinkoff.delete_subscribe_portfolio(
            tinkoff.get_portfolio(update.effective_user.id),
            update.effective_user.name,
            update.effective_user.id
        )
        context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"Подписка на портфель отключена"
        )
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Эта функция, к сожалению не доступна для вас.",
        )


def show_subscribe(update, context):
    if not db.check_user(update.effective_user.id):
        context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"Сначала нужно нажать /start"
        )
        return
    header = ["Тикер", "Название"]
    if context.args:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Для этой функции недоступны аргументы, запустите её без них.",
        )
        return
    subscribe_list = db.show_list_of_subscribes(update.effective_user.name, update.effective_user.id)
    if subscribe_list:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            parse_mode="Markdown",
            text=f"`{tabulate(subscribe_list, headers=header, tablefmt='pipe', stralign='left')}`",
        )
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Ваш список на подписку пуст. Добавьте что-нибудь при помощи /subscribe",
        )


def show_ticker(update, context):
    if not db.check_user(update.effective_user.id):
        context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"Сначала нужно нажать /start"
        )
        return
    if context.args:
        for ticker in context.args:
            try:
                rez = tinkoff.show_brief_ticker_info_by_id(ticker, update.effective_user.id)
            except ValueError:
                context.bot.send_message(
                    chat_id=update.effective_chat.id, text=f"Тикер {ticker} не найден."
                )
                return
            message = f"""*Тикер*: {rez['ticker']}
*Имя*: {rez['name']}
*Последняя цена*: {rez['last_price']}
*Текущаяя цена*: {rez['curr_price']}
*Разница*: {rez['diff']}
#{rez['link']}"""
            context.bot.send_message(
                chat_id=update.effective_chat.id, parse_mode="Markdown", text=message
            )
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Не указаны тикеры, запустите команду так: /show_ticker <TIK> или так /show_ticker <TIK> <TIK> <TIK>",
        )


def unknown(update, context):
    logger.info(
        f"{update.effective_user.name} ({update.effective_user.id}) sent unknown command: {update.message.text}"
    )
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Такой команды нет, выбери нужную команду из списка.",
    )


def unknown_text(update, context):
    logger.info(
        f"{update.effective_user.name} ({update.effective_user.id}) sent unknown command: {update.message.text}"
    )
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Допускаются только команды /.",
    )


start_handler = CommandHandler("start", start)
dispatcher.add_handler(start_handler)

subscribe_handler = CommandHandler("subscribe", subscribe)
dispatcher.add_handler(subscribe_handler)

subscribe_pf_handler = CommandHandler("subscribe_pf", subscribe_pf)
dispatcher.add_handler(subscribe_pf_handler)

del_subscribe_handler = CommandHandler("unsubscribe", unsubscribe)
dispatcher.add_handler(del_subscribe_handler)

del_subscribe_pf_handler = CommandHandler("unsubscribe_pf", unsubscribe_pf)
dispatcher.add_handler(del_subscribe_pf_handler)

show_subscribe_handler = CommandHandler("show_subscribe", show_subscribe)
dispatcher.add_handler(show_subscribe_handler)

show_ticker_handler = CommandHandler("show_ticker", show_ticker)
dispatcher.add_handler(show_ticker_handler)

unknown_command_handler = MessageHandler(
    Filters.command, unknown
)  # Если приходит команда, которую не знаем - пускаем функцию unknown
dispatcher.add_handler(unknown_command_handler)

unknown_text_handler = MessageHandler(
    Filters.text, unknown_text
)  # Отвечаем на любые не команды
dispatcher.add_handler(unknown_text_handler)


# async def main():
#    await asyncio.gather(interval_polling(), interval_news())


# def run ():
#    asyncio.new_event_loop().run_until_complete(main())


if __name__ == "__main__":
    # run()
    updater.start_polling()
    # print (db.check_user('176549646')) -> True

