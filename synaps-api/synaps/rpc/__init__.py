# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2011 Red Hat, Inc.
# Copyright (c) 2012 Samsung SDS Co., LTD
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from synaps import flags
from synaps.utils import strtime
from synaps import log as logging
from synaps.exception import RpcInvokeException
import uuid

import pika, json

LOG = logging.getLogger(__name__)
FLAGS = flags.FLAGS

PUT_METRIC_DATA_MSG_ID = 0x0001
PUT_METRIC_ALARM_MSG_ID = 0x0002
DISABLE_ALARM_ACTIONS = 0x0003
ENABLE_ALARM_ACTIONS = 0x0004
DELETE_ALARMS_MSG_ID = 0x0005
SET_ALARM_STATE_MSG_ID = 0x0006
CHECK_METRIC_ALARM_MSG_ID = 0x0010 


class RemoteProcedureCall(object):
    def __init__(self):
        self.connect()
    
    def connect(self):
        host = FLAGS.get('rabbit_host')
        port = FLAGS.get('rabbit_port')
        try:
            LOG.info(_("connecting to rabbit_host %s %d") % (host, port))

            self.conn = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=FLAGS.get('rabbit_host'),
                    port=FLAGS.get('rabbit_port'),
                    credentials=pika.PlainCredentials(
                        FLAGS.get('rabbit_userid'),
                        FLAGS.get('rabbit_password')
                    ),
                    virtual_host=FLAGS.get('rabbit_virtual_host'),
                )
            )
            
            self.channel = self.conn.channel()
            queue_args = {"x-ha-policy" : "all" }
            self.channel.queue_declare(queue='metric_queue', durable=True,
                                       arguments=queue_args)
        except Exception as e:
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

        message_uuid = str(uuid.uuid4()) 
        body.setdefault('message_id', message_id)
        body.setdefault('message_uuid', message_uuid)
        
        self.channel.basic_publish(
            exchange='', routing_key='metric_queue', body=json.dumps(body),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        
        LOG.info(_("send_msg - id(%03d), %s") % (message_id, message_uuid))
        LOG.debug(_("send_msg - body(%s)") % str(body))
