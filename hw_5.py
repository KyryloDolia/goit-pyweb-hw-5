import sys
from datetime import datetime, timedelta
import httpx
import asyncio
import platform
import json

class HttpError(Exception):
    pass

async def request(url: str):
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(url, timeout=10)
            if r.status_code == 200:
                result = r.json()
                return result
            else:
                raise HttpError(f"Error status: {r.status_code} for {url}")
        except httpx.ReadTimeout:
            print(f"Timeout occurred while trying to reach {url}")
            return None
        except httpx.RequestError as e:
            print(f"An error occurred while requesting {url}: {e}")
            return None


async def fetch_rates(days):
    rates = []
    days = int(days)

    for index_day in range(days):
        d = datetime.now() - timedelta(days=index_day)
        shift = d.strftime("%d.%m.%Y")
        print(f"Fetching rates for: {shift}")

        response = await request(f'https://api.privatbank.ua/p24api/exchange_rates?date={shift}')
        if response is None:
            print(f"No response received for {shift}. Skipping...")
            continue

        if 'exchangeRate' in response:
            exchange_rates = {shift: {}}
            for rate in response['exchangeRate']:
                if rate['currency'] in ['EUR', 'USD']:
                    exchange_rates[shift][rate['currency']] = {
                        'sale': rate.get('saleRateNB'),
                        'purchase': rate.get('purchaseRateNB')
                    }
            rates.append(exchange_rates)
        else:
            print(f"No exchange rates found for {shift}")

    return rates


async def main(days):
    if int(days) > 10:
        print("Error: You can only retrieve data for a maximum of 10 days.")
        return None

    rates = await fetch_rates(days)
    return rates


if __name__ == '__main__':
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        days_requested = sys.argv[1]
        results = asyncio.run(main(days_requested))
        print(json.dumps(results, indent=4, ensure_ascii=False))
    except (IndexError, ValueError):
        print("Usage: python main.py <number_of_days>")
