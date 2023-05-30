from requests import get
from tonconnect.connector import Connector
from tonconnect.exceptions import BridgeException
from config import *
from time import time
import qrcode


def get_address(connector: Connector, nick: str, user_id: int) -> None:
    try:
        address = connector.get_address()
        f1 = open("wallets.csv")
        addresses = f1.read()
        f1.close()
        addresses = list(map(lambda x: x.split(';')[2], addresses.split('\n')[1:]))
        if address not in addresses:
            with open("wallets.csv", 'a') as f:
                f.write(f"\n{nick};{user_id};{address}")
    except BridgeException:
        print("TL")


# def get_swaps_dict() -> dict[str, tuple[str, str]]:
#     f = open("swap_streaks.csv")
#     swaps = {}
#     for elem in f.read().split('\n')[1:]:
#         elem = elem.split(';')
#         swaps[elem[0]] = (elem[1], elem[2])
#     f.close()
#     return swaps


qrcodes = 0


def ton_connect() -> tuple[str, int, Connector]:
    connector = Connector("https://raw.githubusercontent.com/ArkadiyStena/ds_bot_stonfi/main/tonconnect.json",
                          use_tonapi=True, tonapi_token=TON_API_KEY)
    url = connector.connect('tonkeeper', 'test')
    img = qrcode.make(url)
    global qrcodes
    qrcodes += 1
    img.save(f"qr{qrcodes}.png")
    return url, qrcodes, connector


def get_address(connector: Connector, nick: str, user_id: int) -> None:
    try:
        address = connector.get_address()
        with open("wallets.csv", 'a') as f:
            f.write(f"\n{nick};{user_id};{address}")
    except BridgeException:
        print("TL")
    except Exception as e:
        print(e)


def check_wallet(wallet: str) -> tuple[list[tuple[str, int]], dict[str, bool]]:
    base_url = f'https://tonapi.io/v2/accounts/{wallet}'
    possible_roles = [("Wallet Connect", ROLE_IDS["Wallet Connect"])]
    conditions = {}

    nfts = get(base_url + "/nfts?limit=1000&offset=0&indirect_ownership=true",
               headers=AUTH_HEADER).json()["nft_items"]
    nfts = list(map(lambda x: x["collection"]["address"], nfts))
    conditions["Hold [anti]glitch_1"] = (FIRST_COLLECTION in nfts)
    conditions["Hold [anti]glitch_2"] = (SECOND_COLLECTION in nfts)
    conditions["Hold TON Punk"] = (PUNKS_COLLECTION in nfts)

    # swaps, is_old = check_swaps(wallet)
    # conditions["Make a swap today"] = bool(swaps)
    # conditions["Have at least 10 transactions more than one week ago"] = is_old

    june_swapped_amount = check_swaps_for_period(wallet, JUNE, JULY)
    conditions["100 June"] = june_swapped_amount >= 100
    conditions["1 000 June"] = june_swapped_amount >= 1000
    conditions["10 000 June"] = june_swapped_amount >= 10000
    conditions["100 000 June"] = june_swapped_amount >= 100000

    # ton_balance = get(base_url,  headers=AUTH_HEADER).json()["balance"] / 1000000000
    # conditions["Have more than 1 TON"] = ton_balance >= 1

    if conditions["Hold [anti]glitch_1"]:
        possible_roles.append(("[anti]glitch_1 holder", ROLE_IDS["[anti]glitch_1 holder"]))
    if conditions["Hold [anti]glitch_2"]:
        possible_roles.append(("[anti]glitch_2 holder", ROLE_IDS["[anti]glitch_2 holder"]))
    if conditions["Hold TON Punk"]:
        possible_roles.append(("TON Punks Holder", ROLE_IDS["TON Punks Holder"]))

    if conditions["100 June"]:
        possible_roles.append(("1 000 June", ROLE_IDS["1 000 June"]))
    if conditions["1 000 June"]:
        possible_roles.append(("1 000 June", ROLE_IDS["1 000 June"]))
    if conditions["10 000 June"]:
        possible_roles.append(("10 000 June", ROLE_IDS["10 000 June"]))

    return possible_roles, conditions


def check_swaps_for_period(wallet: str, start_time: int, end_time: int) -> float:
    params = {
        'limit': '1000',
        'start_date': start_time,
        'end_date': end_time
    }
    url = f'https://tonapi.io/v2/accounts/{wallet}/events'
    swapped_amount = 0

    for k in range(3):
        res = get(url, params=params, headers=AUTH_HEADER).json()
        events, next_from = res["events"], res["next_from"]
        length = len(events)

        for i in range(length):
            actions = events[i]["actions"]
            if len(actions) == 2 and actions[0]["type"] == "JettonTransfer":
                transfer1 = actions[0]["JettonTransfer"]
                if transfer1["recipient"]["address"] != STONFI_ADDRESS_1:
                    continue
                if actions[1]["type"] == "JettonTransfer":
                    transfer2 = actions[1]["JettonTransfer"]
                    if transfer2["sender"]["address"] != STONFI_ADDRESS_1:
                        continue
                    if transfer1["jetton"]["symbol"] == "pTON":
                        swapped_amount += int(transfer1["amount"]) / 10 ** 9
                    elif transfer2["jetton"]["symbol"] == "pTON":
                        swapped_amount += int(transfer2["amount"]) / 10 ** 9
                elif actions[1]["type"] == "TonTransfer":
                    transfer2 = actions[1]["TonTransfer"]
                    if transfer2["sender"]["address"] == STONFI_ADDRESS_2:
                        swapped_amount += int(transfer2["amount"]) / 10 ** 9
                    else:
                        print(events[i]["event_id"])

        if length < 1000:
            break
        params["before_lt"] = next_from

    return swapped_amount


# проверяет свап за последние сутки по UTC и еще то что кошелек старый (решено было отказаться)
# def check_daily_swaps(wallet: str, offset: int = 0,
#                       period: int = 1) -> tuple[list[str], bool]:
#     start_time = (int(time()) // (24 * 3600) - offset) * (24 * 3600)
#     end_time = start_time + period * 24 * 3600
#     url = f'https://tonapi.io/v2/accounts/{wallet}/events?limit=100'
#     res = get(url, headers=AUTH_HEADER).json()["events"]
#     swaps = []
#     for i in res:
#         if i["timestamp"] < start_time:
#             break
#         if i["timestamp"] > end_time:
#             continue
#         t = i["actions"][0].get("JettonTransfer", None)
#         if t and t["recipient"]["address"] == STONFI_ADDRESS_1:
#             swaps.append(i["event_id"])
#     previous_week = (int(time()) // (24 * 3600) - 7) * (24 * 3600)
#     is_old = bool(len(res) > 10 and (len(res) == 100 or
#                                      res[-10]["timestamp"] < previous_week))
#     return swaps, is_old
