from flask import Flask, render_template
#import pymysql
#import credentials

app= Flask(__name__, template_folder='template')

#class Database:
 #   def __init__(self):
  #      host = credentials.DB_HOST
   #     user = credentials.DB_USER
    #    pwd = credentials.DB_PWD
     #   db = credentials.DB_NAME

#        self.con = pymysql.connect(
#            host=host,
#            user=user,
#            password=pwd,
#            database=db,
#            cursorclass=pymysql.cursors.DictCursor
 #       )

  #      self.cur = self.con.cursor()

@app.route("/")
def index():
#    db = Database()
    return render_template('index.html')

@app.route("/login")
def login():
#    db = Database()
    return render_template('login.html')

@app.route("/register")
def register():
#    db = Database()
    return render_template('register.html')

@app.route("/list")
def list():
#    db = Database()
    return render_template('list.html')

@app.route("/order")
def order():
#    db = Database()
    return render_template('order.html')

@app.route("/game/<int:GameID>") # Dynamically generate a homepage for each game using the gameID as page URL
def gamepage(GameID):
#    db = Database()
    return render_template('gamepage.html', GameID=GameID)

if __name__ == "__main__":
        app.run(host="0.0.0.0", port=5000, debug=True)