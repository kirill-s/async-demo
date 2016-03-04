import asyncio
from aiohttp import web

async def handle(request):
    index = open("index.html", 'rb')
    content = index.read()
    return web.Response(body=content)

async def wshandler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    while 1:
        msg = await ws.receive()
        if msg.tp == web.MsgType.text:
            ws.send_str("Hello, {}".format(msg.data))
            print("Got message %s" % msg.data)
        elif msg.tp == web.MsgType.close:
            print("Closed connection")
            break

    return ws


app = web.Application()

app.router.add_route('GET', '/echo', wshandler)
app.router.add_route('GET', '/', handle)

web.run_app(app)
