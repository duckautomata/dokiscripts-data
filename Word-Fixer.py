# Simple script to FAR words in the archive.
# Since we are using a model, it tends to get some words wrong. This will fix any common word errors.

import os
from tqdm import tqdm


def replace_words_in_srt_files(word_map: dict[str, str], directory: str):
    srt_files = [
        os.path.join(root, file)
        for root, _, files in os.walk(directory)
        for file in files
        if file.endswith(".srt")
    ]

    with tqdm(total=len(srt_files), desc="Processing .srt files") as pbar:
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(".srt"):
                    file_path = os.path.join(root, file)

                    with open(file_path, "r+", encoding="utf-8") as f:
                        content = f.read()

                        for old_word, new_word in word_map.items():
                            content = content.replace(
                                old_word.lower(), new_word.lower()
                            )
                            content = content.replace(
                                old_word.capitalize(), new_word.capitalize()
                            )

                        f.seek(0)
                        f.write(content)

                    pbar.update(1)


# Case sensitive. But we replace for both lowercase and uppercase versions. So it's best to only have lowercase here.
# "old_word1": "new_word1"
word_map = {
    "f**k": "fuck",
    "f***ing": "fucking",
    "f*****g": "fucking",
    "f******": "fucking",
    "fuck***t": "fucking bullshit",
    "fuck***": "fucking",
    "f**ing": "fucking",
    "f*****": "fucker",
    "f***": "fuck",
    "f**": "fuck",
    "sh**": "shit",
    "s**t": "shit",
    "s***": "shit",
    "a**": "ass",
    "b**ch": "bitch",
    "b***h": "bitch",
    "c***": "cunt",
    "p***y": "pussy",
    "d**n": "damn",
    "****": "fuck",
}

directory = "Transcript"

replace_words_in_srt_files(word_map, directory)
