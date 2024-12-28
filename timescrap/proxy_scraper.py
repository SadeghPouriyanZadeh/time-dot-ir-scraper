# scraper.py - Defines the TimeDotIrScraper class for scraping holiday information from holidayapi.ir.
"""
This module contains the TimeDotIrScraper class, which is used to scrape holiday information
from holidayapi.ir for specific dates and calendar types.

Classes:
    TimeDotIrScraper: A class for scraping holiday information from holidayapi.ir.

Usage:
    scraper = TimeDotIrScraper()
    results = scraper.scrape(scraping_parameters)
"""

import json
import os
import time

import numpy as np
import requests
from httpcore import NetworkError
from tqdm import tqdm

from .types import CalendarDate, ScrapingContext, ScrapingParameters


class TimeDotIrScraper:
    """
    A scraper class for retrieving holiday information from holidayapi.ir for specific dates and calendar types.

    Methods:
        __init__():
            Initializes the TimeDotIrScraper instance.

        request_single_day(calendar_date, sleep_range):
            Sends a GET request to the holidayapi.ir for a specific date and calendar type.

        _prepare_days(days):
            Prepares a list of days for scraping, validating and processing the input days.

        _prepare_months(months):
            Prepares and validates a list of months for scraping.

        _prepare_years(years):
            Prepares and validates a list of years for scraping.

        _check_resumability(calendar_range, save_file_path, resume):
            Checks if the scraping process can be resumed from a previously saved file.

        _count_scraped_data(save_file_path, pbar):
            Counts the number of scraped data entries in a JSON file and updates the progress bar description.

        _update_save_file(save_file_path, results):
            Updates the save file with the given results.

        _scrape_single_date(calendar_date, scraping_context, scraping_parameters):
            Scrapes data for a single date.

        scrape(scraping_parameters):
            Scrapes data for the specified years, months, and days based on the given calendar type.
    """

    def __init__(self, scraping_parameters: ScrapingParameters) -> None:
        self.scraping_parameters = scraping_parameters
        pbar = tqdm(total=0, desc="Initializing the scraping process...")
        self.scraping_context = ScrapingContext(params=scraping_parameters, pbar=pbar)

    def request_single_day(self, calendar_date: CalendarDate) -> dict:
        """
        Sends a GET request to the holidayapi.ir for a specific date and calendar type.

        Args:
            calendar_date (CalendarDate): The date and calendar type to request.
            sleep_range (tuple, optional): A tuple representing the range of seconds to sleep between retries. Defaults to (5, 10).

        Returns:
            dict: The JSON response from the API containing holiday information.

        Raises:
            requests.exceptions.RequestException: If there is an issue with the request.
        """
        waiting_for_response = True
        resend_count = 1
        while waiting_for_response:
            try:
                result = requests.get(
                    f"https://holidayapi.ir/{calendar_date.calenadr_type}/{calendar_date.year}/{calendar_date.month}/{calendar_date.day}",
                    timeout=min(self.scraping_parameters.sleep_range),
                ).json()
                waiting_for_response = False
                time.sleep(np.random.uniform(*self.scraping_parameters.sleep_range))
            except requests.exceptions.RequestException as e:
                print(f"Request Error: {e}")
                print(f"Response status is not 200! Resending for {resend_count} times")
                time.sleep(np.random.uniform(*self.scraping_parameters.sleep_range))
                resend_count += 1
        return result

    def _prepare_days(self) -> list:
        """
        Prepares a list of days for scraping.

        This method validates and processes the input days to ensure they are within the valid range (1 to 31).
        It accepts a set, list, or the string "whole_month" to generate the appropriate list of days.

        Args:
            days (set | list | Literal["whole_month"]): The days to be prepared. It can be:
                - A list of integers representing specific days.
                - A set of integers representing specific days.
                - The string "whole_month" to represent all days in a month (1 to 31).

        Returns:
            list: A sorted list of unique days within the range 1 to 31.

        Raises:
            IndexError: If the days list is empty or contains invalid day values (not between 1 and 31).
            TypeError: If the input days type is not a set, list, or the string "whole_month".
        """
        if isinstance(self.scraping_parameters.calendar_range.days, list):
            if len(self.scraping_parameters.calendar_range.days) == 0:
                raise IndexError(
                    "`days` list is empty. No day is selected to be scraped!"
                )
            if (
                min(self.scraping_parameters.calendar_range.days) < 1
                or max(self.scraping_parameters.calendar_range.days) > 31
            ):
                raise IndexError("Days values are not valid.")
            days = list(set(sorted(self.scraping_parameters.calendar_range.days)))
        elif isinstance(self.scraping_parameters.calendar_range.days, str):
            days = list(range(1, 32))
        else:
            raise TypeError("Check the type annotations for input days.")
        self.scraping_parameters.calendar_range.days = days
        return days

    def _prepare_months(self) -> list:
        """
        Prepares and validates a list of months for scraping.

        Args:
            months (set | list | Literal["whole_year"]): A set or list of integers representing months (1-12),
                                                         or the string "whole_year" to represent all months.

        Returns:
            list: A sorted list of unique months (integers) from 1 to 12.

        Raises:
            IndexError: If the months list is empty or contains invalid months values (not between 1 and 12).
            TypeError: If the input type is not a set, list, or the string "whole_year".
        """
        if isinstance(self.scraping_parameters.calendar_range.months, list):
            if len(self.scraping_parameters.calendar_range.months) == 0:
                raise IndexError(
                    "`months` list is empty. No month is selected to be scraped!"
                )
            if (
                min(self.scraping_parameters.calendar_range.months) < 1
                or max(self.scraping_parameters.calendar_range.months) > 12
            ):
                raise IndexError("Months values are not valid.")
            months = list(set(sorted(self.scraping_parameters.calendar_range.months)))
        elif isinstance(self.scraping_parameters.calendar_range.months, str):
            months = list(range(1, 13))
        else:
            raise TypeError("Check the type annotations for input months.")
        self.scraping_parameters.calendar_range.months = months
        return months

    def _prepare_years(self) -> list:
        """
        Prepares and validates a list of years.

        This method checks the input list of years for validity, ensuring that all
        years are positive integers and that the list is not empty. It then removes
        duplicates and sorts the years in ascending order.

        Args:
            years (list): A list of integer years to be validated and prepared.

        Returns:
            list: A sorted list of unique years.

        Raises:
            IndexError: If the input list of years is less than 1 or empty.
        """
        if min(self.scraping_parameters.calendar_range.years) < 1:
            raise IndexError("Years values are below zero.")
        if not len(self.scraping_parameters.calendar_range.years) > 0:
            raise IndexError(
                "`years` list is empty. No year is selected to be scraped!"
            )
        years = sorted(list(set(sorted(self.scraping_parameters.calendar_range.years))))
        self.scraping_parameters.calendar_range.years = years
        return years

    def _check_resumability(self) -> None:
        """
        Checks if the scraping process can be resumed from a previously saved file.

        Args:
            calendar_range (CalendarRange): The range of dates to be scraped.
            save_file_path (str | None, optional): Path to the file where results are saved. Defaults to None.
            resume (bool, optional): Flag to indicate if the process should be resumed from the saved file. Defaults to True.

        Returns:
            tuple[list, list, str]: A tuple containing:
                - results (list): List of results loaded from the saved file or an empty list if no file is provided.
                - loaded_dates (list): List of dates loaded from the saved file or an empty list if no file is provided.
                - save_file_path (str): Path to the file where results are saved.
        """
        self.scraping_context.results = []
        self.scraping_context.loaded_dates = []
        if not self.scraping_parameters.save_file_path:
            starting_year = min(self.scraping_parameters.calendar_range.years)
            ending_year = max(self.scraping_parameters.calendar_range.years)
            now_time = time.strftime("%Y_%m_%d_%H_%M_%S")
            self.scraping_parameters.save_file_path = f"scraping_results/time_dot_ir_{starting_year}_to_{ending_year}_{self.scraping_parameters.calendar_range.calenadr_type}_{now_time}.json"
            print(
                f'Starting a new scraping process at "{self.scraping_parameters.save_file_path}"'
            )
            os.makedirs(
                os.path.dirname(self.scraping_parameters.save_file_path), exist_ok=True
            )
        else:
            if self.scraping_parameters.resume:
                if not os.path.exists(self.scraping_parameters.save_file_path):
                    print(
                        f"File not found at {self.scraping_parameters.save_file_path}. Starting a new scraping process at this location."
                    )
                    os.makedirs(
                        os.path.dirname(self.scraping_parameters.save_file_path),
                        exist_ok=True,
                    )
                else:
                    with open(
                        self.scraping_parameters.save_file_path, "r", encoding="utf-8"
                    ) as f:
                        self.scraping_context.results = json.load(f)
                        print(
                            f"{len(self.scraping_context.results)} dates loaded successfully."
                        )

                        self.scraping_context.loaded_dates = [
                            list(result.keys())[0]
                            for result in self.scraping_context.results
                        ]
            else:
                print(
                    f"Previous data will be overwritten. Starting a new scraping process at {self.scraping_parameters.save_file_path}."
                )
                os.makedirs(
                    os.path.dirname(self.scraping_parameters.save_file_path),
                    exist_ok=True,
                )

    def _count_scraped_data(self) -> int:
        """
        Counts the number of scraped data entries in a JSON file and updates the progress bar description.

        Args:
            save_file_path (str): The file path to the JSON file containing the scraped data.
            pbar (tqdm): The progress bar instance to update with the count of scraped data.

        Returns:
            int: The number of scraped data entries in the JSON file.
        """
        with open(self.scraping_parameters.save_file_path, "r", encoding="utf-8") as f:
            loaded_file = json.load(f)
            count = len(loaded_file)
            self.scraping_context.pbar.set_description(
                desc=f"Total Number of Scraped Data={count}"
            )
        return count

    def _update_save_file(self) -> None:
        """
        Updates the save file with the given results.

        Args:
            save_file_path (str): The path to the file where results will be saved.
            results (list): The list of results to be saved in the file.

        Returns:
            None
        """
        with open(self.scraping_parameters.save_file_path, "w", encoding="utf-8") as f:
            json.dump(self.scraping_context.results, f, indent=4, ensure_ascii=False)

    def _scrape_single_date(self, calendar_date: CalendarDate) -> None:
        """
        Scrapes data for a single date.

        Args:
            calendar_date (CalendarDate): The date to be scraped.
            scraping_context (ScrapingContext): The context of the scraping process.
            scraping_parameters (ScrapingParameters): The parameters for the scraping process.

        Returns:
            None
        """
        the_date = f"{calendar_date.year}/{calendar_date.month}/{calendar_date.day}"
        if the_date in self.scraping_context.loaded_dates:
            return
        result = self.request_single_day(calendar_date)
        if not "status" in result:
            self.scraping_context.results.append({the_date: result})
            self.scraping_context.pbar.update()
        else:
            if "invalid input!" in result["message"]:
                return
            retry_count = 1
            while "status" in result:
                print(
                    f"Server responded invalid results. Retrying for {retry_count} times"
                )
                time.sleep(np.random.uniform(*self.scraping_parameters.sleep_range))
                result = self.request_single_day(calendar_date)
                retry_count += 1
                if retry_count > self.scraping_parameters.retry_limit_warning:
                    print(
                        f"""Too much retrying! ({retry_count} times)
                        Check your network connection!"""
                    )
                if (
                    self.scraping_parameters.halt_limit
                    and retry_count > self.scraping_parameters.halt_limit
                ):
                    raise NetworkError(
                        """Halt the scraping process because of passing request halt limit.
                        Set `halt_limit` to `None` to prevent scraping from halting."""
                    )
            self.scraping_context.results.append({the_date: result})
            self.scraping_context.pbar.update()
            time.sleep(np.random.uniform(*self.scraping_parameters.sleep_range))
        self._update_save_file()
        self._count_scraped_data()
        time.sleep(np.random.uniform(*self.scraping_parameters.sleep_range))

    def scrape(self) -> list:
        """
        Scrapes data for the specified years, months, and days based on the given calendar type.

        Args:
            scraping_parameters (ScrapingParameters): The parameters for the scraping process.

        Returns:
            list: List of scraped data.

        Raises:
            NetworkError: If the number of retries exceeds the halt limit.
        """
        self._check_resumability()
        days = self._prepare_days()
        months = self._prepare_months()
        years = self._prepare_years()
        total_days_to_scrape = len(self.scraping_parameters.calendar_range.years) * len(
            self.scraping_parameters.calendar_range.months
        ) * len(self.scraping_parameters.calendar_range.days) - len(
            self.scraping_context.loaded_dates
        )
        self.scraping_context.pbar.total = total_days_to_scrape
        self.scraping_context.pbar.desc = "Initializing the scraping process..."
        print(f"Total number of dates to scrape: {total_days_to_scrape}")

        for year in years:
            for month in months:
                for day in days:
                    calendar_date = CalendarDate(
                        self.scraping_parameters.calendar_range.calenadr_type,
                        year,
                        month,
                        day,
                    )
                    self._scrape_single_date(calendar_date)
        with open(self.scraping_parameters.save_file_path, "r", encoding="utf-8") as f:
            rs = json.load(f)
            print(f"{len(rs)} dates scraped successfully.")
        self.scraping_context.pbar.close()
        return self.scraping_context.results
