import argparse
from os import listdir
from os.path import join, exists

import music_tag  # type: ignore


ENDC = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
BLUE = "\033[34m"


def blue(text: str, bold: bool = False) -> str:
    return str(f"{BOLD if bold else ''}{BLUE}{text}{ENDC}")


def red(text: str, bold: bool = False) -> str:
    return str(f"{BOLD if bold else ''}{RED}{text}{ENDC}")


def green(text: str, bold: bool = False) -> str:
    return str(f"{BOLD if bold else ''}{GREEN}{text}{ENDC}")


def fix_song(char: str, song: str) -> str:
    song = song[:-4]
    if char in song:
        song = char.join(song.split(char)[1:]).strip()
    return song


def find_cover(folder: str) -> str | None:
    for pattern in ["cover.jpg", "cover.jpeg", "cover.png"]:
        if exists(join(folder, pattern)):
            return pattern
    return None


def print_songs_table(info: dict) -> None:
    title_len = max(max(map(lambda x: len(str(x["title"].first)), info.values())), 5) + 2
    artist_len = max(max(map(lambda x: len(str(x["artist"].first)), info.values())), 6) + 2
    album_len = max(max(map(lambda x: len(str(x["album"].first)), info.values())), 5) + 2

    print(
        f"{blue('Title'.ljust(title_len), True)}{blue('Artist'.ljust(artist_len), True)}{blue('Album'.ljust(album_len), True)}{blue('Cover', True)}"
    )
    for tag in info.values():
        _title = str(tag["title"].first).ljust(title_len)
        _artist = str(tag["artist"].first).ljust(artist_len)
        _album = str(tag["album"].first).ljust(album_len)
        _has_cover = green("Yes") if tag["artwork"].first is not None else red("No")
        print(f"{_title}{_artist}{_album}{_has_cover}")


def ask(text: str, default: bool = False) -> bool:
    answer = input(text)
    if not answer:
        return default
    return answer.lower() == "y"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("folder")
    folder: str = parser.parse_args().folder
    folder = folder[:-1] if folder.endswith("/") else folder

    if not exists(folder):
        print(red(f"Provided directory [{folder}] does not exists"))
        return

    header = """
 __  __ _____ ____    ______ _               
|  \/  |  __ \___ \  |  ____(_)              
| \  / | |__) |__) | | |__   ___  _____ _ __ 
| |\/| |  ___/|__ <  |  __| | \ \/ / _ \ '__|
| |  | | |    ___) | | |    | |>  <  __/ |   
|_|  |_|_|   |____/  |_|    |_/_/\_\___|_|   

"""
    print(green(header))
    print(f"Selected directory: {green(folder)}")

    cover = find_cover(folder)
    print(f"Found cover: {green('YES') if cover else red('NO')}")

    songs = [join(folder, file) for file in listdir(folder) if file.endswith("mp3")]
    print(f"Total songs: {len(songs)}\n")

    song_to_tag = {song: music_tag.load_file(song) for song in songs}
    print_songs_table(song_to_tag)

    if not ask("\nDo you want to edit songs info? y/N: "):
        return

    replace_cover: bool = False
    new_cover = None
    if cover and ask("Use cover from folder? Y/n: ", True):
        replace_cover = True
        with open(join(folder, cover), "rb") as fb:
            new_cover = fb.read()

    new_artist: str | None = None
    if ask("Change Artist? y/N: "):
        new_artist = input("Type new Artist name: ")

    new_album: str | None = None
    if ask("Change Album? y/N: "):
        new_album = input("Type new Album name: ")

    fix: str | None = None
    if ask("Fix song names? y/N: "):
        songs_without_folder = [s.split("/")[-1] for s in songs]
        print("\nSome songs filenames from folder for example:")
        print("\n".join(songs_without_folder[:5]))

        while True:
            fix = input("""
(1) Use part after dash '-'
(2) Use part after space ' '
(3) Use part after dot '.'

Select fix: """)
            if fix not in "123":
                print("Unrecognized answer, try again")
                continue
            print()
            break

        max_len = max(map(len, songs_without_folder)) + 2
        char = {"1": "-", "2": " ", "3": "."}[fix]
        for song in songs_without_folder:
            print(f"{song.ljust(max_len)}{blue('->')}  {fix_song(char, song)}")

    input("\nPress Enter to start fix...")

    for song, tag in song_to_tag.items():
        if fix:
            del tag["title"]
            char = {"1": "-", "2": " ", "3": "."}[fix]
            tag["title"] = fix_song(char, song)

        if new_artist:
            del tag["artist"]
            tag["artist"] = new_artist

        if new_album is not None:
            del tag["album"]
            tag["album"] = new_album or None
        
        if replace_cover and new_cover:
            del tag["artwork"]
            tag["artwork"] = new_cover

        tag.save()


if __name__ == "__main__":
    main()
