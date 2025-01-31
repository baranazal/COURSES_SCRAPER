import pandas as pd
import os
import json
import time
import requests
import logging
from telegram import Bot
from telegram.ext import Application
import asyncio

# Telegram bot token and chat ID
bot_token = 'YOUR_BOT_TOKEN_HERE'
list_of_chat_ids = [
    'YOUR_CHAT_ID_HERE'
]
run_script_after_every_seconds = 10
config_dict = {
    'college_param1': {
        'college_of_technology_engineering': '2',
    },
    'degree_param0': {
        'bachelors': '3',
    },
    'academic_department_param2': {
        'humanities_basic_sciences': '8',
    }
}

# Configure logging
logging.basicConfig(filename='bot.log',
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class Telegram_Bot:

    def __init__(self, bot_token, list_of_chat_ids, config_dict):
        self.bot_token = bot_token
        self.list_of_chat_ids = list_of_chat_ids
        self.config_dict = config_dict
        self.application = Application.builder().token(bot_token).build()
        self.bot = self.application.bot

        # New additions
        self.request_semaphore = asyncio.Semaphore(5)
        self.last_request_time = 0
        self.min_request_interval = 1

        self.notification_settings = {
            'status': True,
            'times': True,
            'days': True,
            'rooms': True,
            'lecturers': True,
            'hours': True,
            'remarks': False,
            'batch_notifications': True,
            'notification_cooldown': 300,
        }

        self.stats = {
            'start_time': time.time(),
            'iterations_completed': 0,
            'changes_detected': 0,
            'notifications_sent': 0,
            'errors_encountered': 0,
        }

    async def _rate_limit(self):
        """Ensure minimum time between requests"""
        now = time.time()
        if now - self.last_request_time < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - (now - self.last_request_time))
        self.last_request_time = time.time()

    async def send_health_report(self):
        """Send periodic health report to admins"""
        uptime = time.time() - self.stats['start_time']
        report = (
            f"🤖 Bot Health Report\n"
            f"Uptime: {uptime/3600:.1f} hours\n"
            f"Iterations: {self.stats['iterations_completed']}\n"
            f"Changes Detected: {self.stats['changes_detected']}\n"
            f"Notifications Sent: {self.stats['notifications_sent']}\n"
            f"Errors: {self.stats['errors_encountered']}"
        )
        await self.send_telegram_message(report)

    async def send_telegram_message(self, message):
        """
        Send a message to the Telegram bot.
        """
        for chat_id in self.list_of_chat_ids:
            try:
                await self.bot.send_message(chat_id=chat_id, text=message)
                self.stats['notifications_sent'] += 1
                logging.info(f"Message sent to chat ID {chat_id}")
            except Exception as e:
                self.stats['errors_encountered'] += 1
                logging.error(
                    f"Failed to send message to chat ID {chat_id}: {e}")

    async def check_cell_changes_through_column_name(self, new_df, old_df,
                                                     column_name_to_check,
                                                     message_footer):
        """
        Check for changes in a specific column between two dataframes and return the rows with changes.
        """
        try:
            # Find rows where values in the specified column have changed
            changed_rows_df = new_df[new_df[column_name_to_check].ne(
                old_df[column_name_to_check])]

            if changed_rows_df.shape[0] > 0:
                for index in range(changed_rows_df.shape[0]):
                    # Get the corresponding rows from both dataframes
                    new_row = changed_rows_df.iloc[index]
                    # Find the matching row in old_df using the course name
                    old_row = old_df[old_df['name'] == new_row['name']].iloc[0]

                    message_header = f"Changes Detected in {column_name_to_check.capitalize()}"

                    # Only show the changed column and essential identifying information
                    row_str = [
                        f"Course Name: {new_row['name']}",
                        f"Section: {new_row['sectionNo']}",
                        f"Previous {column_name_to_check}: {old_row[column_name_to_check]}",  # Value from CSV
                        f"New {column_name_to_check}: {new_row[column_name_to_check]}"       # Value from website
                    ]

                    if column_name_to_check == 'status':
                        # Convert status codes to readable text
                        status_map = {'1': 'Available', '2': 'Cancelled', '3': 'Closed'}
                        row_str[-2] = f"Previous Status: {status_map.get(str(old_row[column_name_to_check]), old_row[column_name_to_check])}"
                        row_str[-1] = f"New Status: {status_map.get(str(new_row[column_name_to_check]), new_row[column_name_to_check])}"

                    each_row_message = '\n'.join(row_str)
                    final_message = f"{message_header}\n\n{each_row_message}\n\n{message_footer}"

                    print(f"Sending update for {new_row['name']} - {column_name_to_check} change")
                    await self.send_telegram_message(final_message)

            return changed_rows_df
        except Exception as e:
            logging.error(
                f"Error in check_cell_changes_through_column_name: {e}")
            return pd.DataFrame()

    async def check_remove_courses(self, new_df, old_df, column_name,
                                   message_footer):
        """
        Check for courses that have been removed from the old dataframe compared to the new dataframe.
        """
        try:
            missing_rows = old_df[~old_df[column_name].isin(new_df[column_name]
                                                            )]
            missing_rows.reset_index(inplace=True)

            if missing_rows.shape[0] > 0:
                each_row_messages = []
                for index in list(missing_rows.index):
                    row_list = list(
                        map(lambda x: str(x).strip(),
                            missing_rows.iloc[index].tolist()))
                    column_names = list(missing_rows.columns)

                    message_header = 'Changes Occurs: COURSE(S) DELETED'
                    row_str = []
                    for column_name, value in zip(column_names, row_list):
                        if column_name == 'status':
                            if value == '1':
                                value = 'Available'
                            elif value == '2':
                                value = 'Cancelled'
                            elif value == '3':
                                value = 'Closed'
                        row_str.append(
                            f'{column_name.title()} : {value.title()}')

                    each_row_message = '\n'.join(row_str)
                    final_message = message_header + '\n\n' + each_row_message + '\n\n' + message_footer
                    await self.send_telegram_message(final_message
                                                     )  # Await the coroutine
                    logging.info(final_message)
        except Exception as e:
            logging.error(f"Error in check_remove_courses: {e}")

    async def add_course(self, new_df, old_df, column_name, message_footer):
        """
        Check for new courses added to the new dataframe compared to the old dataframe.
        """
        try:
            new_rows_added = new_df[~new_df[column_name].
                                    isin(old_df[column_name])]
            message_header = 'Changes Occurs: NEW COURSE(S) ADDED'

            if new_rows_added.shape[0] > 0:
                each_row_messages = []
                for index in range(new_rows_added.shape[0]):
                    row_list = list(
                        map(lambda x: str(x).strip(),
                            new_rows_added.iloc[index].tolist()))
                    column_names = list(new_rows_added.columns)

                    row_str = []
                    for column_name, value in zip(column_names, row_list):
                        if column_name == 'status':
                            if value == '1':
                                value = 'Available'
                            elif value == '2':
                                value = 'Cancelled'
                            elif value == '3':
                                value = 'Closed'
                        row_str.append(
                            f'{column_name.title()} : {value.title()}')

                    each_row_message = '\n'.join(row_str)
                    final_message = message_header + '\n\n' + each_row_message + '\n\n' + message_footer
                    await self.send_telegram_message(final_message
                                                     )  # Await the coroutine
                return True
            else:
                return False
        except Exception as e:
            logging.error(f"Error in add_course: {e}")
            return False

    async def compare_new_and_downloaded_df(self, new_df, old_df, output_csv_name):
        """
        Compare a new dataframe with a downloaded dataframe and send messages for any changes detected.
        """
        try:
            def row_hash(row):
                return hash(tuple(str(v) for v in row.values))

            new_df['row_hash'] = new_df.apply(row_hash, axis=1)
            old_df['row_hash'] = old_df.apply(row_hash, axis=1)

            if new_df['row_hash'].equals(old_df['row_hash']):
                print(f"No changes detected for {output_csv_name}")
                return

            course_location = output_csv_name.split('.')[0]
            print(f"Checking changes for {course_location}...")

            # First check for added/removed courses
            course_added = await self.add_course(new_df, old_df, 'name', course_location)
            print(f"New courses check completed for {course_location}")

            await self.check_remove_courses(new_df, old_df, 'name', course_location)
            print(f"Removed courses check completed for {course_location}")

            if not course_added:
                priority_columns = ['status', 'times', 'days', 'rooms', 'lecturers', 'hours', 'remarks']

                for column in priority_columns:
                    if not self.notification_settings.get(column, True):
                        continue
                    print(f"Checking changes in {column} column...")

                    # Compare values, treating empty and NaN as equivalent
                    new_values = new_df[column].fillna('').astype(str).str.strip()
                    old_values = old_df[column].fillna('').astype(str).str.strip()

                    changed_mask = new_values != old_values

                    if changed_mask.any():
                        # Verify changes are real (not just different representations of empty)
                        real_changes = []
                        for idx in changed_mask[changed_mask].index:
                            new_val = new_values[idx]
                            old_val = old_values[idx]
                            if not (pd.isna(new_val) and pd.isna(old_val)) and new_val != old_val:
                                real_changes.append(idx)

                        if real_changes:
                            changed_df = new_df.loc[real_changes].copy()
                            await self.check_cell_changes_through_column_name(
                                changed_df, old_df, column, course_location)
                            print(f"Found and reported real changes in {column} column")
                            self.stats['changes_detected'] += 1
                        else:
                            print(f"No real changes found in {column} column")
                    else:
                        print(f"No changes found in {column} column")

            print(f"All checks completed for {course_location}")

        except Exception as e:
            self.stats['errors_encountered'] += 1
            logging.error(f"Error in compare_new_and_downloaded_df: {e}")

    async def params_to_dataframe(self, degree_id_param_0, college_id_param1,
                            department_id_param2, page_num_param3):
        """
        Fetch course data from the API and return it as a DataFrame.
        """
        async with self.request_semaphore:
            await self._rate_limit()
            try:
                url = "http://appserver.fet.edu.jo:7778/courses/actions/rmiMethod"
                payload = f"method=getCourses&paramsCount=4&param0={degree_id_param_0}&param1={college_id_param1}&param2={department_id_param2}&param3={page_num_param3}"
                headers = {
                    'Accept':
                    '*/*',
                    'Accept-Encoding':
                    'gzip, deflate',
                    'Accept-Language':
                    'en-US,en;q=0.9',
                    'Connection':
                    'keep-alive',
                    'Content-Length':
                    '67',
                    'Content-Type':
                    'application/x-www-form-urlencoded',
                    'Host':
                    'appserver.fet.edu.jo:7778',
                    'Origin':
                    'http://appserver.fet.edu.jo:7778',
                    'Referer':
                    'http://appserver.fet.edu.jo:7778/courses/index.jsp',
                    'User-Agent':
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
                    'Cookie':
                    'JSESSIONID=7f00000130d7c0410905455c41d48deaadd5e471fd4e.e34OaheNbxeRci0QahyTchuLci1ynknvrkLOlQzNp65In0'
                }
                response = requests.post(url, headers=headers, data=payload)
                response.raise_for_status()
                response.encoding = 'utf-8'
                json_dict = json.loads(
                    response.text.replace('"', '').replace("'", '"').replace(
                        '<br><br>', ' - '))
                return pd.DataFrame(json_dict)
            except Exception as e:
                self.stats['errors_encountered'] += 1
                logging.error(f"Error in params_to_dataframe: {e}")
                return pd.DataFrame()

    async def download_csv_using_params(self, college_id_param1,
                                        degree_id_param_0,
                                        department_id_param2, output_csv_name):
        """
        Download current website data and compare it with the existing CSV file for any changes.
        """
        try:
            if not os.path.exists('./Data_CSVs'):
                os.mkdir('./Data_CSVs')

            # First fetch current website data
            df_list = []
            for page_num in range(1, 100):
                df = await self.params_to_dataframe(degree_id_param_0,
                                              college_id_param1,
                                              department_id_param2,
                                              str(page_num))
                if not df.empty:
                    df_list.append(df)
                else:
                    break

            if df_list:
                current_website_df = pd.concat(df_list)
                current_website_df.reset_index(drop=True, inplace=True)

                # Standardize empty values in current website DataFrame
                current_website_df = current_website_df.replace({pd.NA: '', pd.NaT: '', None: '', 'nan': '', float('nan'): ''})
                current_website_df = current_website_df.fillna('')

                # Clean and standardize strings
                for col in current_website_df.columns:
                    if current_website_df[col].dtype == object:
                        current_website_df[col] = current_website_df[col].astype(str).str.strip()

                # Read existing CSV if it exists
                existing_csv_df = None
                if os.path.exists(f'./Data_CSVs/{output_csv_name}'):
                    try:
                        existing_csv_df = pd.read_csv(f'./Data_CSVs/{output_csv_name}')

                        # Apply same standardization to existing CSV DataFrame
                        existing_csv_df = existing_csv_df.replace({pd.NA: '', pd.NaT: '', None: '', 'nan': '', float('nan'): ''})
                        existing_csv_df = existing_csv_df.fillna('')

                        # Clean and standardize strings
                        for col in existing_csv_df.columns:
                            if existing_csv_df[col].dtype == object:
                                existing_csv_df[col] = existing_csv_df[col].astype(str).str.strip()

                        existing_csv_df.reset_index(drop=True, inplace=True)
                    except Exception as e:
                        logging.error(f"Error reading existing CSV file {output_csv_name}: {e}")
                        existing_csv_df = None

                if existing_csv_df is not None:
                    # Compare current website data with existing CSV
                    if not current_website_df.equals(existing_csv_df):
                        real_changes = False
                        for col in current_website_df.columns:
                            if not (current_website_df[col].fillna('') == existing_csv_df[col].fillna('')).all():
                                real_changes = True
                                break

                        if real_changes:
                            print(f"Real changes detected in {output_csv_name}")
                            await self.compare_new_and_downloaded_df(current_website_df, existing_csv_df, output_csv_name)
                        else:
                            print(f"No real changes detected in {output_csv_name}")

                # Save the current website data to CSV
                if not current_website_df.empty:
                    current_website_df['remarks'] = current_website_df['remarks'].str.replace('-', '')
                    current_website_df.to_csv(f'./Data_CSVs/{output_csv_name}',
                                  index=False,
                                  encoding='utf-8-sig')
            else:
                logging.warning(f"No data available for {output_csv_name.split('.')[0]}")
        except Exception as e:
            logging.error(f"Error in download_csv_using_params: {e}")

    async def get_dataframe_on_parameters(self):
        """
        Get the dataframe for each combination of parameters specified in the config_dict.
        """
        try:
            for college_name, college_id in self.config_dict[
                    'college_param1'].items():
                for degree_name, degree_id in self.config_dict[
                        'degree_param0'].items():
                    for department_name, department_id in self.config_dict[
                            'academic_department_param2'].items():
                        if college_id == '3':
                            if department_id == '1' or department_id == '7':
                                output_csv_name = f"Course_Data - {college_name}_{degree_name}_{department_name}.csv"
                                await self.download_csv_using_params(
                                    college_id, degree_id, department_id,
                                    output_csv_name)  # Await the coroutine
                        elif college_id == '2':
                            output_csv_name = f"Course_Data - {college_name}_{degree_name}_{department_name}.csv"
                            await self.download_csv_using_params(
                                college_id, degree_id, department_id,
                                output_csv_name)  # Await the coroutine
        except Exception as e:
            logging.error(f"Error in get_dataframe_on_parameters: {e}")


