import asyncio
import os
from aiogram import Bot, Dispatcher
from aiohttp import web, ClientSession

from config import BOT_TOKEN
from handlers import router


async def healthcheck(request):
    return web.Response(text="OK")


async def ping_endpoint(request):
    """Endpoint для внешних ping сервисов"""
    return web.Response(text="PONG", status=200)


async def start_web_server():
    """Запускает веб-сервер и возвращает порт"""
    app = web.Application()
    app.router.add_get("/", healthcheck)
    app.router.add_get("/ping", ping_endpoint)
    app.router.add_get("/health", healthcheck)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    print(f"🌐 Web server started on port {port}")
    
    # Ждем бесконечно, чтобы сервер работал
    try:
        await asyncio.Future()  # Бесконечное ожидание
    except asyncio.CancelledError:
        pass
    finally:
        await runner.cleanup()


async def keep_alive_ping(port: int):
    """
    Периодически делает запрос к healthcheck endpoint,
    чтобы сервер на Render.com не засыпал
    """
    while True:
        try:
            await asyncio.sleep(300)  # 5 минут = 300 секунд
            
            async with ClientSession() as session:
                try:
                    # Делаем запрос к localhost healthcheck
                    async with session.get(f"http://localhost:{port}/health", timeout=5) as response:
                        if response.status == 200:
                            print(f"✅ Keep-alive ping successful: {await response.text()}")
                        else:
                            print(f"⚠️ Keep-alive ping returned status: {response.status}")
                except Exception as e:
                    print(f"❌ Keep-alive ping error: {e}")
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"❌ Keep-alive loop error: {e}")
            await asyncio.sleep(60)  # Подождать минуту перед повтором при ошибке


async def main():
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    # Получаем порт из переменной окружения
    port = int(os.environ.get("PORT", 10000))
    
    # Запускаем веб-сервер в фоне
    web_server_task = asyncio.create_task(start_web_server())
    
    # Даем серверу немного времени на запуск
    await asyncio.sleep(1)
    
    # Запускаем keep-alive ping в фоне
    keep_alive_task = asyncio.create_task(keep_alive_ping(port))
    
    try:
        await asyncio.gather(
            dp.start_polling(bot),
            web_server_task,
        )
    finally:
        # Отменяем задачи при завершении
        keep_alive_task.cancel()
        web_server_task.cancel()
        try:
            await keep_alive_task
        except asyncio.CancelledError:
            pass
        try:
            await web_server_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    asyncio.run(main())
