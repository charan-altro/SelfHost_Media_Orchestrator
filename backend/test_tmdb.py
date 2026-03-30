import asyncio
import httpx

async def test():
    client = httpx.AsyncClient()
    headers = {
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJlNjhiNzRjZjcwOTU2OGNhZDJlOTY2MTJiYThkNzQxNiIsIm5iZiI6MTc2Nzg3NTc2OS45MDcsInN1YiI6IjY5NWZhNGI5OTUyZGQ1NDUyYTNkYWY4NyIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.Ff4Hk53g8sJ8tDErjB1CU6GYClaaXx_qHqqwYyfWbkA',
        'Accept': 'application/json'
    }
    resp = await client.get('https://api.tmdb.org/3/search/movie?query=The%20Matrix', headers=headers)
    print("STATUS:", resp.status_code)
    print("RESPONSE:", resp.text)

asyncio.run(test())