if __name__ == '__main__':
    try:
        print("Starting BAU Course Monitor Bot...")
        logging.info("Bot initialized and starting monitoring process")
        class_obj = Telegram_Bot(bot_token, list_of_chat_ids, config_dict)

        async def main():
            health_report_interval = 3600  # 1 hour
            last_health_report = time.time()
            iteration = 1

            while True:
                try:
                    print(f"\nStarting iteration {iteration}")
                    print(f"Checking for updates at {time.strftime('%Y-%m-%d %H:%M:%S')}")
                    await class_obj.get_dataframe_on_parameters()

                    if time.time() - last_health_report > health_report_interval:
                        await class_obj.send_health_report()
                        last_health_report = time.time()

                    class_obj.stats['iterations_completed'] += 1
                    print(f"Iteration {iteration} completed. Waiting {run_script_after_every_seconds} seconds...")
                    logging.info(f"Completed iteration {iteration}")
                    iteration += 1
                    await asyncio.sleep(run_script_after_every_seconds)

                except Exception as e:
                    class_obj.stats['errors_encountered'] += 1
                    logging.error(f"Iteration error: {e}")
                    await asyncio.sleep(30)  # Brief pause before retry

        asyncio.run(main())
    except Exception as e:
        logging.error(f"Script failed: {e}")
        print(f"Script encountered an error: {e}")
