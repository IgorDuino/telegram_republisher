from tortoise import Tortoise, run_async

import settings

from multiprocessing import Process


def run_pyrogram():
    import userbot


def run_flask():
    import web


if __name__ == "__main__":
    pyrogram_process = Process(target=run_pyrogram)
    flask_process = Process(target=run_flask)

    try:
        pyrogram_process.start()
        flask_process.start()

        pyrogram_process.join()
        flask_process.join()

    except KeyboardInterrupt:
        pyrogram_process.terminate()
        flask_process.terminate()
        pyrogram_process.join()
        flask_process.join()
