# types.py - Defines data structures and a context manager for scraping operations related to calendar dates.
"""
This module defines data structures and a context manager for scraping operations related to calendar dates.

Classes:
    CalendarDate: A class to represent a calendar date with attributes for calendar type, year, month, and day.
    CalendarRange: A class to represent a range of calendar dates with attributes for calendar type, years, months, and days.
    ScrapingContext: A context manager for scraping operations, encapsulating various parameters and state, including progress tracking and result storage.

Dependencies:
    dataclasses: Provides a decorator and functions for creating data classes.
    typing: Provides type hints for function and variable annotations.
    tqdm: Provides a fast, extensible progress bar for loops and other operations."""

from dataclasses import dataclass, field
from typing import Literal

from tqdm import tqdm


@dataclass
class CalendarDate:
    """
    A class to represent a calendar date.

    Attributes:
        calenadr_type (Literal["gregorian", "jalali"]): The type of calendar, either "gregorian" or "jalali".
        year (int): The year of the date.
        month (int): The month of the date.
        day (int): The day of the date.
    """

    calenadr_type: Literal["gregorian", "jalali"]
    year: int
    month: int
    day: int


@dataclass
class CalendarRange:
    """
    A class to represent a range of calendar dates.

    Attributes:
        calenadr_type (Literal["gregorian", "jalali"]): The type of calendar being used, either "gregorian" or "jalali".
        years (list): A list of years included in the range.
        months (set | list | Literal["whole_year"]): A set or list of months included in the range, or "whole_year" to include all months.
        days (set | list | Literal["whole_month"]): A set or list of days included in the range, or "whole_month" to include all days of the month.
    """

    calenadr_type: Literal["gregorian", "jalali"]
    years: list
    months: set | list | Literal["whole_year"]
    days: set | list | Literal["whole_month"]


@dataclass
class ScrapingParameters:
    """
    A class to represent the parameters for scraping operations.

    Attributes:
        calendar_range (CalendarRange): The range of dates to be scraped.
        sleep_range (tuple[int, int]): The range of sleep intervals between requests.
        retry_limit_warning (int): The number of retries before issuing a warning.
        halt_limit (int): The number of retries before halting the operation.
        save_file_path (str | None): The file path where results will be saved.
        resume (bool): Flag indicating whether to resume from a previous state.
    """

    calendar_range: CalendarRange
    sleep_range: tuple[int, int]
    retry_limit_warning: int
    halt_limit: int
    save_file_path: str
    resume: bool


@dataclass
class ScrapingContext:
    """
    A context manager for scraping operations, encapsulating various parameters and state.

    Attributes:
        params (ScrapingParameters): The parameters for scraping operations.
        pbar (tqdm): A progress bar instance to track scraping progress.
        loaded_dates (list): A list to store dates that have been loaded.
        results (list): A list to store the results of the scraping operation.

    Args:
        params (ScrapingParameters): The parameters for scraping operations.
    """

    params: ScrapingParameters
    pbar: tqdm = field(
        default_factory=lambda: tqdm(
            total=0,
            position=0,
            leave=True,
            desc="Initializing the scraping process...",
        )
    )
    loaded_dates: list = field(default_factory=list)
    results: list = field(default_factory=list)
