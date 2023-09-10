import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from PIL import Image
from rich.console import Console
from rich.progress import Progress, track
from rich.prompt import Prompt

import leaderboards
import legacy_database

console = Console()
dba = legacy_database.DatabaseAccess("./data/data.db")


def worker(file: str):
    role, region, _ = file.split("-")  # parse the filename
    results = leaderboards.parse(  # parse the leaderboard
        image_path=os.path.join("./assets/leaderboard_images", file),
        assets_path="./assets/hero_images",
        role=role,
        region=region,
        model_name=model_name,
    )

    for i in results:
        if i.heroes[0].name != "Blank":
            dba.add_leaderboard_entry(seasonNumber=target_season, leaderboard_entry=i)


def worker2(file: str):
    role, region, _ = file.split("-")  # parse the filename
    results = leaderboards.parse(  # parse the leaderboard
        image_path=os.path.join("./assets/leaderboard_images/MANUAL", file),
        assets_path="./assets/hero_images",
        role=role,
        region=region,
        model_name=model_name,
    )
    for i in results:
        # Populate the database with the parsed results
        if i.heroes[0].name != "Blank":
            dba.add_leaderboard_entry(seasonNumber=target_season, leaderboard_entry=i)


def main():
    global target_season, model_name  # globals so the worker threads can access them
    # sorry

    target_season = "5_8"
    model_name = "thearyadev-2023-08-25"
    dba.create_season(seasonNumber=target_season)

    files = os.listdir("./assets/leaderboard_images")
    max_workers = 16
    progress = Progress()

    with progress:
        progress_bar = progress.add_task(
            "[red]Parsing Leaderboard Images...", total=len(files)
        )

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(worker, file) for file in files]
            for future in as_completed(futures):
                progress.advance(progress_bar)


if __name__ == "__main__":
    main()