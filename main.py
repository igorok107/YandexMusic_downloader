import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-q', action='store_true', help='Don\'t promt actions')
parser.add_argument('-d', action='store_true', help='Don\'t download tracks')
parser.add_argument('-l', action='store_true', help='Print all tracks')
args = parser.parse_args()

from yandex_music import Client
from yandex_music.exceptions import Unauthorized, BadRequest, InvalidBitrate
import json
from pathlib import Path
import colorama

colorama.init(autoreset=True)

try:
    token = Path("config").read_text()
except FileNotFoundError:
    token = ''

try:
    client = Client.from_token(token, report_new_fields=False)
except Unauthorized:
    client = False
    token = ''

if not client.me.account.uid:
    login = input("Login: ").strip()
    password = input("Password: ").strip()
    try:
        client = Client.from_credentials(login, password, report_new_fields=False)
    except BadRequest as ex:
        print(f'{colorama.Fore.RED}{str(ex)}')
        quit()

if not token and client.me.account.uid:
    Path('config').write_text(client.token)

list_tracks_modified = False
chars = [' ', '!', '~', '#', '-', '+', '=', '.', ',', '$', '&', "'", '—', '–', '(', ')', '[', ']', '{', '}', '@']

tracks = client.users_likes_tracks()
print(f'\nTotal tracks: {len(tracks)}')

download = not args.d
p = 'C:/Music'
if not args.q:
    if not args.d:
        if input("Download tracks? (Y/n): ").upper() in ["N", "NO", "NOT"]:
            download = False

    _p = input('Path with music ("C:\\Music")')
    if _p:
        p = _p

try:
    with open('tracks.json', mode='r', encoding='UTF-8') as f:
        list_tracks = json.load(f)
except (FileNotFoundError, json.decoder.JSONDecodeError):
    list_tracks = {}

try:
    downloaded = 0
    for (i, short_track) in enumerate(tracks):
        if not list_tracks.get(short_track.track_id, False):
            list_tracks[short_track.track_id] = short_track.fetchTrack().to_dict()
            list_tracks_modified = True
        track = list_tracks.get(short_track.track_id)
        file_path = Path(p) / \
                    f'{"".join([x if x.isalnum() or x in chars else "" for x in track.get("artists")[0]["name"]])} - ' \
                    f'{"".join([x if x.isalnum() or x in chars else "" for x in track.get("title", "Unknown")])}.mp3'
        print(colorama.ansi.clear_line(2), end='\r')
        print(f'{i + 1:03}: {track.get("artists")[0]["name"]} - {track.get("title")}', end=' ')
        if not file_path.exists():
            if download:
                print(f'[{colorama.Fore.YELLOW}Downloading{colorama.Fore.RESET}]', end='')
                try:
                    short_track.fetchTrack().download(file_path, bitrate_in_kbps=320)
                except InvalidBitrate:
                    short_track.fetchTrack().download(file_path, bitrate_in_kbps=192)
                downloaded += 1
                print(colorama.ansi.clear_line(2), end='\r')
                print(f'{i + 1:03}: {track.get("artists")[0]["name"]} - {track.get("title")}',
                      end=f' [{colorama.Fore.GREEN}OK{colorama.Fore.RESET}]{"*" if args.l else ""}\n')
            else:
                print(f'[{colorama.Fore.RED}NOT EXIST{colorama.Fore.RESET}]')
        else:
            print(f'[{colorama.Fore.GREEN}OK{colorama.Fore.RESET}]', end='')
            if args.l:
                print()
            else:
                print('\r', end='')
    print(colorama.ansi.clear_line(2))
except KeyboardInterrupt:
    print(f'\n{colorama.Fore.LIGHTBLUE_EX}Exit...')
finally:
    if downloaded > 0:
        print(f"{colorama.Fore.GREEN}{downloaded} tracks was downloaded.")
    if len(list_tracks) > 0 and list_tracks_modified:
        with open('tracks.json', mode='w', encoding='UTF-8') as f:
            json.dump(list_tracks, f, ensure_ascii=False, indent=4)
            print(f"{colorama.Fore.GREEN}Total {len(list_tracks)} tracks in DataBase.")
