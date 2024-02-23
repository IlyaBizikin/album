import logging
import os
from tempfile import mkstemp
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from PIL import Image
from fpdf import FPDF
import io

TOKEN = "6763145931:AAEXn-mXsusS0XDG-ZdH3jGRFkJaZOsb5-Q"
bot = Bot(token=TOKEN)
dp = Dispatcher(bot=bot)

logging.basicConfig(level=logging.INFO)

user_images = {}

A4_SIZE = (2480, 3508)


class PDF(FPDF):
    def __init__(self, orientation='P', unit='mm', format='A4'):
        super().__init__(orientation, unit, format)


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(KeyboardButton("Создать альбом"))
    await message.reply("Привет! Отправь мне фото, и я создам из них фотоальбом.", reply_markup=markup)


@dp.message_handler(content_types=['photo'])
async def handle_docs_photo(message: types.Message):
    global user_images

    user_id = message.from_user.id
    if user_id not in user_images:
        user_images[user_id] = []

    photo_bytes = io.BytesIO()
    await message.photo[-1].download(destination_file=photo_bytes)
    user_images[user_id].append(photo_bytes)

    await message.reply("Фото добавлено!")


@dp.message_handler(lambda message: message.text == "Создать альбом")
async def create_album(message: types.Message):
    user_id = message.from_user.id

    if user_id not in user_images or len(user_images[user_id]) == 0:
        await message.reply("Сначала отправь мне фото!")
        return

    pdf = PDF()

    for photo_bytes in user_images[user_id]:
        photo_bytes.seek(0)
        img = Image.open(photo_bytes)
        img = img.resize(A4_SIZE, Image.Resampling.LANCZOS)
        pdf.add_page()

        fd, tmpfilepath = mkstemp(suffix=".jpg")
        os.close(fd)

        try:
            img.save(tmpfilepath, format="JPEG")
            pdf.image(tmpfilepath, x=0, y=0, w=210, h=297)
        except FileNotFoundError:
            print('Ошибка! Файл не существует')
        finally:
            os.remove(tmpfilepath)

    pdf_content = pdf.output(dest='S').encode('latin1')
    pdf_output = io.BytesIO(pdf_content)

    await bot.send_document(user_id, ('album.pdf', pdf_output))
    await message.reply("Ваш PDF альбом готов!")

    del user_images[user_id]


if __name__ == '__main__':
    executor.start_polling(dp)
