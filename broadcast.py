from flask import Flask, request, render_template, abort, jsonify,redirect , url_for, session
import requests
import sqlite3
from datetime import datetime
from flask_login import current_user

webapp = Flask(__name__)
webapp.secret_key = '=g8Z&KUak&dKKe*P&*8q'

email_to_ldap_map = {}
email_to_name_map = {}

'''
 get the logged in user's email address and admin status from session variables
'''

def get_user():
  return session['username']

def get_status():
  return session['admin_status']


'''
  Below are the functions for page routes
'''
# page routes
@webapp.route('/home', defaults={'user': None}, methods=["GET"])
@webapp.route('/home/<user>', methods=["GET"])
def render_home(user):
  if user:
    session['username'] = user
    session['admin_status'] = get_admin_status(user)
  logged_user = get_user()
  admin = get_status()
  get_user_videos(logged_user)
  user_video = session['user_video']
  return render_template('home.html', result = user_video, user=logged_user, admin=admin)


@webapp.route("/videoupload")
def render_videoupload():
  logged_user = get_user()
  admin = get_status()
  return render_template('uploadvideo.html',user=logged_user, admin=admin)


@webapp.route('/myvideos', methods=["GET"])
def render_myuploads():
  logged_user = get_user()
  get_owner_videos(logged_user)
  admin = get_status()
  owner_video = session['owner_video']
  return render_template('myuploads.html', result = owner_video, user=logged_user, admin=admin)


@webapp.route("/manageusers")
def render_manageuser():
  logged_user = get_user()
  admin = get_status()
  return render_template('manageusers.html',user=logged_user, admin=admin)


# AJAX calls
@webapp.route("/searchHome" , methods=["GET","POST"])
def searchHome():
  key = request.form['key']
  data = []
  user_video = session['user_video']
  if not key:
    data = user_video
  else:
    for rec in user_video:
      if rec[0].lower().find(key.lower()) != -1 or rec[2].lower().find(key.lower()) != -1: # title and description
        data.append(rec)
  return render_template('generateFrame.html', result = data)


@webapp.route("/searchmyvideo" , methods=["GET","POST"])
def searchmyvideo():
  key = request.form['key']
  data = []
  owner_video = session['owner_video']
  if not key:
    data = owner_video
  else:
    for rec in owner_video:
      if rec[0].lower().find(key.lower()) != -1 or rec[2].lower().find(key.lower()) != -1: #title and description
        data.append(rec)
  return render_template('generateMyVideoFrames.html', result = data)


@webapp.route("/deleteVideo" , methods=["GET","POST"])
def deleteVideo():
  video_id = request.form['key']
  data = []
  delete_helper(video_id)
  logged_user = get_user()
  get_owner_videos(logged_user)
  owner_video = session['owner_video']
  return render_template('generateMyVideoFrames.html', result = owner_video)


@webapp.route("/updateVideo", methods=["GET","POST"])
def updateVideo():
  logged_user = get_user()
  title = request.form['title']
  url = request.form['url']
  desc = request.form['desc']
  users = request.form['users']
  video_id = request.form['video_id']
  users = users.split(',')
  update_video_helper(video_id, title, desc)
  updateUsers(video_id, users,logged_user)
  get_owner_videos(logged_user)
  owner_video = session['owner_video']
  return render_template('generateMyVideoFrames.html', result = owner_video)


# JSON calls
@webapp.route("/search_users")
def search_users():
  search_key = request.args.get('search_key')
  res = dict(filter(lambda item: search_key.lower() in item[0].lower(), email_to_name_map.items()))
  res = [email for email in res.keys()]
  return jsonify(res)


@webapp.route("/uploadNewVideo")
def uploadNewVideo():
  title = request.args.get('title')
  url = request.args.get('url')
  description = request.args.get('description')
  users = request.args.get('users')
  users = users.split(',')
  logged_user = get_user()
  print(logged_user,url, title, description, users)
  res = upload_video(logged_user,url, title, description, users)
  return jsonify(res)


@webapp.route("/addnewuser")
def addnewuser():
  first_name = request.args.get('first_name')
  last_name = request.args.get('last_name')
  email_id = request.args.get('email_id')
  phone_number = request.args.get('phone_number')
  admin = request.args.get('admin_status')
  res = add_new_user_db(first_name, last_name, email_id, phone_number, admin)
  return jsonify(res)


@webapp.route("/get_video_watcher_list")
def get_video_watcher_list():
  video_id = request.args.get('video_id')
  res = get_video_users(video_id)
  return jsonify(res)


@webapp.route("/setallusers")
def setallusers():
  get_all_users()
  return jsonify(len(email_to_name_map))


#helper functions.
def get_all_users():
  global email_to_ldap_map
  global email_to_name_map
  
  connection = get_db_connection()
  cursor = connection.cursor()
  cursor.execute("select ud.email_id, ud.first_name, ud.last_name from \
                  user_details ud ")
  records = cursor.fetchall()

  for rec in records:
    print(rec)
    email_to_ldap_map[rec[0]] = rec[1] +', '+rec[2]
    email_to_name_map[rec[0]+'('+rec[1]+','+rec[2]+')'] = 1


