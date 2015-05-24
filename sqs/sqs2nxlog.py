#!/usr/bin/env python

import boto.sqs,os,json,sys,socket,time

class MyConfig:
  def __init__(self,config_file="sqs2nxlog.conf"):
    with open(config_file) as json_data_file:
        data = json.load(json_data_file)
    self.settings = data
    
if __name__ == "__main__":
  try:
    c = boto.sqs.connect_to_region(os.environ['AWS_DEFAULT_REGION'])
  except Exception as e:
    print "Error:",e 
    sys.exit(-1)

  cfg = MyConfig()
  mon_q = []

  # get_queue is failing for some reason
  for q in c.get_all_queues():
    if q.name in cfg.settings['input_queues']:
      print "Found", q.name, q.count()
      mon_q.append(q)

  for q in mon_q:
    m = c.receive_message(q,wait_time_seconds=3)

    print len(m), "messages left"
    while len(m) >0:
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.connect(('127.0.0.1', 1514))

        
      raw_message = m[0].get_body()
      json_m = json.loads(raw_message)
      final_m = {}

      rh = str(m[0].receipt_handle)
      c.delete_message_from_handle(q,rh)
      final_m['Subject'] = json_m['Subject']
      final_m['Payload'] = json_m['Message']
      final_m['Timestamp'] = json_m['Timestamp']

      print "Sending:\n", json.dumps(final_m)
      s.send(json.dumps(final_m)+'\r\n')
      s.close()
      m = c.receive_message(q,wait_time_seconds=3)
