import aiohttp


class TokenMetadataFetcher:
    @staticmethod
    async def fetch_metadata(uri):
        async with aiohttp.ClientSession() as session:
            async with session.get(uri) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None
