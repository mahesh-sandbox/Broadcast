import sqlite3

try:
  connection = sqlite3.connect('broadcast.db')
  cursor = connection.cursor()

  # sql = 'drop table video_details;'
  # cursor.execute(sql)

  # sql = 'drop table user_details;'
  # cursor.execute(sql)

  # sql = 'drop table user_video_mappings;'
  # cursor.execute(sql)

  createTable = '''
                create table video_details 
                ( video_id  INTEGER primary key AUTOINCREMENT,
                  url   varchar2(256),
                  title  varchar2(100),
                  description text,
                  uploaded_by varchar2(100),
                  created_date datetime);
                '''
  
  cursor.execute(createTable)

  createTable = '''
              create table user_details 
              ( user_id  INTEGER primary key AUTOINCREMENT,
                first_name  varchar2(256),
                last_name   varchar2(256),
                email_id varchar2(100) not null,
                phone_num   varchar2(20),
                admin_account varchar2(10));
              '''

  cursor.execute(createTable)

  createTable = '''
              create table user_video_mappings 
              ( mapping_id  INTEGER primary key AUTOINCREMENT,
                email_id   varchar2(100),
                video_id int,
                created_date datetime);
              '''

  cursor.execute(createTable)

  insert_sql = 'insert into user_details (first_name, last_name, email_id, phone_num, admin_account) \
                    values (?,?,?,?,?);'

  values = ['Admin', 'Account', 'admin@gmail.com', '123456789', 'Y'] 
  cursor.execute(insert_sql, values)
  connection.commit()

except sqlite3.Error as error:
  print(error)

