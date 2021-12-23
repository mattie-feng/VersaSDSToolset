# -*- coding: utf-8 -*-
from vplx_app import create_app
import sys 
sys.path.append("..")
import log

log.Log.filename = log.WEB_LOG_NAME
logger = log.Log()
app = create_app()

if __name__ == '__main__':
  app.run(host='0.0.0.0',  # 任何ip都可以访问
      port=7777,  # 端口
      debug=True,
      threaded=True
      )

