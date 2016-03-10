import asyncio
import json
from aiohttp import web

import settings
from game import Game

async def handle(request):
    ALLOWED_FILES = ["index.html", "style.css"]

    name = request.match_info.get('name')
    if not name:
        name = "index.html"
    if name not in ALLOWED_FILES:
        return web.Response(status=404)
    try:
        with open(name, 'rb') as index:
            content = index.read()
    except:
        return web.Response(status=404)
    return web.Response(body=content)


async def wshandler(request):
    print("Connected")
    app = request.app
    game = app["game"]
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    player = None
    while 1:
        msg = await ws.receive()
        if msg.tp == web.MsgType.text:
            print("Got message %s" % msg.data)

            data = json.loads(msg.data)
            if type(data) == int and player:
                # Interpret as key code
                player.keypress(data[0])
            if type(data) != list:
                continue
            if not player:
                if data[0] == "new_player":
                    player = game.new_player(data[1], ws)
            elif data[0] == "join":
                if app["game_cycle"] is None or \
                   app["game_cycle"].cancelled():
                    app["game_cycle"] = asyncio.ensure_future(game_cycle(app))
                    print("Starting game cycle")
                game.join(player)

        elif msg.tp == web.MsgType.close:
            break

    if player:
        game.player_disconnected(player)
    if app["game_cycle"] and\
       not app["game_cycle"].cancelled() and\
       not game.count_alive_players():
        app["game_cycle"].cancel()
        print("Stopping game cycle")
    print("Closed connection")
    return ws

async def game_cycle(app):
    while 1:
        app["game"].end_turn()
        if not game.count_alive_players():
            app["game_cycle"].cancel()
        await asyncio.sleep(1./settings.GAME_SPEED)


app = web.Application()

app["game"] = Game()
app["game_cycle"] = None

app.router.add_route('GET', '/connect', wshandler)
app.router.add_route('GET', '/{name}', handle)
app.router.add_route('GET', '/', handle)

web.run_app(app)
