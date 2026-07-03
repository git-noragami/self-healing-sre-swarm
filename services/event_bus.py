import json
import time
import redis

class EventBus:
    """
    A unified broker engine wrapping Redis Streams primitives.
    Provides standardized channels for metric alarms and structural anomalies.
    """
    def __init__(self, host="redis", port=6379, stream_name="infrastructure_events"):
        # We use a connection pool to safely reuse sockets across async transactions
        self.pool = redis.ConnectionPool(host=host, port=port, decode_responses=True)
        self.client = redis.Redis(connection_pool=self.pool)
        self.stream_name = stream_name

    def publish_event(self, event_type: str, source_service: str, details: dict):
        """
        Pushes a structured operational payload into the append-only stream.
        """
        payload = {
            "event_type": event_type,        # e.g., "ERROR_SPIKE", "CONTAINER_DOWN"
            "source": source_service,        # e.g., "payments-service"
            "timestamp": str(time.time()),
            "details": json.dumps(details)    # Serialize complex attributes safely as JSON strings
        }
        # XADD appends the data to the stream. '*' instructs Redis to autogenerate a unique ID
        return self.client.xadd(self.stream_name, payload)

    def read_new_events(self, last_id="$", count=10):
        """
        Polls the stream for unread events since the provided event ID.
        """
        # XREAD reads data from the stream sequentially
        streams = {self.stream_name: last_id}
        results = self.client.xread(streams, count=count, block=1000) # Block for up to 1000ms if empty
        
        events = []
        if results:
            for stream, records in results:
                for record_id, record_dict in records:
                    record_dict["id"] = record_id
                    record_dict["details"] = json.loads(record_dict["details"])
                    events.append(record_dict)
        return events