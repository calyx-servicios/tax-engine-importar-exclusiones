from pandas_job import PandasJob
from bot import Bot


def test():
    """Test function"""
    print("Test!")
    pandas = PandasJob()
    bot = Bot()
    df_csv = pandas.read_file("test.csv")
    df_csv_formated = bot.format_file(df_csv)
    print(df_csv_formated)
