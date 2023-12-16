# Krishna Biniwale, kbiniwal@usc.edu
# ITP 216, Fall 2023
# Section: 32081
# Final Project
# Description:
# This is a web app that displays the stock prices and other data from various corporations.
# Users can search for the company through its name or ticker and select on the company they want to view.
# They will be shown a graph of the stock prices of the company, as well as other data about the stock.
# This doesn't use ML/AI, but it does use SQL databases (The CSV files are ONLY used to initialize the databases and
# are not used for anything else in the code.)
from flask import Flask, redirect, render_template, request, url_for
import os
import sqlite3 as sl
import csv
import json
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64


app = Flask(__name__)

import os

# Set your Kaggle API credentials
os.environ['KAGGLE_USERNAME'] = 'krishnabiniwale'
os.environ['KAGGLE_KEY'] = '5b070e0f2d9e0182c40798545d6ccba0'

# Set the path to the Kaggle API credentials file within your local project
project_directory = os.path.abspath(os.path.dirname(__file__))
kaggle_config_dir = project_directory
os.environ['KAGGLE_CONFIG_DIR'] = kaggle_config_dir

# Import kaggle after setting environment variables
import kaggle

# URL and file path
dataset_url = 'ehallmar/daily-historical-stock-prices-1970-2018'
csv_file_path_1 = 'historical_stocks.csv'

# Download the dataset using Kaggle API
kaggle.api.dataset_download_files(dataset_url, path='.', unzip=True)


# root end point
@app.route("/")
def home():
    """
    Goes to the home search page and displays the stocks from the user's search

    :return: renders the home html template page with the parameter of the list of stocks
    """
    stocks = request.args.get('stocks')
    if stocks is not None:
        return render_template('home.html', result=json.loads(stocks))
    else:
        return render_template('home.html', result=[])


@app.route("/stockdata", methods=["POST", "GET"])
def display_stock():
    """
    Displays a stock and its statistics based on the query result from db_get_stock_prices

    :return: data.html template that displays the above
    """
    ticker = request.form.get('selected_ticker', '')
    img_buffer, avg_price_num, avg_volume_num, avg_price_fluctuation_num = db_get_stock_prices(ticker)
    avg_price = format(avg_price_num, '.2f')
    avg_price_fluctuation = format(avg_price_fluctuation_num, '.2f')
    avg_volume = format(avg_volume_num, '.0f')

    # Render the template with the image buffer
    return render_template('data.html', img=img_buffer, price=avg_price, volume=avg_volume, fluctuation=avg_price_fluctuation)


@app.route("/findstock", methods=["POST", "GET"])
def find_stock():
    """
    Finds a stock or list of stocks based on the name

    :return: list of stocks based on name
    """
    stock_ticker = request.form['stockticker'].strip().upper()
    stock_name = request.form['stockname'].strip().upper()
    all_stocks = db_get_stocks()
    stocks = []
    # Finds the stocks based on the stock ticker and/or the name
    for stock in all_stocks:
        if (stock_ticker != '' and stock_ticker in stock[0].upper()) or (stock_name != '' and stock_name in stock[1].upper()):
            stocks.append([stock[0], stock[1]])

    return redirect(url_for('home', stocks=json.dumps(stocks)))


def db_get_stock_prices(ticker):
    """
    Queries the stocks database to get the stock prices and other data for the stock
    Then creates a plot for the stock prices

    :param ticker: the ticker of the stock selected

    :return: the image of the graph, and statistics for the stock prices
    """
    conn = sl.connect('stocks.db')

    # Construct the SQL query to fetch data for the specified ticker
    query = f"SELECT * FROM stock_prices WHERE ticker = '{ticker}'"

    # Read data from the SQL table into a DataFrame
    df_ticker = pd.read_sql(query, conn)

    # Convert the 'date' column to datetime format
    df_ticker.loc[:, 'date'] = pd.to_datetime(df_ticker['date'])

    # Plot the 'close' prices
    fig, ax = plt.subplots(1, 1)
    ax.plot(df_ticker['date'], df_ticker['close'], label=ticker)

    # Calculate the average price
    avg_price = df_ticker['close'].mean()

    # Calculate the average volume
    avg_volume = df_ticker['volume'].mean()

    # Calculate the average fluctuation
    df_ticker['fluctuation'] = df_ticker['high'] - df_ticker['low']
    avg_fluctuation = df_ticker['fluctuation'].mean()

    ax.set(title='Past prices of stock', xlabel='Date', ylabel='Close Price ($)')
    ax.legend()

    # Save the plot as an image
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)
    plt.close()

    # Close the database connection
    conn.close()

    # Encode the image buffer as base64
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')

    # Return the image buffer
    return img_base64, avg_price, avg_volume, avg_fluctuation


