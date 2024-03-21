import datetime
import io
import json
from minio import Minio
import pika
import redis

quantity_previous_transactions = 5

# Cria conexão com o RabbitMQ
connection_rabbmitmq = pika.BlockingConnection(pika.ConnectionParameters(
    host="localhost",
    port=5672,
    virtual_host="/"))

channel = connection_rabbmitmq.channel()
print("Conectado ao RabbitMQ")

# Cria conexão com o Redis
connection_redis = redis.Redis(host='localhost', port=6379, db=0)
print("Conectado ao Redis")

queue_name = "fraud_detector_queue"

channel.queue_declare(queue=queue_name)
channel.queue_bind(exchange="amq.fanout", queue=queue_name)

# Função para upload do relatório de fraude no minio
def upload_fraud_report_to_minio(steam:io.StringIO, file_name, length:int):
    connection_minio = Minio(
        endpoint="localhost:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
        secure=False)

    bucket_name = "fraud-bucket"
    bucket_exists = connection_minio.bucket_exists(bucket_name)

    # verificando se o bucket existe
    if bucket_exists:
        print(f"O bucket {bucket_name} existe.")
    else:
        connection_minio.make_bucket(bucket_name)
        print(f"Bucket {bucket_name} criado com sucesso.")

    binaryIO = io.BytesIO(steam.getvalue().encode("utf-8"))    
    connection_minio.put_object(bucket_name=bucket_name, 
                                object_name=file_name, 
                                data=binaryIO, 
                                length=-1,
                                part_size=10*1024*1024, 
                                content_type="text/plain")
    
    print(f"Arquivo {file_name} enviado para o bucket {bucket_name} com sucesso.")
    
    url_get = connection_minio.get_presigned_url(
        method="GET",
        bucket_name=bucket_name,
        object_name=file_name)

    print(f"Link para dowloand do arquivo {url_get} \n")

    connection_redis.set(file_name, url_get)

# Função para retonar a média do valor das transações
def get_state_transaction(transactions):
    if transactions:  # Check if transactions is not empty
        return transactions[-1]["state"]  # Get the "state" from the last transaction

def creates_fraud_report(account_number, previous_transactions, current_transaction):
    print("Relatorio de fraude")
    state_current = current_transaction["state"]
    state_previous = previous_transactions[-1]["state"]

    date_current_str = current_transaction["date"]
    date_current_datetime = datetime.datetime.strptime(date_current_str, "%Y-%m-%d %H:%M:%S.%f")

    date_previous_str = previous_transactions[-1]["date"]
    date_previous_datetime = datetime.datetime.strptime(date_previous_str, "%Y-%m-%d %H:%M:%S.%f")

    delta_time = date_current_datetime - date_previous_datetime

    file_stream = io.StringIO()
    file_stream.write(f"Numero da conta: {current_transaction['account_number']}\n")
    length = file_stream.write("Transacao atual: {}\n".format(current_transaction))

    # Escreve no file stream o conteúdo do relatório de fraude
    #file_stream.write(f"Account Number: {current_transaction['account_number']}\n")
        
    file_stream.write(f"Transacoes anteriores: {previous_transactions}\n")

    file_stream.write(f"Estado onde foi realizada a transacao anterior {state_previous}\n") 
    file_stream.write(f"Estado onde foi realizada a transacao atual {state_current}\n") 
    file_stream.write(f"Diferenca de tempo entre a realizacao da transacao atual (fraude) e a anterior (nao fraude): {delta_time}")

    # Reinicia o conteúdo do file stream
    file_stream.seek(0)
    
    file_name = f"relatorio_de_fraude-conta-{account_number}-transacao-{current_transaction['transaction_id']}.txt"

    upload_fraud_report_to_minio(file_stream, file_name, length)
  

    file_stream.close()



# Função para consumir a mensagem do RabbitMQ
def message_transaction_consumed(channel, method_frame, header_frame, body):
    # Decodificar a mensagem JSON recebida
    current_transaction = json.loads(body.decode("utf-8"))
    print("Transação: ", current_transaction)

    account_number = current_transaction["account_number"]
    state_current = current_transaction["state"]
    date_current_str = current_transaction["date"]
    date_current_datetime = datetime.datetime.strptime(date_current_str, "%Y-%m-%d %H:%M:%S.%f")
    
    
    result_previous_transaction = connection_redis.get(account_number)
    
    if result_previous_transaction is None:
        transactions = [current_transaction]
        connection_redis.set(account_number, json.dumps(transactions))
    else:
        previous_transactions = json.loads(result_previous_transaction)
        state_previous_transaction = get_state_transaction(previous_transactions)
        print("Estado onde foi realizada a transação: ", state_current, "\n")

        date_previous_str = previous_transactions[-1]["date"]
        date_previous_datetime = datetime.datetime.strptime(date_previous_str, "%Y-%m-%d %H:%M:%S.%f")

        delta_time = date_current_datetime - date_previous_datetime

        # Indica se houve transação em outro estado em menos de uma hora, se a condição for verdadeira
        # indica que houve fraude
        fraud_condition = (state_current != state_previous_transaction) and (delta_time.total_seconds() < 3600)

        if fraud_condition:
            print(f"Transação fraudulenta na conta {account_number}. Id da transação: {current_transaction['transaction_id']}")
            creates_fraud_report(account_number, previous_transactions, current_transaction)

        if len(previous_transactions) >= quantity_previous_transactions:
            previous_transactions.pop(0)

        # condição para não enviar transação fraudulenta para o cache, 
        # evita que transações válidas sejam consideradas como fraudulentas
        # pois a comparação entre os estados onde foram feitas as transações
        # teria o estado onde ocorreu a fraude
        if fraud_condition == False:
            previous_transactions.append(current_transaction)
            connection_redis.set(account_number, json.dumps(previous_transactions))


channel.basic_consume(queue=queue_name, on_message_callback=message_transaction_consumed, auto_ack=True)

print("Esperando por mensagens. Para sair pressione CTRL+C")
channel.start_consuming()