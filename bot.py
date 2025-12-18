import asyncio
import os
from aiogram import Bot, Dispatcher
from aiohttp import web

from config import BOT_TOKEN
from handlers import router


async def healthcheck(request):
    return web.Response(text="OK")


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", healthcheck)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()


async def main():
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    await asyncio.gather(
        dp.start_polling(bot),
        start_web_server()
    )


if __name__ == "__main__":
    asyncio.run(main())
