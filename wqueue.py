# App
from app import app, db, scheduler, q, match_q, test_q
from flask.ext.login import current_user
from models import Warrior, Submission, Match, Queue
from flask import abort
from datetime import datetime
from jobs import run_match
import math
import random

def frontend_submit_to_queue(q, w_id):
    w = Warrior.query.filter(Warrior.id == w_id).first()
    if not w:
        abort(404)
    if not q.isOpen:
        abort(401)
    # Only an owner, or the admin can submit to the queue
    # Testables can be submitted to a test queue
    if (not (q.qType == 0 and w.testable)) and (not current_user.admin):
        is_owner = False
        for o in w.owners:
            if o.id == current_user.id:
                is_owner = True
        if not is_owner:
            abort(401)

    sub = Submission(name=w.name,
                     authors=w.authors(),
                     code=w.code,
                     submitted=datetime.now(),
                     submissionUserId=current_user.id,
                     queueId=q.id,
                     warriorId=w.id)
    # Todo respect subs per warrior

    # Todo respect subs per user
    user_subs = Submission.query.filter(Submission.active == True).filter(Submission.submissionUserId == current_user.id).filter(Submission.queueId == q.id).count()
    warrior_subs = Submission.query.filter(Submission.active == True).filter(Submission.warriorId == w.id).filter(Submission.queueId == q.id).count()
    if q.qType != 0 and ((user_subs >= q.maxSubsPerUser and q.maxSubsPerUser > -1) or (warrior_subs >= q.maxSubsPerWarrior and q.maxSubsPerWarrior > -1)):
        abort(401)
    db.session.add(sub)
    db.session.commit()

    return sub

def schedule_queue(q):
    job = scheduler.schedule(
        scheduled_time=datetime.now(),
        func=queue_job,
        args=[q.id],
        interval=app.config['SECONDS_PER_QUEUE_UPDATE'],
        repeat=None
        )
    print("Scheduled periodic job for queue: " + str(job.id))
    return job.id


def queue_job(q_id):
    print("Running queue job for id " + str(q_id))
    remaining_matches = match_q.count
    queue = Queue.query.get(q_id)
    if not queue:
        print("Queue not existing")
        return
    if not queue.active:
        print("Queue not longer active stopping")
        queue.stop_queue();
        return
    if queue.qType != 2:
        print("Queue not of schedule type")
        queue.stop_queue();
        return
    subs_query = Submission.query.filter(Submission.queueId == q_id).filter(Submission.active == True)
    num_of_subs = subs_query.count()

    if app.config['MATCHES_PER_QUEUE_UPDATE'] == -1:
        app.config['MATCHES_PER_QUEUE_UPDATE'] = num_of_subs

    new_matches = app.config['MATCHES_PER_QUEUE_UPDATE'] - remaining_matches

    if remaining_matches > 0:
        app.config['MATCHES_PER_QUEUE_UPDATE'] = math.ceil(app.config['MATCHES_PER_QUEUE_UPDATE']*0.9)
    elif app.config['MATCHES_PER_QUEUE_UPDATE'] < num_of_subs:
        app.config['MATCHES_PER_QUEUE_UPDATE'] = math.ceil(app.config['MATCHES_PER_QUEUE_UPDATE']*1.1)

    if new_matches < 0:
        new_matches = 1

    print("New matches: " + str(new_matches))
    subs = subs_query.order_by(Submission.sigma.desc()).all()
    print(subs)
    for i in range(0,new_matches):
        dmin = 100000000
        the_op = None
        for op in subs:
            if op.id != subs[i].id:
                d = abs(op.mu - subs[i].mu)
                if d < dmin:
                    dmin = d
                    the_op = op
        if the_op:
            print("Schedule match "  + str(subs[i].id) + " vs. " + str(the_op.id))
            schedule_match(queue, subs[i], the_op)
    print("Done running queue job")

def schedule_match(queue, sub1, sub2, test=False):
    match = Match(done=False,
                  scheduled=datetime.now(),
                  executed=None,
                  winner=-1,
                  seed=random.randint(1, 1000000),
                  participant1Id=sub1.id,
                  participant2Id=sub2.id,
                  queueId=queue.id)
    db.session.add(match)
    db.session.commit()
    job = ""
    if test:
      job = test_q.enqueue(run_match, match.id)
    else:
      job = match_q.enqueue(run_match, match.id)
    match.job = job.id
    db.session.commit()
    return match

# Todo
# resubmit
# copy_submission

# @app.route('/make/')
# def make():
#     job = q.enqueue(stuff, 'argument')
#     session['job'] = job.id
#     return job.id

# @app.route('/get/')
# def get():

#     job = rq.job.Job.fetch(session['job'], connection=redis_conn)
#     out = str(job.result)
#     #except:
#     #    out = 'No result yet'
#     return out