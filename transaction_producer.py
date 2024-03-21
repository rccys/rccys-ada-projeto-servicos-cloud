import datetime
import time
import uuid
import pika
import json

# Cria conexão com o RabbitMQ
connection_rabbmitmq = pika.BlockingConnection(
    pika.ConnectionParameters(host="localhost", 
                              port=5672, 
                              virtual_host="/")
)

channel = connection_rabbmitmq.channel()


properties = pika.BasicProperties(
    app_id="transaction_producer", 
    content_type="application/json"
)


transaction_file = open("transaction.json")

transaction = json.load(transaction_file)

transaction_file.close()

# envia a transação para o RabbitMQ inseirindo o ID da transação e a data
for transaction in transaction:
    transaction["transaction_id"] = str(uuid.uuid4())
    transaction["date"] = str(datetime.datetime.now())
        
    channel.basic_publish(exchange="amq.fanout", 
                          routing_key="", 
                          body=json.dumps(transaction), 
                          properties=properties)

    print(f"Transação efetuada: '{json.dumps(transaction)}'\n")

    time.sleep(2)

channel.close()
