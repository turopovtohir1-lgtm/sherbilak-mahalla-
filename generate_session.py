import asyncio
from pyrogram import Client

# Ushbu skript faqat mahalliy kompyuterda bir marta ishga tushiriladi
# va olingan 'String Session' ni Railway ENV ga qo'shasiz.

async def main():
    api_id = input("API_ID kiriting: ")
    api_hash = input("API_HASH kiriting: ")
    
    async with Client(":memory:", api_id=int(api_id), api_hash=api_hash) as app:
        session_string = await app.export_session_string()
        print("\n" + "="*50)
        print("Sizning STRING_SESSION kodingiz (buni nusxalab oling):")
        print("="*50 + "\n")
        print(session_string)
        print("\n" + "="*50)

if __name__ == "__main__":
    asyncio.run(main())
