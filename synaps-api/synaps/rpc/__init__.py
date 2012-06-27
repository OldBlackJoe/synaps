# Copyright 2012 Samsung SDS
# All Rights Reserved

from synaps import flags
from synaps.utils import strtime
from synaps import log as logging
from synaps.exception import RpcInvokeException

import pika, json

LOG = logging.getLogger(__name__)
FLAGS = flags.FLAGS

PUT_METRIC_DATA_MSG_ID = 0x0001
PUT_METRIC_ALARM_MSG_ID = 0x0002
DISABLE_ALARM_ACTIONS = 0x0003
ENABLE_ALARM_ACTIONS = 0x0004
DELETE_ALARMS_MSG_ID = 0x0005
SET_ALARM_STATE_MSG_ID = 0x0006


class RemoteProcedureCall(object):
    def __init__(self):
        self.connect()
    
    def connect(self):
        try:
            LOG.info(_("connecting to rabbitmq_server"))
            self.conn = pika.BlockingConnection(
                pika.ConnectionParameters(host=FLAGS.get('rabbitmq_server'))
            )
            
            self.channel = self.conn.channel()
            queue_args = {"x-ha-policy" : "all" }
            self.channel.queue_declare(queue='metric_queue', durable=True,
                                       arguments=queue_args)
        except:
            raise RpcInvokeException()
    
    def send_msg(self, message_id, body):
        """
        
        
        Args:
            message_id: int
                ex) PUT_METRIC_DATA_MSG_ID (0x0001)
                    PUT_METRIC_ALARM_MSG_ID (0x0002)
                    ...
            body: dict object (will be converted into json format)
            
        """
        if type(message_id) is not int:
            raise RpcInvokeException()
        
        if not self.conn.is_open:
            self.connect()

        body.setdefault('message_id', message_id)
        self.channel.basic_publish(
            exchange='', routing_key='metric_queue', body=json.dumps(body),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        
        LOG.info(_("send_msg - id(%03d)") % message_id)
        LOG.debug(_("send_msg - body(%s)") % str(body))
