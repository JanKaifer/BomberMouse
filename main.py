import websocket
import json
from collections import deque as deqeue
from time import time

bombs = []

config = {}


def print_board(board):
    for line in board:
        print("".join(line))


def get_bomb_score(board, x, y):
    global config
    score = 0
    agg = 3
    for _x in range(1,config["turns_to_explode"]):
        if board[x + _x][y] == 'P':
            score += agg
        if board[x + _x][y] == '.':
            score += 1
            break
        elif board[x + _x][y] == '#':
            break

    for _x in range(1,config["turns_to_explode"]):
        if board[x - _x][y] == 'P':
            score += agg
        if board[x - _x][y] == '.':
            score += 1
            break
        elif board[x - _x][y] == '#':
            break

    for _y in range(1,config["turns_to_explode"]):
        if board[x][y + _y] == 'P':
            score += agg
        if board[x][y + _y] == '.':
            score += 1
            break
        elif board[x][y + _y] == '#':
            break

    for _y in range(1,config["turns_to_explode"]):
        if board[x][y - _y] == 'P':
            score += agg
        if board[x][y - _y] == '.':
            score += 1
            break
        elif board[x][y - _y] == '#':
            break

    return score


def zab_bo(board, x, y, radius, x1, y1):
    if x == x1:
        if y == y1:
            return True
        if y < y1:
            if y1 - y >= radius:
                return False
            while y < y1:
                y += 1

                if board[x][y] in '#.':
                    return False
            return True

        if y > y1:
            if y - y1 >= radius:
                return False
            while y > y1:
                y -= 1

                if board[x][y] in '#.':
                    return False
            return True

    if y == y1:
        if x < x1:
            if x1 - x >= radius:
                return False
            while x < x1:
                x += 1

                if board[x][y] in '#.':
                    return False
            return True

        if x > x1:
            if x - x1 >= radius:
                return False
            while x > x1:
                x -= 1

                if board[x][y] in '#.':
                    return False
            return True


directions = {
    (0, -1): "up",
    (1, 0): "right",
    (0, 1): "down",
    (-1, 0): "left"
}

depth = 5
last = "down"


def on_message(ws, message):
    global config
    global last
    try:
        print("### start ###")
        recieved = time()
        state = json.loads(message)
        if 'points_per_wall' in state:
            # první zpráva obsahuje konfiguraci, ne stav hry
            config = state
            return

        print("Config:", config)
        if not state['Alive']:
            print("Chcípnul jsem")
            ws.close()
            return

        board = list(map(list, state["Board"]))
        #print("players", state["Players"])
        for player in state["Players"]:
            if board[player["LastX"]][player["LastY"]] == "B" and player["Alive"]:
                bombs.append((player["LastX"], player["LastY"], state["Turn"] - 1, player["Radius"]))

        i = 0
        while i < len(bombs):
            bomb = bombs[i]
            if board[bomb[0]][bomb[1]] == " ":
                del bombs[i]
            else:
                i += 1

        #print_board(board)

        X, Y = state['X'], state['Y']
        print("Position:", X, Y)

        front = deqeue([(X, Y, 0, 0, [], [])])
        best = ""
        best_score = -1000

        print("Turn:", state["Turn"])
        print("Bombs:", bombs)
        while front:
            #print(front)
            x, y, dist, score, new_bombs, action = front.popleft()
            print("\t\t>", x, y, dist, score, new_bombs, action)
            if dist >= depth:
                if score > best_score:
                    best_score = score
                    best = action[0]
                print("\t<-- Reached.")
                continue

            for direction in directions:
                if board[x + direction[0]][y + direction[1]]:
                    valid = True
                    for bomb in bombs:
                        if bomb[3] + config["turns_to_explode"] <= state["Turn"]+dist <= bomb[3] + config["turns_to_explode"] + \
                                config["turns_to_flameout"]:
                            valid = valid and zab_bo(board, bomb[0], bomb[1], bomb[3], x + direction[0], y + direction[1])
                            if not valid:
                                break

                    if valid and board[x + direction[0]][y + direction[1]] in "P ":
                        action += [directions[direction]]

                        front.append((x + direction[0], y + direction[1], dist + 1, score, new_bombs[:], action[:]))
                        print("-->", directions[direction])

            if (x, y) not in new_bombs and (last != "bomb" or dist):
                action += ["bomb"]
                front.append((x, y, dist + 1, score + get_bomb_score(board, x, y), new_bombs[:] + [(x, y)], action[:]))
                print("--> bomb")

        print("Time:", time()-recieved)
        print("Best:", best)
        ws.send(best)
        last = best
        #exit(1)

    except Exception as e:
        print(e)
        pass


def on_error(ws, error):
    print(error)


def on_close(ws):
    print("### closed ###")


auth_string = "player1:1111"


def on_open(ws):
    ws.send(auth_string)


ws = websocket.WebSocketApp(
    "ws://192.168.1.100:8002/",
    on_message=on_message,
    on_error=on_error,
    on_close=on_close,
    on_open=on_open
)
ws.run_forever()
