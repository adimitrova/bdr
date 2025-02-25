from pyspark.sql import SparkSession
from pyspark.sql.functions import lit
from pyspark.sql.types import StructType, StructField, FloatType, LongType, IntegerType, StringType

from src.utils import (
    get_logger,
    fetch_data_from_api,
    save_data,
    get_data_path,
    get_date_range
)

from src.settings import config

logger = get_logger("Type")


class Type:
    def __init__(self, spark_context: SparkSession, type_id: str, market_id: int):
        self.sc: SparkSession = spark_context
        self.id: int = type_id
        self._name: str = None
        self._description: str = None
        self._market_id: int = market_id
        self.buy_discount_percent: int = config.DISCOUNT_PRICE_PERCENT if config.DISCOUNT_PRICE_PERCENT else 30
        self.seven_day_ave: float = None
        self.seven_days_volume: int = None

    @property
    def market_id(self):
        return self._market_id

    @property
    def name(self):
        if not self._name:
            self._get_type_name_description()
        return self._name

    @property
    def description(self):
        if not self._description:
            self._get_type_name_description()
        return self._description

    def calculate_7day_ave(self) -> None:
        # NB: needs to fetch latest data as the average may change based on new orders
        # (not sure i will have time to implement ^^)
        # so for now - calculate once at the instantiation time of the object and use as hardcoded value
        logger.info("Fetching historical data for type %s with ID=%s for market_id=%s..", self.name, self.id,
                    self.market_id)

        schema = StructType([
            StructField("avg_price_7_days", FloatType(), True),
            StructField("total_volume", LongType(), True),
            StructField("type_id", IntegerType(), True),
            StructField("type_name", StringType(), True)
        ])
        url = config.ENDPOINT_GET_ITEM_INFO.format(type_id=self.id)
        type_name = fetch_data_from_api(url=url).get('name', 'Unknown type')
        logger.info("Querying API for item [%s] with ID=%s, market_id=%s", type_name, self.id, self.market_id)

        data_file_name = get_data_path(file_name=f"HISTORICAL_DAILY_PRICE_REGION_{self.market_id}_TYPE_{self.id}.json")
        url = config.ENDPOINT_HISTORICAL_DAILY_PRICES_PER_REGION.format(region_id=self.market_id, type_id=self.id)
        data_historical_data_per_region = fetch_data_from_api(url=url)
        df = self.sc.createDataFrame(data_historical_data_per_region)
        logger.debug(f"DataFrame Schema: {df.schema.simpleString()}")
        logger.info("Showing the schema and the first rows from the historical data")
        df.show(5)
        save_data(data=data_historical_data_per_region, file_path=data_file_name)  # just to have it
        df.createOrReplaceTempView(name='historical_market_data')
        date_from, date_to = get_date_range()
        logger.info("Computing average based on the following time period: %s - %s", date_from, date_to)

        hist_ave_7days_per_region_and_type_df = self.sc.sql(f"""
                    SELECT
                        ROUND(AVG(average), 3) AS avg_price_7_days,
                        ROUND(SUM(volume), 0) AS total_volume
                    FROM historical_market_data
                    WHERE date BETWEEN "{date_from}" AND "{date_to}"
                    ORDER BY total_volume DESC
                """)
        seven_day_average_and_volume = hist_ave_7days_per_region_and_type_df.collect()[0]
        self.seven_day_ave = float(seven_day_average_and_volume['avg_price_7_days'])
        self.seven_days_volume = int(seven_day_average_and_volume['total_volume'])
        logger.info("Calculated seven_days_average = %s, seven_days_volume = %s",
                    self.seven_day_ave, self.seven_days_volume)
        self.sc.catalog.dropTempView("historical_prices_df")

    def calc_percent_from_ave(self) -> float:
        target_price = self.seven_day_ave - self.seven_day_ave * self.buy_discount_percent / 100
        logger.info("Calculated discounted price based on average for the last 7 days with discount of %s%%: %s",
                    self.buy_discount_percent, target_price)
        return target_price

    def is_price_good_to_buy(self, curr_price: int) -> bool:
        if not self.seven_day_ave:
            self.calculate_7day_ave()
        discount_price = self.calc_percent_from_ave()
        log_message = "Based on the given criteria of %s%% percent the current price " \
                      "of %s with market_id %s %s for buying. " \
                      "Current price stands at %s and average is %s. " \
                      "To be beneficial, the price should be <= %s"

        if curr_price <= discount_price:
            status = "IS GOOD"
            logger.info(log_message,
                        self.buy_discount_percent, self.name, self.market_id, status,
                        curr_price, self.seven_day_ave, discount_price)
            return True
        else:
            status = "is NOT good"
            logger.info(log_message,ss
                        self.buy_discount_percent, self.name, self.market_id, status,
                        curr_price, self.seven_day_ave, discount_price)
            return False
        # FIXME: Logs a line like
        #  8   19:13:33 - type.py:is_price_good_to_buy:109      - idk why, but it's not in the log file

    def _get_type_name_description(self) -> None:
        type_data = fetch_data_from_api(url=config.ENDPOINT_GET_ITEM_INFO.format(type_id=self.id))
        self._name = type_data.get("name", None)
        self._description = type_data.get("description", None)

    def __repr__(self):
        return repr(
            f'Type(id: {self.id}, name: {self.name}, description: {self.description} market_id: {self.market_id})')