def db_get_stocks() -> list:
    """
    Queries the database for all the stocks and returns it
    Used to create a list of all stocks that is further manipulated

    :return: a list of stocks, with each stock having a ticker and a name
    """
    conn = sl.connect('stocks.db')
    cursor = conn.cursor()
    stmt = "SELECT * FROM stocks;"
    results = cursor.execute(stmt)
    stocks = []
    for result in results:
        stocks.append([result[0], result[2]])

    return stocks


def is_table_exist(table_name):
    """
    Queries the database to check if a table already exists
    Used to ensure that time isn't wasted duplicating a table

    :return: returns true if the table exists and false otherwise
    """
    conn = sl.connect('stocks.db')
    cursor = conn.cursor()
    query = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
    cursor.execute(query)

    # Fetch the result
    result = cursor.fetchone()

    # Close the database connection
    conn.close()

    # Return True if the table exists, False otherwise
    return result is not None


def create_tables():
    """
    Creates the stocks table and the stock_prices table in the database
    Called upon program start if the tables don't already exist
    """
    # Create stocks table
    conn = sl.connect('stocks.db')
    cursor = conn.cursor()
    create_table_query = '''
    CREATE TABLE IF NOT EXISTS stocks (
        ticker TEXT,
        exchange TEXT,
        name TEXT,
        sector TEXT,
        industry TEXT
    );
    '''
    cursor.execute(create_table_query)
    conn.commit()

    # Create stock prices table
    create_stock_prices_table_query = '''
    CREATE TABLE IF NOT EXISTS stock_prices (
        ticker TEXT,
        open REAL,
        close REAL,
        adj_close REAL,
        low REAL,
        high REAL,
        volume INTEGER,
        date DATE
    );
    '''
    cursor.execute(create_stock_prices_table_query)
    conn.commit()

    # Close the database connection
    conn.close()


def read_csv_files():
    """
    Reads data from stocks CSV and insert into the database
    Called upon program start if the tables in the database don't already exist
    """
    conn = sl.connect('stocks.db')
    cursor = conn.cursor()
    csv_file_path_1 = 'historical_stocks.csv'

    with open(csv_file_path_1, 'r', newline='', encoding='utf-8') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        next(csvreader)  # Skip the header row
        for row in csvreader:
            # Insert data into the 'stocks' table
            insert_query = 'INSERT INTO stocks VALUES (?, ?, ?, ?, ?)'
            cursor.execute(insert_query, row)

    conn.commit()

    csv_file_path_2 = 'historical_stock_prices.csv'  # Replace with the actual path to your CSV file

    with open(csv_file_path_2, 'r', newline='', encoding='utf-8') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        next(csvreader)  # Skip the header row
        for row in csvreader:
            # Insert data into the 'stock_prices' table
            insert_query = 'INSERT INTO stock_prices VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
            cursor.execute(insert_query, row)
    conn.commit()

    # Close the database connection
    conn.close()


@app.route('/<path:path>')
def catch_all(path):
    """
    Redirects junk urls to the home page

    :return: the home page html template
    """
    return redirect(url_for("home"))


# main entrypoint
# runs app
if __name__ == "__main__":
    # Checks to see if the tables already exist
    if not is_table_exist('stocks') or not is_table_exist('stock_prices'):
        create_tables()
        read_csv_files()
    app.secret_key = os.urandom(12)
    app.run(debug=True)
