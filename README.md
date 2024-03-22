# Como executar o projeto
Execute os passos abaixo em ordem sequencial.

Faça o download do projeto ou um git pull.

## Definição de Fraude
Se houve transação em outro estado em menos de uma hora, sidnifica que ocorreu fraude.

Obs.: se for identificada um fraude a transação fraudulenta não será enviada para o cache, isso evita que transações válidas sejam consideradas como fraudulentas, pois a comparação entre os estados onde foram realizadas as transações teria o estado onde ocorreu a fraude devido à consulta ao cache.

## Ferramentas que devem ser instaladas
[Docker]https://www.docker.com/products/docker-desktop/

[Python3]https://www.python.org/downloads/

[pip]https://pip.pypa.io/en/stable/installation/

## Python dependencies
  
```BASH
# é necessário ter o pip instalado

# abra um terminal e excute as instalções abaixo:

# instalação do RabbitMQ
pip install pika

# instalação do Redis
pip install redis

# instalação do MinIO
pip install minio

```

## Containers Docker

```BASH
# inicie o docker desktop 

# abra um terminal e excute o comando abaixo:
# RabbitMQ
docker run -it --rm --name rabbitmq -p 15672:15672 -p 5672:5672 rabbitmq:3-management
# após execução do comando o terminal pode ser fechado
```
[acessar interface](http://localhost:15672)
user: guest
password: guest

```BASH
# abra um terminal e excute o comando abaixo:
# Redis
docker run -it --rm --name redis-stack -p 6379:6379 -p 8001:8001 redis/redis-stack:latest
```
[acessar interface](http://localhost:8001)

```BASH
# abra um terminal e excute o comando abaixo:
# Minio
docker run --rm -p 9000:9000 -p 9001:9001 quay.io/minio/minio server /data --console-address ":9001"
```
[acessar interface](http://localhost:9001)
user: minioadmin
password: minioadmin

## Execução dos códigos
```BASH
# Abra um terminal, navegue até a pasta onde foi realizado o dowloand do projeto.
# Abra um segundo terminal, navegue até a pasta onde foi realizado o dowloand do projeto.
# No primeiro terminal execute o código abaixo:
python fraud_detector_consumer.py

# No segundo terminal excute o código abaixo:
python transaction_producer.py

```
