import asyncio

from work_1.handle.handle import router
from work_1.static import dp, bot


async def main():
    dp.include_router(router)
    await asyncio.gather(dp.start_polling(bot))


if __name__ == '__main__':
    asyncio.run(main())
