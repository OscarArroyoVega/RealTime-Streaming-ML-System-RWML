from quixstreams import Application

def produce_trade(
    kafka_broker_address: str,
    kafka_topic: str,
    product_id: str,
):
    """
    Reads trades from the Kraken websocket API and saves them the given Kafka topic.
    
    Args:
        kafka_broker_address (str): Kafka broker address.
        kafka_topic (str): Kafka topic where the trades will be saved.
        product_id (str): Product id of the trades to be saved.
        
    Returns:    
        None
    """
    
    # Create an Application to connect to the Quix broker with Kafka 
    from quixstreams import Application
    
    # Create an Application to connect to the Quix broker with kafka topic
    app = Application(broker_address='localhost:9092')
    # Define an output topic with JSON serialization
    output_topic = app.topic(name=kafka_topic, value_serializer='json')

    # Create a Producer instance
    with app.get_producer() as producer:
        event = {"product_id": ETH/EUR, 
                 "price": 1000,
                 "qty": 1,
                 "side": "buy",
                 "timestamp_ms": 1609459200000}
        # Serialize the event using the defined topic 
        # Transform it into a sequence of bytes
        message = output_topic.serialize(key=data["id"], value=event)
        
        #Produce the messageinto the kafka topic
        producer.produce(topic=output_topic.name, key=message.key, value=message.value)
        
if __name__ == '__main__':
    produce_trade(
        kafka_broker_address='localhost:9092',
        kafka_topic='trades',
        product_id='ETH/EUR',
    )