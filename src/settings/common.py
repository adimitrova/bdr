from os import environ

ENV = 'prod'
RETRY_COUNTER = environ.get('RETRY_COUNTER', 3)
DISCOUNT_PRICE_PERCENT = 3
REGIONS = environ.get("REGIONS",
                      [
                          {
                              "name": "Derelik",
                              "region_id": "10000001",
                              "info": "trade hub"
                          },
                          {
                              "name": "The Forge",
                              "region_id": "10000002",
                              "info": "trade hub, Jita is always cheaper due to its trade volume"
                          },
                          {
                              "name": "Metropolis",
                              "region_id": "10000042",
                              "info": "regional hub"
                          }
                      ])

BASE_URL = "https://esi.evetech.net"
API_VERSION = "/latest"
ENDPOINT_HISTORICAL_DAILY_PRICES_PER_REGION = "/markets/{region_id}/history/?type_id={type_id}"

# each item (type) has info with name and description
ENDPOINT_GET_ITEM_INFO = "/universe/types/{type_id}/?datasource=tranquility&language=en"

# This will return all market orders in that region
# The lowest sell order price (cheapest available item)
# The highest buy order price (highest bid price)
ENDPOINT_CURR_PRICE_PER_REGION = "/markets/{region_id}/orders/"
ENDPOINT_CURR_PRICE_PER_REGION_AND_ITEM_BASE = "/markets/{region_id}/orders/?type_id={type_id}"
ENDPOINT_CURR_PRICE_PER_REGION_BASE = "/markets/{region_id}/orders"

# actual price people are selling at for all items
ENDPOINT_CURR_PRICE_PER_REGION_SELL = f"{ENDPOINT_CURR_PRICE_PER_REGION_BASE}/?order_type=sell"
ENDPOINT_CURR_PRICE_PER_REGION_AND_ITEM_SELL = f"{ENDPOINT_CURR_PRICE_PER_REGION_AND_ITEM_BASE}&order_type=sell"

# ENDPOINT_CURR_PRICE_PER_REGION_BUY = f"{ENDPOINT_CURR_PRICE_PER_REGION_BASE}&order_type=buy"

# fetch prices for all items/types, sort by adjusted_price to get the top X items to use
ENDPOINT_MARKET_ITEM_PRICES = "/markets/prices/"
