# scraper.py - Defines the TimeDotIrScraper class for scraping holiday information from holidayapi.ir.
"""
This module contains the TimeDotIrScraper class, which is used to scrape holiday information
from holidayapi.ir for specific dates and calendar types.

Classes:
    TimeDotIrScraper: A class for scraping holiday information from holidayapi.ir.

Usage:
    scraper = TimeDotIrScraper()
    results = scraper.scrap(years, months, days, calenadr_type, sleep_range, retry_limit_warning, halt_limit, save_file_path, resume)
"""

import json
import os
import time
from typing import Literal

import numpy as np
import requests
from httpcore import NetworkError
from tqdm import tqdm

from .types import CalendarDate, CalendarRange, ScrapingContext, ScrapingParameters


class TimeDotIrScraper:
    """
    A scraper class for retrieving holiday information from holidayapi.ir for specific dates and calendar types.

    Methods:
        __init__():
            Initializes the TimeDotIrScraper instance.

        request_for_one_day(calenadr_type, year, month, day, sleep_range):

        _prepare_days(days):
            Prepares a list of days for scraping, validating and processing the input days.

        _prepare_months(months):

        _prepare_years(years):
            Prepares and validates a list of years for scraping.

        _check_resumability(years, calenadr_type, save_file_path, resume):

        _count_scraped_data(save_file_path, pbar):

        _update_save_file(save_file_path, results):

        scrap(years, months, days, calenadr_type, sleep_range, retry_limit_warning, halt_limit, save_file_path, resume):
    """

    def __init__(self):
        pass

    def request_single_day(
        self,
        calendar_date: CalendarDate,
        sleep_range: tuple = (5, 10),
    ) -> dict:
        """
        Sends a GET request to the holidayapi.ir for a specific date and calendar type.

        Args:
            calenadr_type (Literal["gregorian", "jalali"]): The type of calendar to use.
            year (int): The year of the date to request.
            month (int): The month of the date to request.
            day (int): The day of the date to request.
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
                    timeout=min(sleep_range),
                ).json()
                waiting_for_response = False
                time.sleep(np.random.uniform(*sleep_range))
            except requests.exceptions.RequestException as e:
                print(f"Request Error: {e}")
                print(f"Response status is not 200! Resending for {resend_count} times")
                time.sleep(np.random.uniform(*sleep_range))
                resend_count += 1
        return result

    def _prepare_days(self, days: set | list | Literal["whole_month"]) -> list:
        """
        Prepare a list of days for scraping.

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
        if isinstance(days, list):
            # check whether days list is not empty
            if len(days) == 0:
                raise IndexError(
                    "`days` list is empty. No day is selected to be scraped!"
                )
            # check whether days values are valid between 1 and 31
            if min(days) < 1 or max(days) > 31:
                raise IndexError("Days values are not valid.")
            days = list(set(sorted(days)))
        elif isinstance(days, str):
            days = list(range(1, 32))
        else:
            raise TypeError("Check the type annotations for input days.")
        return days

    def _prepare_months(self, months: set | list | Literal["whole_year"]) -> list:
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
        if isinstance(months, list):
            # check whether months list is not empty
            if len(months) == 0:
                raise IndexError(
                    "`months` list is empty. No month is selected to be scraped!"
                )
            # check whether months values are valid between 1 and 12
            if min(months) < 1 or max(months) > 12:
                raise IndexError("Months values are not valid.")
            months = list(set(sorted(months)))
        elif isinstance(months, str):
            months = list(range(1, 13))
        else:
            raise TypeError("Check the type annotations for input months.")
        return months

    def _prepare_years(self, years: list) -> list:
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
        # check the years given in the input
        if min(years) < 1:
            raise IndexError("Years values are below zero.")
        if not len(years) > 0:
            raise IndexError(
                "`years` list is empty. No year is selected to be scraped!"
            )
        years = list(set(sorted(years)))
        return years

    def _check_resumability(
        self,
        calendar_range: CalendarRange,
        save_file_path: str | None = None,
        resume: bool = True,
    ) -> tuple[list, list, str]:
        """
        Checks if the scraping process can be resumed from a previously saved file.

        Args:
            years (list): List of years to be scraped.
            calenadr_type (Literal["gregorian", "jalali"]): Type of calendar to be used.
            save_file_path (str | None, optional): Path to the file where results are saved. Defaults to None.
            resume (bool, optional): Flag to indicate if the process should be resumed from the saved file. Defaults to True.

        Returns:
            tuple[list, list, str]: A tuple containing:
                - results (list): List of results loaded from the saved file or an empty list if no file is provided.
                - loaded_dates (list): List of dates loaded from the saved file or an empty list if no file is provided.
                - save_file_path (str): Path to the file where results are saved.
        """
        results = []
        loaded_dates = []
        if not save_file_path:
            starting_year = sorted(calendar_range.years)[0]
            ending_year = sorted(calendar_range.years)[-1]
            now_time = time.strftime("%Y_%m_%d_%H_%M_%S")
            # make the `scraper_results` directory if not exists
            os.makedirs("scraping_results", exist_ok=True)

            save_file_path = f"scraping_results/time_ir_{starting_year}_to_{ending_year}_{calendar_range.calenadr_type}_{now_time}.json"

        elif save_file_path and resume:
            with open(save_file_path, "r", encoding="utf-8") as f:
                loaded_results = json.load(f)
                print(f"{len(loaded_results)} dates loaded successfully.")
                loaded_dates = []
                for i, _ in enumerate(loaded_results):
                    loaded_dates.append(list(loaded_results[i].keys())[0])

            results = loaded_results
        else:
            pass
        return results, loaded_dates, save_file_path

    def _count_scraped_data(self, save_file_path: str, pbar: tqdm) -> int:
        """
        Counts the number of scraped data entries in a JSON file and updates the progress bar description.

        Args:
            save_file_path (str): The file path to the JSON file containing the scraped data.
            pbar (tqdm): The progress bar instance to update with the count of scraped data.

        Returns:
            int: The number of scraped data entries in the JSON file.
        """
        with open(save_file_path, "r", encoding="utf-8") as f:
            loaded_file = json.load(f)
            count = len(loaded_file)
            pbar.set_description(desc=f"Number of Scraped Data: {count}")
        return count

    def _update_save_file(self, save_file_path: str, results: list) -> None:
        """
        Updates the save file with the given results.

        Args:
            save_file_path (str): The path to the file where results will be saved.
            results (list): The list of results to be saved in the file.

        Returns:
            None
        """
        with open(save_file_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)

    def _scrape_single_date(
        self,
        calendar_date: CalendarDate,
        scraping_context: ScrapingContext,
        scraping_parameters: ScrapingParameters,
    ):
        # skip requesting when the response is already in the results file
        the_date = f"{calendar_date.year}/{calendar_date.month}/{calendar_date.day}"
        if the_date in scraping_context.loaded_dates:
            return
        # request to get whether correct response or not
        # the response will be checked down below
        result = self.request_single_day(calendar_date)

        # check if the result is valid
        if not "status" in result:
            scraping_context.results.append({the_date: result})
            scraping_context.pbar.update()
            time.sleep(np.random.uniform(*scraping_parameters.sleep_range))
        # skip if the date is invalid
        else:
            if "invalid input!" in result["message"]:
                return

            # retry until getting the desired result
            retry_count = 1
            while "status" in result:
                print(
                    f"Server responded invalid results. Retrying for {retry_count} times"
                )
                time.sleep(np.random.uniform(*scraping_parameters.sleep_range))
                result = self.request_single_day(calendar_date)
                retry_count += 1
                if retry_count > scraping_parameters.retry_limit_warning:
                    print(
                        f"""Too much retrying! ({retry_count} times)
                        Check your network connection!"""
                    )
                if (
                    scraping_parameters.halt_limit
                    and retry_count > scraping_parameters.halt_limit
                ):
                    raise NetworkError(
                        """Halt the scraping process because of passing request halt limit.
                        Set `halt_limit` to `None` to prevent scraping from halting."""
                    )

            scraping_context.results.append({the_date: result})
            scraping_context.pbar.update()
            time.sleep(np.random.uniform(*scraping_parameters.sleep_range))

        if scraping_parameters.save_file_path:
            self._update_save_file(
                scraping_parameters.save_file_path, scraping_context.results
            )
        if scraping_parameters.save_file_path:
            self._count_scraped_data(
                scraping_parameters.save_file_path, scraping_context.pbar
            )

    def scrape(self, scraping_parameters: ScrapingParameters) -> list:
        """
        Scrapes data for the specified years, months, and days based on the given calendar type.

        Args:
            years (list): List of years to scrape data for.
            months (set | list | Literal["whole_year"]): Set or list of months to scrape data for, or "whole_year" to scrape all months.
            days (set | list | Literal["whole_month"]): Set or list of days to scrape data for, or "whole_month" to scrape all days.
            calenadr_type (Literal["gregorian", "jalali"]): Type of calendar to use for scraping.
            sleep_range (tuple, optional): Range of time to sleep between requests. Defaults to (5, 10).
            retry_limit_warning (int, optional): Number of retries before issuing a warning. Defaults to 20.
            halt_limit (int, optional): Number of retries before halting the scraping process. Defaults to 50.
            save_file_path (str | None, optional): Path to save the scraped data. If None, data will not be saved. Defaults to None.
            resume (bool, optional): Whether to resume scraping from the last saved state. Defaults to True.

        Returns:
            list: List of scraped data.

        Raises:
            NetworkError: If the number of retries exceeds the halt limit.
        """
        scraping_context = ScrapingContext(params=scraping_parameters)

        (
            scraping_context.results,
            scraping_context.loaded_dates,
            scraping_parameters.save_file_path,
        ) = self._check_resumability(
            scraping_parameters.calendar_range,
            scraping_parameters.save_file_path,
            scraping_parameters.resume,
        )
        days = self._prepare_days(scraping_parameters.calendar_range.days)
        months = self._prepare_months(scraping_parameters.calendar_range.months)
        years = self._prepare_years(scraping_parameters.calendar_range.years)

        # total days to add in the for loop
        scraping_context.pbar = tqdm(
            total=len(years) * len(months) * len(days)
            - len(scraping_context.loaded_dates)
        )
        for year in sorted(years):
            for month in months:
                for day in days:
                    calendar_date = CalendarDate(
                        scraping_parameters.calendar_range.calenadr_type,
                        year,
                        month,
                        day,
                    )
                    self._scrape_single_date(
                        calendar_date, scraping_context, scraping_parameters
                    )

        with open(scraping_parameters.save_file_path, "r", encoding="utf-8") as f:
            rs = json.load(f)
            print(f"{len(rs)} dates scraped successfully.")

        return scraping_context.results
