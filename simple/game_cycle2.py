import asyncio
from aiohttp import web

async def handle(request):
    index = open("index.html", 'rb')
    content = index.read()
    return web.Response(body=content)


async def wshandler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    recv_task = None
    cycle_task = None
    cycle_end = request.app["cycle_end"]
    while 1:
        if not recv_task:
            recv_task = asyncio.ensure_future(ws.receive())
        if not cycle_task:
            await cycle_end.acquire()
            cycle_task = asyncio.ensure_future(cycle_end.wait())

        done, pending = await asyncio.wait(
            [recv_task,
             cycle_task],
            return_when=asyncio.FIRST_COMPLETED)

        if recv_task in done:
            msg = recv_task.result()
            if msg.tp == web.MsgType.text:
                ws.send_str("Hello, {}".format(msg.data))
                print("Got message %s" % msg.data)
            elif msg.tp == web.MsgType.close:
                print("Closed connection")
                break
            recv_task = None

        if cycle_task in done:
            ws.send_str("game cycle passed")
            print("game cycle passed")
            cycle_end.release()
            cycle_task = None

    return ws

async def game_cycle(app):
    cycle_end = app["cycle_end"]
    while 1:
        await asyncio.sleep(1)
        await cycle_end.acquire()
        cycle_end.notify_all()
        cycle_end.release()



app = web.Application()

app["cycle_end"] = asyncio.Condition()
asyncio.ensure_future(game_cycle(app))

app.router.add_route('GET', '/echo', wshandler)
app.router.add_route('GET', '/', handle)

web.run_app(app)
