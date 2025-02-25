
from services.aws_sqs import blueprint
from flask import request, json, Response
from redis import Redis
import logging, boto3, hashlib
from decimal import Decimal
from services import AWS_ACCESS_KEY, AWS_SECRET_KEY, STORAGE_URL
from services.aws_rekognition.routes import detect_labels
from services.aws_dynamo.routes import get_data_from_md5, update_key
from services.aws_elasticache.routes import put_cache
from services.aws_opensearch.routes import put_search_index

@blueprint.route('/producer',methods=['POST'])
def produce_queue(key=None, img=None):
    keyName = key or request.form.get('key')
    img = img or request.form.get('key_imgmd5')
    key_md5 = hashlib.md5(keyName.encode()).hexdigest()
    
    print(key_md5)
    jsonObj={
        'key_md5': key_md5,
        'key': keyName,
        'img': img
    }
    logging.basicConfig(level=logging.INFO)
    # redis = Redis(host=REDIS_ENDPOINT, port=6379, decode_responses=True, ssl=True, username='myuser', password='MyPassword0123456789')
    # Get the service resource
    sqs = boto3.resource('sqs',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name='us-east-1')
    
    # Get the queue
    queue = sqs.get_queue_by_name(QueueName='cc-photoalbum')

   # Create a new message
    response = queue.send_message(MessageBody=json.dumps(jsonObj))

    # The response is NOT a resource, but gives you a message ID and MD5
    if response:
        success=True
    else:
        success=False

    return Response(json.dumps({"success": success, "data":{"MessageId": response.get('MessageId'), "MD5OfMessageBody": response.get('MD5OfMessageBody'), "response": response}}, default=str), status=200, mimetype='application/json')


@blueprint.route('/consumer',methods=['POST'])
#Upload a new file to an existing bucket
def consume_queue():
    # Get the service resource
    sqs = boto3.resource('sqs',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name='us-east-1')

    # Get the queue
    queue = sqs.get_queue_by_name(QueueName='photoalbum.fifo')
    # print(queue)
    # Process messages by printing out body and optional author name
    i=0
    j=0
    # print(queue.receive_messages())
    for message in queue.receive_messages():
        # need to call rekognition
        print('Hello, {0}'.format(message.body))
        print('test')
        key_md5=message.body
        val_from_db=json.loads(get_data_from_md5('key_md5', key_md5).data)['content']
        print(val_from_db)
        img_lbl=json.loads(detect_labels(val_from_db['img_url']).data, parse_float=Decimal)
        print(img_lbl)
        response_from_db=json.loads(update_key(val_from_db['key'], val_from_db['img_url'], img_lbl['attributes'], img_lbl['labels'], img_lbl['categories']).data)
        put_cache(val_from_db['key'], val_from_db['img_url'], img_lbl['labels'], img_lbl['categories'])
        put_search_index(key_md5, val_from_db['key'], val_from_db['img_url'], img_lbl['labels'], img_lbl['categories'])
        if response_from_db['success']:
            response = message.delete()
            if response: 
                print(response)
                i=i+1
            else:
                print(response)
                j=j+1

    if len(queue.receive_messages())==0:
        msg="Nothing to consume"
        success=True
    else:
        success=True
        msg="Total " + str(i) + " keys consumed successfully and " + str(j) + " keys consumption failed"

    
    return Response(json.dumps({"success": success, "data":{"msg": msg}}, default=str), status=200, mimetype='application/json')