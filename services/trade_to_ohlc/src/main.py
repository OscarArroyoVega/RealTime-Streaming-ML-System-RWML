from quixstreams import Application
from datetime import timedelta
from typing import Any, List, Optional, Tuple
from loguru import logger


def init_ohlc_candle(trade: dict):
    logger.debug(f"Received trade: {trade}")
    """
    Returns the initial OHLC candle when the first `trade` in that window happens.
    """
    return {
        'open': trade['price'],
        'high': trade['price'],
        'low': trade['price'],
        'close': trade['price'],
        'volume': trade['quantity'],
        'product_id': trade['product_id'],
    }

def update_ohlc_candle(candle: dict, trade: dict):
    """
    Updates the OHLC candle with the new `trade`.
    """
    candle['high'] = max(candle['high'], trade['price'])
    candle['low'] = min(candle['low'], trade['price'])
    candle['close'] = trade['price']
    candle['volume'] += trade['quantity']
    candle['product_id'] = trade['product_id']
    # candle['timestamp_ms'] = trade['timestamp_ms']
    return candle  # TODO add open to candle as candle['open'] = trade['price']**before update_ohlc_candle() 

def transform_trade_to_ohlcv(
    kafka_broker_address: str,
    kafka_input_topic: str,
    kafka_output_topic: str,
    kafka_consumer_group: str,
    ohlcv_window_seconds: int,
):
    """
    Reads incoming trades from a Kafka topic, aggregates them into OHLC data and writes the OHLC data to another Kafka topic.
    
    Args:
        kafka_broker_address (str): The address of the Kafka broker.
        kafka_input_topic (str): The name of the Kafka topic to read trades from.
        kafka_output_topic (str): The name of the Kafka topic to write OHLC data to.
        product_consumer_group (str): The name of the Kafka consumer group.
        
    Returns:
        None
    """
    
    # Define the application with Redpanda broker address
    app = Application(
        broker_address=kafka_broker_address,
        consumer_group=kafka_consumer_group,
        auto_create_topics=True,
    )
    
    def custom_ts_extractor(
        value: Any,
        headers: Optional[List[Tuple[str, bytes]]],
        timestamp: float,
        timestamp_type: int,
    ) -> int:
        """
        Extracts the timestamp from the message value.
        """  
        return value["timestamp_ms"]
    
    # Define the input and output topics
    input_topic = app.topic(name=kafka_input_topic, value_deserializer="json", timestamp_extractor=custom_ts_extractor)
    output_topic = app.topic(name=kafka_output_topic, value_serializer="json")

    # Create a StreamingDataFrame for the input topic
    sdf = app.dataframe(input_topic)
    
    # debug for incoming messages
    #sdf.update(logger.debug)

    # Apply processing logic
    #sdf = sdf.update(lambda row: {"processed_value": row["original_value"] * 2})

    # Send the processed data to the output topic
    #sdf = sdf.to_topic(output_topic)
    

    # create the application window, the meat of the application!
    sdf = (
        sdf.tumbling_window(duration_ms=timedelta(seconds=ohlcv_window_seconds))
        .reduce(
            reducer=update_ohlc_candle,
            initializer=init_ohlc_candle,)
        .final()
    )
    
    # unpack the dictionary into separate columns
    sdf["open"] = sdf["value"]["open"]
    sdf["high"] = sdf["value"]["high"]
    sdf["low"] = sdf["value"]["low"]
    sdf["close"] = sdf["value"]["close"]
    sdf["volume"] = sdf["value"]["volume"]
    sdf["product_id"] = sdf["value"]["product_id"]
    sdf["timestamp_ms"] = sdf["end"]
    
    # keep only the columns we need
    sdf = sdf[["product_id", "timestamp_ms", "open", "high", "low", "close", "volume"]]
    
    #print the output to the console
    sdf.update(logger.debug)
    
    sdf = sdf.to_topic(output_topic)
    
    # Run or kick off the application
    app.run(sdf)
    

if __name__ == "__main__":
    
    from src.config import config
    
    transform_trade_to_ohlcv(
        kafka_broker_address=config.kafka_broker_address,
        kafka_input_topic=config.kafka_input_topic,
        kafka_output_topic=config.kafka_output_topic, # FIXME extract config info to environment variables file
        kafka_consumer_group=config.kafka_consumer_group,
        ohlcv_window_seconds=config.ohlcv_window_seconds,
    )                   

    