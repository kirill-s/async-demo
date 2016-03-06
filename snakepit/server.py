import asyncio
import json
from aiohttp import web

import settings
from game import Game

async def handle(request):
    name = request.match_info.get('name')
    if not name:
        name = "index.html"
    if name not in ["index.html", "style.css"]:
        return web.Response(status=404)
    try:
        with open(name, 'rb') as index:
            content = index.read()
    except:
        return web.Response(status=404)
    return web.Response(body=content)


async def wshandler(request):
    app = request.app
    game = app["game"]
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    player_id = None
    while 1:
        msg = await ws.receive()
        if msg.tp == web.MsgType.text:
            print("Got message %s" % msg.data)
            data = json.loads(msg.data)
            if not player_id:
                if data[0] == "name":
                    player_id = game.add_player(data[1], ws)
            elif data[0] == "join":
                if app["game_cycle"] is None or \
                   app["game_cycle"].cancelled():
                    app["game_cycle"] = asyncio.ensure_future(game_cycle(app))
                    print("Starting game cycle")
                game.join(player_id)
            else:
                # Interpret as key code
                game.player_keypress(player_id, data[0])

        elif msg.tp == web.MsgType.close:
            game.player_disconnect(player_id)
            if not game.any_alive_players():
                app["game_cycle"].cancel()
                print("Stopping game cycle")
            print("Closed connection")
            break

    return ws

async def game_cycle(app):
    while 1:
        app["game"].end_turn()
        if not game.any_alive_players():
            app["game_cycle"].cancel()
        await asyncio.sleep(1./settings.GAME_SPEED)


app = web.Application()

app["game"] = Game()
app["game_cycle"] = None

app.router.add_route('GET', '/echo', wshandler)
app.router.add_route('GET', '/{name}', handle)
app.router.add_route('GET', '/', handle)

web.run_app(app)
