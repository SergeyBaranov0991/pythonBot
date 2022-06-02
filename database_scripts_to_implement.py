import sqlite3 as sl
con = sl.connect('database1.db')



sql = 'INSERT INTO REMINDERS (id, REMINDER_TEXT, REMINDER_WHEN) values(?, ?, ?)'
data = [
    (1, 'Напомнить про что нибудь раз', 30052022),
    (2, 'Напомнить про что нибудь два', 30052022),
    (3, 'Напомнить про что нибудь три', 30052022)
]

with con:
    con.executemany(sql, data)