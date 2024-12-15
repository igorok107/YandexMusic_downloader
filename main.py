import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-q', action='store_true', help='Don\'t promt actions')
parser.add_argument('-d', action='store_true', help='Don\'t download tracks')
parser.add_argument('-l', action='store_true', help='Print all tracks')
args = parser.parse_args()

from yandex_music import Client
from yandex_music.exceptions import *
import json
from pathlib import Path
import colorama

colorama.init(autoreset=True)

try:
    token = Path("config").read_text()
except FileNotFoundError:
    token = ''


client = Client(token)
try:
    client.init()
except NotFoundError:
    print(f"{colorama.Fore.LIGHTRED_EX}Error 404. (Wrong token or api url)")
    exit(404)

if not client.me.account.uid:
    print(f"{colorama.Fore.LIGHTRED_EX}Not authorized.")
    exit(1)

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
    _p = input(f'Path with music ("{p}")')
    if _p:
        if not Path(_p).exists():
            Path(_p).mkdir(parents=True, exist_ok=True)
        if Path(_p).is_dir():
            p = _p
        else:
            print(f"{colorama.Fore.LIGHTRED_EX}\"{_p}\" not is directory")
            exit(2)

try:
    with open('tracks.json', mode='r', encoding='UTF-8') as f:
        tracks_db = json.load(f)
except (FileNotFoundError, json.decoder.JSONDecodeError):
    tracks_db = {}

downloaded = 0
try:
    for (i, short_track) in enumerate(tracks):
        if not tracks_db.get(short_track.track_id, False):
            tracks_db[short_track.track_id] = short_track.fetchTrack().to_dict()
            list_tracks_modified = True
        track = tracks_db.get(short_track.track_id)
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
                except InvalidBitrateError:
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
    if len(tracks_db) > 0 and list_tracks_modified:
        with open('tracks.json', mode='w', encoding='UTF-8') as f:
            json.dump(tracks_db, f, ensure_ascii=False, indent=4)
    print(f'\n{colorama.Fore.LIGHTBLUE_EX}Exit...')
finally:
    if downloaded > 0:
        print(f"{colorama.Fore.GREEN}{downloaded} tracks was downloaded.")
    print(f"{colorama.Fore.GREEN}Total {len(tracks_db)} tracks in DataBase.")
