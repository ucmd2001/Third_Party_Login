import asyncio
import time
 
now = lambda: time.time()
 
async def dosomething(num):
    print('第 {} 任務，第一步'.format(num))
    await asyncio.sleep(2)
    print('第 {} 任務，第二步'.format(num))
 
if __name__ == "__main__":
    start = now()
    tasks = [dosomething(i) for i in range(5)]
    asyncio.run(asyncio.wait(tasks))
    print('TIME: ', now() - start)