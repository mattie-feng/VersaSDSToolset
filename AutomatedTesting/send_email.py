# coding:utf8
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class Email(object):
    def __init__(self, config, timeout=8):
        self.config = config
        self.email_config = self.config.get_email()
        self._enable = self.email_config["enable"]
        self._host = self.email_config["host"]
        self._port = self.email_config["port"]
        self._sender = self.email_config["sender"]
        self._password = self.email_config["password"]
        self._receiver_list = self.email_config["receiver_list"]
        self._receiver = ','.join(self._receiver_list)
        self._encrypt = self.email_config["encrypt"]
        self._anonymous = False
        self._timeout = timeout

    def _package_msg(self, title, content):
        msg = MIMEMultipart()
        msg['Subject'] = title
        msg['From'] = self._sender
        msg['To'] = self._receiver
        context = MIMEText(content, _subtype='html', _charset='utf-8')
        msg.attach(context)
        return msg

    def email_switch(func):
        def send(self, *args):
            if self._enable is True:
                return func(self, *args)
            else:
                print("The email switch is off.")

        return send

    def _connect_login(self):
        try:
            if self._encrypt == 'ssl':
                send_smtp = smtplib.SMTP_SSL(self._host, self._port, timeout=self._timeout)
                send_smtp.connect(self._host)
            else:
                send_smtp = smtplib.SMTP(timeout=self._timeout)
                if self._encrypt == 'tls':
                    send_smtp.connect(self._host, self._port)
                    send_smtp.ehlo()
                    send_smtp.starttls()
                else:
                    send_smtp.connect(self._host, self._port)
                    send_smtp.ehlo()
        except:
            print("Failed to connect smtp server!")
            return False
        try:
            send_smtp.login(self._sender, self._password)
        except:
            print("User or Password is wrong")
            return False
        return send_smtp

    def _connect_login_anonymous(self):
        try:
            if self._encrypt == 'ssl':
                send_smtp = smtplib.SMTP_SSL(self._host, self._port, timeout=self._timeout)
            else:
                send_smtp = smtplib.SMTP(self._host, self._port, timeout=self._timeout)
            return send_smtp
        except:
            print("The Host unable to connect!")
            return False

    def _send_mail(self, title, content):
        if self._anonymous is True:
            send_smtp = self._connect_login_anonymous()
        else:
            send_smtp = self._connect_login()
        if send_smtp:
            try:
                msg = self._package_msg(title, content)
                send_smtp.sendmail(
                    self._sender, self._receiver_list, msg.as_string())

            except:
                print("Send Fail, Please check receiver_list.")
                return
        else:
            return
        send_smtp.close()
        print("Send success!")

    @email_switch
    def send_autotest_mail(self):
        content = """\
                <html>
                <head>
                    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
                    <title>自动化测试</title>
                </head>
                <body>
                    <div id="container">
                        <p><strong>测试已结束，请查收测试结果。</strong></p>
                    </div>
                </body>
                </html> """
        title = "自动化测试"
        self._send_mail(title, content)

    @email_switch
    def send_alive_mail(self):
        title = "邮件测试"
        content = "I'm still alive"
        self._send_mail(title, content)
