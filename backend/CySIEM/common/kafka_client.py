"""
Thin, reusable Kafka producer/consumer wrappers.
Every service in KKSIEM (normalizer, detection consumers, agents) uses these
instead of touching confluent_kafka / kafka-python directly, so retry logic,
serialization, and error handling live in one place.
"""
from __future__ import annotations
import json
import logging
from typing import Callable, Optional, Iterator
from confluent_kafka import Producer, Consumer, KafkaException, KafkaError
from pydantic import BaseModel

logger = logging.getLogger("kksiem.kafka")


def _json_serializer(obj) -> bytes:
    if isinstance(obj, BaseModel):
        return obj.model_dump_json().encode("utf-8")
    return json.dumps(obj, default=str).encode("utf-8")


class KafkaProducerClient:
    def __init__(self, bootstrap_servers: str, client_id: str = "kksiem-producer"):
        self.producer = Producer({
            "bootstrap.servers": bootstrap_servers,
            "client.id": client_id,
            "acks": "all",
            "retries": 5,
            "retry.backoff.ms": 300,
            "enable.idempotence": True,
        })

    def _delivery_report(self, err, msg):
        if err is not None:
            logger.error(f"Delivery failed for record to {msg.topic()}: {err}")
        else:
            logger.debug(f"Delivered to {msg.topic()} [{msg.partition()}] @ offset {msg.offset()}")

    def send(self, topic: str, value, key: Optional[str] = None):
        try:
            self.producer.produce(
                topic=topic,
                key=key.encode("utf-8") if key else None,
                value=_json_serializer(value),
                callback=self._delivery_report,
            )
            self.producer.poll(0)
        except BufferError:
            logger.warning("Kafka producer queue full, flushing and retrying")
            self.producer.flush(5)
            self.producer.produce(topic=topic, key=key, value=_json_serializer(value))
        except KafkaException as e:
            logger.error(f"Kafka produce error on topic {topic}: {e}")
            raise
    def send_and_wait(
            self,
            topic: str,
            value,
            key: Optional[str] = None,
            timeout: float = 10.0,
        ):
            delivery_error = []

            def delivery_callback(err, msg):
                if err is not None:
                    delivery_error.append(err)

            try:
                self.producer.produce(
                    topic=topic,
                    key=key.encode("utf-8") if key else None,
                    value=_json_serializer(value),
                    callback=delivery_callback,
                )

                remaining = self.producer.flush(timeout)

                if remaining != 0:
                    raise TimeoutError(
                        f"Timed out delivering message to topic={topic}; "
                        f"{remaining} message(s) still pending"
                    )

                if delivery_error:
                    raise KafkaException(delivery_error[0])

            except Exception:
                logger.exception(
                    "Kafka synchronous delivery failed for topic=%s",
                    topic,
                )
                raise
            
    def flush(self, timeout: float = 10.0):
        self.producer.flush(timeout)


class KafkaConsumerClient:
    def __init__(self, bootstrap_servers: str, group_id: str, topics: list[str],
                 auto_offset_reset: str = "earliest"):
        self.consumer = Consumer({
            "bootstrap.servers": bootstrap_servers,
            "group.id": group_id,
            "auto.offset.reset": auto_offset_reset,
            "enable.auto.commit": False,   # manual commit after successful processing
        })
        self.consumer.subscribe(topics)
        self.topics = topics

    def poll_loop(self, handler: Callable[[dict, str], None],
                  on_error: Optional[Callable[[Exception, bytes], None]] = None,
                  poll_timeout: float = 1.0):
        """
        Blocking poll loop. `handler(parsed_json, raw_key)` is called per message.
        If handler raises, `on_error(exception, raw_bytes)` is called (e.g. to push
        to a dead-letter-queue) and the loop continues rather than crashing.
        """
        logger.info(f"Starting consume loop for topics={self.topics}")
        try:
            while True:
                msg = self.consumer.poll(poll_timeout)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    logger.error(f"Kafka consumer error: {msg.error()}")
                    continue

                raw_value = msg.value()
                try:
                    parsed = json.loads(raw_value.decode("utf-8"))
                    key = msg.key().decode("utf-8") if msg.key() else None
                    handler(parsed, key)
                    self.consumer.commit(msg)
                except Exception as e:
                    logger.exception(
                        "Failed to process Kafka message "
                        "topic=%s partition=%s offset=%s: %s",
                        msg.topic(),
                        msg.partition(),
                        msg.offset(),
                        e,
                    )

                    if on_error is None:
                        logger.error(
                            "No error handler configured; message will NOT be committed."
                        )
                        continue

                    try:
                        on_error(e, raw_value)

                        # Only commit after the failure was successfully handled.
                        self.consumer.commit(msg)

                        logger.warning(
                            "Failed message sent to error handler and committed "
                            "topic=%s partition=%s offset=%s",
                            msg.topic(),
                            msg.partition(),
                            msg.offset(),
                        )

                    except Exception:
                        logger.exception(
                            "Error handler failed; message will NOT be committed "
                            "and can be retried."
                        )
        except KeyboardInterrupt:
            logger.info("Consumer loop interrupted, shutting down")
        finally:
            self.consumer.close()
