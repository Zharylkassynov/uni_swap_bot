import asyncio
import os
import signal
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiohttp import web, ClientSession

from config import BOT_TOKEN
from handlers import router


async def healthcheck(request):
    return web.Response(text="OK")


async def ping_endpoint(request):
    """Endpoint для внешних ping сервисов"""
    return web.Response(text="PONG", status=200)


async def start_web_server():
    """Запускает веб-сервер"""
    app = web.Application()
    app.router.add_get("/", healthcheck)
    app.router.add_get("/ping", ping_endpoint)
    app.router.add_get("/health", healthcheck)

    runner = web.AppRunner(app)
    await runner.setup()

    # Render автоматически устанавливает переменную PORT
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    print(f"🌐 Web server started on port {port} (from PORT env: {os.environ.get('PORT', 'not set')})")
    
    # Ждем бесконечно, чтобы сервер работал
    try:
        await asyncio.Future()  # Бесконечное ожидание
    except asyncio.CancelledError:
        pass
    finally:
        await runner.cleanup()


async def keep_alive_ping():
    """
    Периодически делает запрос к healthcheck endpoint через внешний URL,
    чтобы сервер на Render.com не засыпал.
    
    На Render.com бесплатные инстансы засыпают после 15 минут неактивности.
    Поэтому делаем запросы каждые 10 минут.
    """
    # Получаем внешний URL из переменной окружения или используем localhost
    external_url = os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("RENDER_URL")
    
    if not external_url:
        # Если нет внешнего URL, пробуем использовать localhost (но это не поможет на Render)
        port = int(os.environ.get("PORT", 10000))
        ping_url = f"http://localhost:{port}/health"
        print(f"⚠️ RENDER_EXTERNAL_URL не установлен, используем localhost (может не работать на Render)")
    else:
        # Убираем слэш в конце, если есть
        external_url = external_url.rstrip('/')
        ping_url = f"{external_url}/health"
        print(f"🌐 Используем внешний URL для keep-alive: {ping_url}")
    
    while True:
        try:
            # Ждем 10 минут (600 секунд) - меньше чем 15 минут засыпания Render
            await asyncio.sleep(300)
            
            async with ClientSession() as session:
                try:
                    async with session.get(ping_url, timeout=10) as response:
                        if response.status == 200:
                            text = await response.text()
                            print(f"✅ Keep-alive ping successful: {text}")
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
    # Создаем бота с правильными настройками
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    dp.include_router(router)

    # Запускаем веб-сервер в фоне
    web_server_task = asyncio.create_task(start_web_server())
    
    # Даем серверу немного времени на запуск
    await asyncio.sleep(2)
    
    # Запускаем keep-alive ping в фоне
    keep_alive_task = asyncio.create_task(keep_alive_ping())
    
    print("🤖 Bot starting...")
    
    try:
        # Запускаем polling с правильной обработкой остановки
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            close_bot_session=True
        )
    except Exception as e:
        print(f"❌ Error in polling: {e}")
        raise
    finally:
        print("🛑 Shutting down...")
        # Отменяем задачи при завершении
        keep_alive_task.cancel()
        web_server_task.cancel()
        
        # Закрываем сессию бота
        await bot.session.close()
        
        try:
            await keep_alive_task
        except asyncio.CancelledError:
            pass
        try:
            await web_server_task
        except asyncio.CancelledError:
            pass
        
        print("✅ Shutdown complete")


def signal_handler(sig, frame):
    """Обработчик сигналов для graceful shutdown"""
    print(f"\n⚠️ Received signal {sig}, shutting down gracefully...")
    sys.exit(0)


if __name__ == "__main__":
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
