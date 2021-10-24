#TODO parse openings from pgn key 

import requests
import logging
from chessdotcom import get_player_stats, get_player_game_archives
import pprint
import pandas as pd
import re

from hashlib import md5

#====================================================================================================

def INFO(str):
    print(f"[INFO]     {str}")

#====================================================================================================

def WARN(str):
    print(f"[WARN]     {str}")

#====================================================================================================

def ERROR(str):
    print(f"[ERROR]     {str}")

#====================================================================================================

def get_game_archives(user_name):
    return f"https://api.chess.com/pub/player/{user_name}/games/archives"

#====================================================================================================

def get_opening_eco(pgn):
    "Get ECO code of opening (encyclopedia of chess openings) """

    # FIXME some validity checks needed

    '\[ECO \"[A-Z][0-9][0-9]\"\] should match the codes like: [ECO "A20"] '

    match = re.search('\[ECO \"[A-Z][0-9][0-9]\"\]', pgn)
    if match:
        code = match.group(0)
        # strip useless characters
        code = code[6:-2]
        return code
    else:
        return ""

#====================================================================================================


def main(args):

    # setup pretty printer
    printer = pprint.PrettyPrinter()

    # get json file of player monthly game archives
    user_name = args.user_name
    INFO(f"Retrieving games for user {user_name}")
    
    monthly_archives = requests.get(get_game_archives(user_name)).json()
    #printer.pprint(monthly_archives)

    # validity check, should be a dictionary with 1 key, "archives"
    if len(monthly_archives) != 1 and monthly_archives.keys() != ["archives"]:
        ERROR("Invalid data retrieved, not continuing")
        exit(1)

    # preparing to turn into dataframe
    game_url_hash, time_class, player_colour, opening, game_url, player_result, opponent_result = [], [], [], [], [], [], []

    # Each item in this list contains a URL, formatted like https://api.chess.com/pub/player/{user}/games/YYYY/MM
    # Loop over each, and retrieve the games
    for archive in monthly_archives["archives"]:
        # retrieve in json format, turn to pandas dataframe
        data = requests.get(archive).json()
        game_data = data["games"]
        #printer.pprint(games["games"][0])

        for game in game_data:

            # skip chess variants
            if game["rules"] != "chess":
                continue

            # check if user played as white or black
            user_colour = ""
            user_colour = "white" if game["white"]["username"] == user_name else "black"
            player_colour.append(user_colour)

            opponent_colour = "white" if player_colour == "black" else "black"

            if "accuracies" in game.keys():
                print(game["accuracies"][user_colour])

            time_class.append(game["time_class"])

            # save player and opponent result, player "win" can be because opponent resigned, flagged, abandoned, etc
            player_result.append(game[user_colour]["result"])
            opponent_result.append(game[opponent_colour]["result"])

            opening_name = ""
            try:
                opening_name = get_opening_eco(game["pgn"])
                opening.append(opening_name)
            except KeyError:
                opening_name = "Unknown"

            url = game["url"]
            url_hash = md5(url.encode("utf-8")).hexdigest()

            game_url.append(url)
            game_url_hash.append(url_hash)

    # save to dataframe
    game_dict = {
        "url_hash" : game_url_hash,
        "time_class" : time_class,
        "player_colour" : player_colour,
        "opening" : opening,
        "game_url" : game_url,
        "player_result" : player_result,
        "opponent_result" : opponent_result
    }

    game_df = pd.DataFrame(game_dict,
            columns = [
                "url_hash",
                "time_class",
                "player_colour",
                "opening",
                "game_url",
                "player_result",
                "opponent_result"
            ]
        )

    INFO("Finished retrieving data")

    print(game_df.head(20))


#====================================================================================================

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--user-name",         metavar = "USERNAME", type = str, help = "chess.com username", required = False, default = "sddish")
    args = parser.parse_args()
    main(args)
