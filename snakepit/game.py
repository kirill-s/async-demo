from random import randint
import json

import settings
from player import Player


class Game:

    def __init__(self):
        self._last_id = 0
        self._colors = list(range(0, settings.MAX_PLAYERS))
        self._players = {}
        self._disconnected = []
        self._world = []
        self.create_world()

    def create_world(self):
        for y in range(0, settings.FIELD_SIZE_Y):
            self._world.append([(" ", 0)] * FIELD_SIZE_X)

    def new_player(self, name, ws):
        self._last_id += 1
        player_id = self._last_id

        self._send_personal(ws, "world", json.dumps(self._world))
        player = Player(ws)
        self._players[player_id] = player
        return player_id

    def join(self, player_id):
        if len(self._colors) == 0:
            self._send_personal(ws, "error", "Maximum players reached")
            return
        color = self._colors(randint(0, len(self._colors)))
        self._colors.remove(color)
        self._players[player_id].join(color)
        self._send_all("p_join", player_id, name)

    def player_keypress(player_id, keycode):
        self._players[player_id].keypress(keycode)

    def game_over(self, player_id):
        self._players[player_id].alive = False
        self._send_all("p_gameover", player_id)
        color = self._players[player_id].color
        self._colors.append(color)

    def player_disconnect(self, player_id):
        p = self._players[player_id]
        if p.alive:
            self.game_over(player_id)
            render = p.render_game_over()
            self._send_all_render(render)
        del p, self._players[player_id]

    def any_alive_players(self):
        return any([p.alive for p in self._players.values()])

    def end_turn(self):
        messages = []
        render_all = []
        for p_id, p in self._players.items():

            if not p.alive:
                continue
            # check if snake already exists
            elif len(p.snake):
                # check next position's content
                pos = p.next_position()
                # check bounds
                if p.x < 0 or p.x >= settings.FIELD_SIZE_X or\
                   p.y < 0 or p.y >= settings.FIELD_SIZE_Y:
                    self.game_over(p_id)
                    render_all += p.render_game_over()
                    continue

                char = self.world[pos.y, pos.x].char
                grow = 0
                if char.isdigit():
                    # start growing next turn in case we eaten a digit
                    grow = int(char)
                    p.score += grow
                    messages = ["score", p_id, p.score]
                elif char != " ":
                    self.game_over(p_id)
                    render_all += p.render_game_over()
                    continue

                render_all = p.render_move()
                p.grow = grow
            else:
                # newborn snake
                render_all = p.render_new_snake()

        # send all render messages
        self._send_all_render(render_all)
        # send additional messages
        if messages:
            self._send_all_multi(messages)


    def _send_all_render(self, render):
        messages = []
        for r in render:
            messages.append(["r"] + list(r))
        self._send_all_multi(messages)

    def _send_personal(self, ws, *args):
        msg = json.dumps([args])
        ws.send_str(msg)

    def _send_all(self, *args):
        self._send_all_multi([args])

    def _send_all_multi(self, commands):
        msg = json.dumps(commands)
        for player in self._players.values():
            if player.ws:
                player.ws.send_str(msg)

