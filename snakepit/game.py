from random import randint
import json

import settings
from player import Player
from datatypes import Char, Draw


class Game:

    def __init__(self):
        self._last_id = 0
        self._colors = []
        self._players = {}
        self._world = []
        self.create_world()

    def create_world(self):
        for y in range(0, settings.FIELD_SIZE_Y):
            self._world.append([Char(" ", 0)] * settings.FIELD_SIZE_X)

    def new_player(self, name, ws):
        self._last_id += 1
        player_id = self._last_id
        self._send_personal(ws, "handshake", name, player_id)

        self._send_personal(ws, "world", self._world)
        player = Player(player_id, name, ws)
        self._players[player_id] = player
        return player

    def join(self, player):
        if player.alive:
            return
        if self.count_alive_players() == settings.MAX_PLAYERS:
            self._send_personal(ws, "error", "Maximum players reached")
            return
        # pick a color, try to have all different colors
        if not len(self._colors):
            self._colors = list(range(0, settings.NUM_COLORS))
        color = self._colors[randint(0, len(self._colors) - 1)]
        self._colors.remove(color)
        # init snake
        player.new_snake(color)
        # notify all about new player
        self._send_all("p_joined", player._id, player.name, color)

    def game_over(self, player):
        player.alive = False
        self._send_all("p_gameover", player._id)
        self._colors.append(player.color)

    def player_disconnected(self, player):
        player.ws = None
        if player.alive:
            self.game_over(player)
            render = player.render_game_over()
            self.apply_render(render)
        del self._players[player._id]
        del player

    def count_alive_players(self):
        return sum([int(p.alive) for p in self._players.values()])

    def next_frame(self):
        messages = []
        render_all = []
        for p_id, p in self._players.items():

            if not p.alive:
                continue
            # check if snake already exists
            if len(p.snake):
                # check next position's content
                pos = p.next_position()
                # check bounds
                if pos.x < 0 or pos.x >= settings.FIELD_SIZE_X or\
                   pos.y < 0 or pos.y >= settings.FIELD_SIZE_Y:
                    self.game_over(p)
                    render_all += p.render_game_over()
                    continue

                char = self._world[pos.y][pos.x].char
                grow = 0
                if char.isdigit():
                    # start growing next turn in case we eaten a digit
                    grow = int(char)
                    p.score += grow
                    messages.append(["score", p_id, p.score])
                elif char != " ":
                    self.game_over(p)
                    render_all += p.render_game_over()
                    continue

                render_all += p.render_move()
                p.grow += grow
            else:
                # newborn snake
                render_all += p.render_new_snake()

        render_all += self.spawn_objects()

        # send all render messages
        self.apply_render(render_all)
        # send additional messages
        if messages:
            self._send_all_multi(messages)

    def spawn_objects(self):
        render = []
        if randint(1, 100) <= settings.DIGIT_SPAWN_RATE:
            char = str(randint(1,9))
            x = randint(0, settings.FIELD_SIZE_X - 1)
            y = randint(0, settings.FIELD_SIZE_Y - 1)
            color = randint(0, settings.NUM_COLORS)
            render += [Draw(x, y, char, color)]
        #if randint(1, 100) <= settings.STONE_SPAWN_RATE:
        #    render += [Draw(x, y, '#', 0)]
        return render


    def apply_render(self, render):
        messages = []
        for draw in render:
            # apply to local
            self._world[draw.y][draw.x] = Char(draw.char, draw.color)
            # send messages
            messages.append(["r"] + list(draw))
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

