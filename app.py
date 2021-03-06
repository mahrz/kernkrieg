from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.bcrypt import Bcrypt
from redis import Redis
from rq_scheduler import Scheduler
import rq

app = Flask(__name__, static_folder = './angular/app', static_url_path='/app')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db' #'sqlite:///kurs.db' #
app.config['SECRET_KEY'] = "KERNKRIEGFTW"
app.config['QUEUE_DIR'] = "/tmp/kk-queues"
app.config['MATCHES_PER_QUEUE_UPDATE'] = -1
app.config['SECONDS_PER_QUEUE_UPDATE'] = 30
app.config['HIDE_MATCHES'] = True
app.config['HIDE_TESTS'] = True

db = SQLAlchemy(app)

bcrypt = Bcrypt()
bcrypt.init_app(app)

# Tell RQ what Redis connection to use
redis_conn = Redis()

# Redis Queue

q = rq.Queue(connection=redis_conn)
match_q = rq.Queue('matches', connection=redis_conn)
test_q = rq.Queue('tests', connection=redis_conn)
scheduler = Scheduler(connection=redis_conn)