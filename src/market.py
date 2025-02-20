import os
import random
import time
from typing import List
from math import inf
from pyspark.errors.exceptions.captured import AnalysisException
from pyspark.sql import SparkSession

from src.settings import config
from src.type import Type
from src.gamer import Gamer
from src.utils import (
    get_logger,
    fetch_data_from_api,
    save_data,
    get_data_path,
    get_a_spark_session,
    get_date_today,
    get_date_yesterday
)

logger = get_logger("Type logger")


class Market:
    def __init__(self, region_id: int, spark_context: SparkSession, num_of_types_to_fetch: int = None):
        self.id: int = region_id  # market id = region_id
        self.num_of_types_to_fetch: int = num_of_types_to_fetch if num_of_types_to_fetch else 10
        self.traders: List[Gamer] = []
        self.sc: SparkSession = spark_context
        self.type_ids_list: List[int] = self.get_top_x_most_popular_types()

    def get_top_x_most_popular_types(self):
        # top types are the ones with the most volume, i.e. the ones that are most commonly traded in the current market
        logger.info("Fetching data from API - top %s types for market_id=%s", self.num_of_types_to_fetch, self.id)
        data_file_name = get_data_path(file_name=f"CURR_PRICE_PER_REGION_SELL_{self.id}.json")

        if not os.path.isfile(data_file_name):
            data = fetch_data_from_api(
                url=config.ENDPOINT_CURR_PRICE_PER_REGION_SELL.format(region_id=self.id))
            save_data(data=data,
                      file_path=data_file_name)

        df = self.sc.read.json(data_file_name)
        logger.info("Showing the schema and the first rows from the data")
        df.show(5)
        logger.debug(f"DataFrame Schema: {df.schema.simpleString()}")
        df.createOrReplaceTempView(name='sell_orders')

        popular_types_df = self.sc.sql(f"""
                SELECT type_id, SUM(volume_total) AS total_volume
                FROM sell_orders
                GROUP BY type_id
                ORDER BY total_volume DESC LIMIT {self.num_of_types_to_fetch}
            """)
        try:
            popular_types_df.coalesce(1).write.json(
                path=get_data_path(file_name=f"TOP_{self.num_of_types_to_fetch}_TYPES_PER_REGION_{self.id}"))
        except AnalysisException:
            pass
        popular_types_df.registerTempTable('types')

        # NB: get a list of type_ids based on popularity (most orders / total_volume) for that region
        popular_types_list = popular_types_df.select('type_id').collect()
        popular_types_list = [int(row.type_id) for row in popular_types_df.collect()]

        # NB: Use this info to get all these types' historical data based on type_id and region_id
        logger.info("Extracted top %s most popular type IDs for market %s: %s",
                    self.num_of_types_to_fetch, self.id, popular_types_list)
        return popular_types_list

    def add_trader(self, trader: Gamer):
        logger.info("Adding gamer %s to the traders list for market %s", trader.name, self.id)
        self.traders.append(trader)

    def remove_trader(self, trader: Gamer):
        logger.info("Removing gamer %s from the traders list for market %s", trader.name, self.id)
        if trader in self.traders:
            self.traders.remove(trader)
        else:
            logger.info(f"Gamer {trader.name} not found in traders list.")

    def notify_traders(self, type_obj: Type):
        for trader in self.traders:
            logger.info("Notifying trader %s about low price for type_id %s", trader.name, type_obj.id)
            trader.notify(market_id=self.id, type_obj=type_obj)

    def track_item_prices(self):

        while True:
            logger.info("=" * 100)
            # random choice simulates random type data coming in for one of the IDs already inside the list
            type_id_to_query = random.choice(self.type_ids_list)
            curr_price = self.get_curr_price_for_type(type_id_to_query=type_id_to_query)
            type_obj = Type(spark_context=self.sc, type_id=type_id_to_query, market_id=self.id)
            if type_obj.is_price_good_to_buy(curr_price=curr_price):
                self.notify_traders(type_obj=type_obj)
            time.sleep(3)  # FIXME: maybe with a proper queue and/or rabbitMQ if there's time, for now.. sleep

    def get_curr_price_for_type(self, type_id_to_query: int):
        logger.info("Receiving new data for type_id %s and market_id %s.. please wait..",
                    type_id_to_query, self.id)  # fake log to simulate polling
        url = config.ENDPOINT_CURR_PRICE_PER_REGION_AND_ITEM_SELL.format(region_id=self.id,
                                                                         type_id=type_id_to_query)
        api_resp_json = fetch_data_from_api(url=url)
        df = self.sc.createDataFrame(api_resp_json)
        df.createOrReplaceTempView(name='sell_orders_per_item')
        logger.info("Fetching the lowest price available from today for type_id %s and market_id %s",
                    type_id_to_query, self.id)

        base_query = """
                        SELECT issued, price, volume_remain
                        FROM sell_orders_per_item
                        WHERE volume_remain > 0
                        AND CAST(issued AS TIMESTAMP) LIKE '{date_to_query}%'
                        ORDER BY CAST(issued AS TIMESTAMP) DESC, price ASC
                        LIMIT 1
                    """
        latest_order_df = self.sc.sql(base_query.format(date_to_query=get_date_today()))
        if latest_order_df.isEmpty():
            latest_order_df = self.sc.sql(base_query.format(date_to_query=get_date_yesterday()))

        curr_lowest_sell_price = None
        if not latest_order_df.isEmpty():
            curr_lowest_sell_price = float(latest_order_df.select("price").collect()[0][0])
            self.sc.catalog.dropTempView("sell_orders_per_item")
            logger.info("Current lowest price for type_id %s is %s", type_id_to_query, curr_lowest_sell_price)
        else:
            logger.info("Current lowest price for type_id %s could NOT be determined for some reason.. Check the data",
                        type_id_to_query)
            data_file_name = get_data_path(
                file_name=f"DEBUG_SELL_ORDERS_REGIONID_{self.id}_TYPEID_{type_id_to_query}.json")
            logger.info("Saving the full fetched data for debugging at %s", data_file_name)
            save_data(data=api_resp_json, file_path=data_file_name)
            curr_lowest_sell_price = inf
        self.sc.catalog.dropTempView("sell_orders_per_item")
        return curr_lowest_sell_price
