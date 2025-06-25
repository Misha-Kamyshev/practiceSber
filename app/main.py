import asyncio

from app.handle.handle import router
from app.static import dp, bot


async def main():
    dp.include_router(router)
    await asyncio.gather(dp.start_polling(bot))


if __name__ == '__main__':
    asyncio.run(main())
