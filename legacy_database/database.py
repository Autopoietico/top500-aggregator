import datetime
import sqlite3
import threading

import leaderboards

lock = threading.Lock()


class DatabaseAccess:
    def __init__(self, db_path: str):
        # db is used in FastAPI which uses multiple threads. This is to prevent sqlite3 from throwing an error
        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.connection.cursor()

    def create_info_table(self):
        """Creates the season_info table in the database"""
        lock.acquire()
        self.cursor.execute(
            """CREATE TABLE season_info(
                                    id TEXT PRIMARY KEY,
                                    collection_date INTEGER,
                                    disclaimer TEXT
                            )"""
        )
        self.connection.commit()
        lock.release()

    def add_info_entry(self, season_identifier: str, timestamp: int, disclaimer: str):
        """Adds a new entry to the season_info table in the database

        Args:
            season_identifier (str): season number identifier. Format: season_{seasonNumber}_{subseasonNumber}
            timestamp (int): timestamp of the season
            disclaimer (str): disclaimer for the season
        """
        lock.acquire()
        self.cursor.execute(
            f"""
            INSERT INTO season_info 
            (id, collection_date, disclaimer)
            VALUES(?, ?, ?)
            """,
            (season_identifier, timestamp, disclaimer),
        )
        self.connection.commit()
        lock.release()

    def create_season(self, seasonNumber: str):
        """Creates a new season table in the database

        Args:
            seasonNumber (str): season number identifier. Format: season_{seasonNumber}_{subseasonNumber}
        """
        self.cursor.execute(
            f"""CREATE TABLE season_{seasonNumber}(
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    region TEXT,
                                    role TEXT,
                                    gamesPlayed INTEGER,
                                    firstMostPlayed TEXT,
                                    secondMostPlayed TEXT,
                                    thirdMostPlayed TEXT
                            )"""
        )
        self.connection.commit()

    def add_leaderboard_entry(
        self, seasonNumber: str, leaderboard_entry: leaderboards.LeaderboardEntry
    ):
        """adds leaderboard entry to the database for a single season

        Args:
            seasonNumber (str): season number identifier. Format: season_{seasonNumber}_{subseasonNumber}
            leaderboard_entry (leaderboards.LeaderboardEntry): leaderboard entry to add to the database
        """
        lock.acquire()
        self.cursor.execute(
            f"""
            INSERT INTO season_{seasonNumber} 
            (region, role, gamesPlayed, firstMostPlayed, secondMostPlayed, thirdMostPlayed)
            VALUES(?, ?, ?, ?, ?, ?)
            """,
            (
                leaderboard_entry.region,
                leaderboard_entry.role,
                leaderboard_entry.games,
                leaderboard_entry.heroes[0].name,
                leaderboard_entry.heroes[1].name,
                leaderboard_entry.heroes[2].name,
            ),
        )
        self.connection.commit()
        lock.release()

    def get_all_records(self, seasonNumber: str) -> list[leaderboards.LeaderboardEntry]:
        """_summary_

        Args:
            seasonNumber (str): season number identifier. Format: season_{seasonNumber}_{subseasonNumber}


        Returns:
            list[leaderboards.LeaderboardEntry]: list of leaderboardEntry objects
        """
        lock.acquire()
        self.cursor.execute(f"SELECT * FROM season_{seasonNumber}")
        data = self.cursor.fetchall()
        lock.release()
        results = list()
        for line in data:
            results.append(
                leaderboards.LeaderboardEntry(
                    heroes=[
                        line[4],  # fmp
                        line[5],  # smp
                        line[6],  # tmp
                    ],
                    role=leaderboards.Role[line[2]],
                    region=leaderboards.Region[line[1]],
                    games=line[3],
                )
            )

        return results

    def get_seasons(self) -> list[str]:
        """Returns a list of all seasons in the database

        Returns:
            list[str]: list of season identifiers. Format: {seasonNumber}_{subseasonNumber}
        """
        lock.acquire()
        self.cursor.execute("SELECT * FROM season_info")
        data: list[tuple[str, int]] = self.cursor.fetchall()
        lock.release()
        # filter and sort and some other stuff lol.
        seasons_sorted = sorted(
            [entry[0].replace("season_", "") for entry in data],
            key=lambda x: (int(x.split("_")[0]), int(x.split("_")[1])),
        )
        output_seasons = list()
        for season in seasons_sorted:
            if season in ("34_8", "35_8", "36_8"):
                output_seasons.append(season)

        for season in seasons_sorted:
            if season not in ("34_8", "35_8", "36_8"):
                output_seasons.append(season)

        return output_seasons

    def get_total_hero_occurrence_count(
        self, hero: str, region: leaderboards.Region, seasonNumber: str
    ) -> int:
        """Gets the total number of times a hero has appeared in a season

        Args:
            hero (str): hero name
            region (leaderboards.Region): region
            seasonNumber (str): season number identifier. Format: {seasonNumber}_{subseasonNumber}

        Returns:
            int: number of times the hero has appeared in the season
        """
        lock.acquire()
        self.cursor.execute(
            f"""
            SELECT COUNT(*) FROM season_{seasonNumber}
                WHERE region = '{region.name}'
                    AND (
                    firstMostPlayed = '{hero}' OR secondMostPlayed = '{hero}' OR thirdMostPlayed = '{hero}'
                    )
            """
        )
        result: tuple[int] = self.cursor.fetchone()
        lock.release()
        return result[0]

    def get_season_disclaimer(self, seasonNumber: str) -> str:
        """Gets the disclaimer for a season

        Args:
            seasonNumber (str): season number identifier. Format: {seasonNumber}_{subseasonNumber}

        Returns:
            str: disclaimer
        """
        lock.acquire()
        self.cursor.execute(
            f"SELECT disclaimer FROM season_info WHERE id = 'season_{seasonNumber}'"
        )
        result: tuple[str] = self.cursor.fetchone()
        lock.release()
        return result[0]

    def add_season_info_entry(
        self, season_identifier: str, disclaimer: str | None, patch_notes: str | None
    ) -> None:
        lock.acquire()
        self.cursor.execute(
            f"INSERT INTO season_info (id, disclaimer, patch_notes) VALUES(?, ?, ?)",
            (season_identifier, disclaimer, patch_notes),
        )
        lock.release()
        return None


if __name__ == "__main__":
    dba = DatabaseAccess("../data/data.db")