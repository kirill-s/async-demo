import asyncio
from aiohttp import web

async def handle(request):
    index = open("index.html", 'rb')
    content = index.read()
    return web.Response(body=content)


async def wshandler(request):
    app = request.app
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    if app["game_cycle"] is None or \
       app["game_cycle"].cancelled():
        app["game_cycle"] = asyncio.ensure_future(game_cycle(app))
    app["sockets"].append(ws)
    while 1:
        msg = await ws.receive()
        if msg.tp == web.MsgType.text:
            ws.send_str("Hello, {}".format(msg.data))
            print("Got message %s" % msg.data)
        elif msg.tp == web.MsgType.close:
            app["sockets"].remove(ws)
            if len(app["sockets"]) == 0:
                app["game_cycle"].cancel()
            print("Closed connection")
            break

    return ws

async def game_cycle(app):
    print("Game cycle started")
    while 1:
        for ws in app["sockets"]:
            ws.send_str("game cycle passed")
        await asyncio.sleep(2)


app = web.Application()

app["sockets"] = []
app["game_cycle"] = None

app.router.add_route('GET', '/echo', wshandler)
app.router.add_route('GET', '/', handle)

web.run_app(app)