def get_admin_status(email_id):
  connection = get_db_connection()
  cursor = connection.cursor()
  cursor.execute("select admin_account from user_details where email_id = ? ; ",[email_id])
  records = cursor.fetchall()
  return records[0][0]


def get_user_videos(email_id): # videos of the logged in user
  connection = get_db_connection()
  records = []
  try:
    cursor = connection.cursor()
    cursor.execute("select vd.title, vd.url, vd.description, vd.uploaded_by, vd.created_date, uvm.mapping_id from \
                    video_details vd, \
                    user_video_mappings  uvm\
                    where 1=1 \
                      and vd.video_id = uvm.video_id \
                      and uvm.email_id = ? \
                    order by vd.created_date desc",[email_id])
    records = cursor.fetchall()
    session['user_video'] = records
  except:
    session['user_video'] = []


def upload_video(email_id, url, title, description, user_list):
  connection = get_db_connection()
  try:
    new_url = url.replace('view?usp=sharing','preview')
    cursor = connection.cursor()
    cursor.execute('select * from video_details where url = ? ;',[new_url])
    result = cursor.fetchone()

    if result:
      return 'Video already exists. Please visit My Uploads page to manage your videos.'
    else:
      insert_video_sql = 'insert into video_details ( url, title, description, uploaded_by, created_date) \
                          values (?,?,?,?,?)'
      video_values = [new_url, title, description, email_id, datetime.now()]
      cursor.execute(insert_video_sql, video_values)
      connection.commit()
      video_id = cursor.lastrowid
      users = { x for x in user_list}
      users.add(email_id)
      invalid_users = update_user_mapping(video_id, users)
      usr_msg = ''
      if invalid_users:
        usr_msg = 'Following users are invalid. '+','.join(user for user in invalid_users)
      return 'Video uploaded successfully.' + usr_msg
  except sqlite3.Error as e:
    print(e)
    return 'Error uploading the video. Please try again or contact support at broadcast_support@madrascoders.com'


def update_user_mapping(video_id, userlist):
  invalid_users = []
  connection = get_db_connection()
  cursor = connection.cursor()

  for email_id in userlist:
    try:
      video_mapping_sql = 'insert into user_video_mappings (email_id, video_id, created_date)\
                            values(?,?,?)'
      user_values = [email_id, video_id, datetime.now()]
      cursor.execute(video_mapping_sql, user_values)
      connection.commit()
    except:
      invalid_users.append(email_id)
      continue
  return invalid_users


def add_new_user_db(first_name, last_name, email_id, phone_number, admin):
  connection = get_db_connection()
  cursor = connection.cursor()

  cursor.execute('select 1 from user_details where email_id = ? ;',[email_id])
  result = cursor.fetchone()
  if result:
    return 'User with same email address already present. Please retry with a different email address'
  else:
    try:
      insert_sql = 'insert into user_details (first_name, last_name, email_id, phone_num, admin_account) \
                    values (?,?,?,?,?);'

      values = [first_name, last_name, email_id, phone_number, admin] 
      cursor.execute(insert_sql, values)
      connection.commit()
      return 'User added succesfully'
    except sqlite3.Error as e:
      print(e)
      return 'Adding user failed. Please retry'


def delete_helper(video_id):
  connection = get_db_connection()
  if not connection:
    print('Failed')
  cursor = connection.cursor()
  cursor.execute('delete from video_details where video_id = ?',[(video_id)])
  cursor.execute('delete from user_video_mappings where video_id = ?',[(video_id)])
  connection.commit()
  return None


def update_video_helper(video_id, title, description):
  connection = get_db_connection()
  if not connection:
    print('Failed')
  cursor = connection.cursor()
  cursor.execute('update video_details \
                     set title = ? \
                        ,description = ? \
                   where video_id = ?',[(title, description, video_id)])
  connection.commit()
  return None


def updateUsers(video_id, user_list,email_id):
  connection = get_db_connection()
  if not connection:
    print('Failed')
  cursor = connection.cursor()
  cursor.execute('delete from user_video_mappings where video_id = ?',[(video_id)])
  connection.commit()
  users = {x for x in user_list}
  users.add(email_id)
  update_user_mapping(video_id, users)
  return None


def get_video_users(video_id):

  connection = get_db_connection()
  if not connection:
    print('Failed')
  cursor = connection.cursor()
  cursor.execute('select ud.email_id \
                    from user_video_mappings uvm\
                        ,user_details ud \
                  where 1=1 \
                    and uvm.email_id = ud.email_id \
                    and uvm.video_id = ?;',[(video_id)])
  records = cursor.fetchall()
  return ([e[0] for e in records])


def get_owner_videos(email_id):

  connection = get_db_connection()
  if not connection:
    print('Failed')
  cursor = connection.cursor()

  cursor.execute("select vd.title, vd.url, vd.description, vd.uploaded_by, vd.created_date, vd.video_id from \
                  video_details vd \
                  where 1=1 \
                    and vd.uploaded_by = ? \
                  order by vd.created_date desc;",[(email_id)])
  records = cursor.fetchall()
  session['owner_video'] = records


def get_db_connection():

  connection = None
  try:
    connection = sqlite3.connect('broadcast.db')
  except:
    return None
  
  return connection


if __name__ == '__main__':
  webapp.debug = True
  webapp.run()