from flask import Flask, render_template, request
import pymysql
import credentials

app= Flask(__name__, template_folder='template')

class Database:
    def __init__(self):
       host = credentials.DB_HOST
       user = credentials.DB_USER
       pwd = credentials.DB_PWD
       db = credentials.DB_NAME

       self.con = pymysql.connect(
           host=host,
           user=user,
           password=pwd,
           database=db,
           cursorclass=pymysql.cursors.DictCursor
       )

       self.cur = self.con.cursor()

    def getTags(self):
        try:
           self.cur.execute("Select * from Tag")
           result = self.cur.fetchall()
        except:
            result = "Failed to fetch tags"
        
        return result

    def close(self):
        self.con.close()

    def getGamesList(self, sort, time, tagSelect, offset):
        query = "SELECT g.GameID, g.Name, g.Rating, g.Price, GROUP_CONCAT(t.Name ORDER BY t.Name SEPARATOR ', ') AS Tags FROM Game as g LEFT JOIN Gametag as gt on g.GameID=gt.GameID LEFT JOIN Tag as t on gt.TagID=t.TagID WHERE 1=1"
        params = []

        if time == "Today":
            query += " AND ReleaseDate >= CURDATE()"
        elif time == "ThisWeek":
            query += " AND ReleaseDate >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
        elif time == "ThisMonth":
            query += " AND ReleaseDate >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)"
        elif time == "ThisYear":
            query += " AND ReleaseDate >= DATE_SUB(CURDATE(), INTERVAL 365 DAY)"

        query += " GROUP BY g.GameID"

        if sort == "Alphabetical":
            query += " ORDER BY Name ASC"
        elif sort == "TopRated":
            query += " ORDER BY Rating DESC"
        elif sort == "MostRecent":
            query += " ORDER BY ReleaseDate DESC"

        if tagSelect:
            placeholders = ",".join(["%s"] * len(tagSelect))
            query += f" AND Tag IN ({placeholders})"
            params.extend(tagSelect)

        query += " LIMIT 50"

        query += f" OFFSET {offset}"

        self.cur.execute(query, params)
        return self.cur.fetchall()
    
    def getGameAttributes(self, GameID):
        query = f"SELECT g.GameID, g.Name, g.Description, g.Rating, g.Price, g.ReleaseDate, d.Name AS DeveloperName, p.Name AS PublisherName, GROUP_CONCAT(DISTINCT t.Name ORDER BY t.Name SEPARATOR ', ') AS Tags, GROUP_CONCAT(DISTINCT CONCAT(DLC.DLCID, ':', DLC.Name, ' ($', DLC.Price, ')') SEPARATOR ' | ') AS DLCs FROM Game as g LEFT JOIN Developer as d on g.DeveloperID=d.DeveloperID LEFT JOIN Publisher as p on g.PublisherID=p.PublisherID LEFT JOIN Gametag as gt on g.GameID=gt.GameID LEFT Join Tag as t on gt.TagID=t.TagID LEFT JOIN DLC on g.GameID=DLC.GameID WHERE GameID={GameID} GROUP BY g.GameID"
        try:
            self.cur.execute(query)
            result = self.cur.fetchone()
        except:
            result = "failed to fetch game data"
        
        return result

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

@app.route("/list", methods=['GET', 'POST'])
def list():
    db = Database()

    # get tags for filter options
    tags = db.getTags()

    # initialize variables for retrieving filter options
    selectedSort = None
    selectedTime = None
    selectedTags = []

    # execute upon filter selection
    if request.method == "POST":
        selectedSort = request.form.get("sort")
        selectedTime = request.form.get("time")
        selectedTags = request.form.getlist("tagSelect")

        # get the page number and set the offset accordingly
        page = int(request.args.get("page", 1))
        if page < 1:
            page = 1

        offset = (page - 1) * 50

        # Run SQL query using the form data
        gamesList = db.getGamesList(selectedSort, selectedTime, selectedTags, offset)
    else:
        # Default table on first load
        # get the page number and set the offset accordingly
        page = int(request.args.get("page", 1))
        if page < 1:
            page = 1

        offset = (page - 1) * 50

        
        gamesList = db.getGamesList("TopRated", None, [], offset)

    # Convert flat list → 5x10 matrix
    grid = []
    row = []

    for i, item in enumerate(gamesList):
        row.append(item)
        if (i + 1) % 5 == 0:
            grid.append(row)
            row = []

    # If fewer than 50 results, pad the last row
    if row:
        while len(row) < 5:
            row.append(None)
        grid.append(row)
        
    lastPage = len(gamesList) < 50

    db.close()
    return render_template('list.html', tags=tags, grid=grid, page=page, lastPage=lastPage)

@app.route("/order")
def order():
#    db = Database()
    return render_template('order.html')

@app.route("/game/<int:GameID>") # Dynamically generate a homepage for each game using the gameID as page URL
def gamepage(GameID):
    db = Database()
    gameData = db.getGameAttributes(GameID)
    db.close()
    return render_template('gamepage.html', gameData=gameData)

# BELOW THIS POINT IS SIMPLY PAGES TO ADD DATA TO THE DATABASE AND WILL NOT BE NECESSARY FOR THE FINAL PRODUCT
@app.route("/admin")
def adminPanel():
    self.cur.execute("SELECT * FROM Developer")
    developers = self.cur.fetchall()

    self.cur.execute("SELECT * FROM Publisher")
    publishers = self.cur.fetchall()

    self.cur.execute("SELECT * FROM Game")
    games = self.cur.fetchall()

    self.cur.execute("SELECT * FROM Tag")
    tags = self.cur.fetchall()

    return render_template(
        "admin_add.html",
        developers=developers,
        publishers=publishers,
        games=games,
        tags=tags
    )

@app.route("/add/developer", methods=["POST"])
def addDeveloper():
    name = request.form["Name"]
    self.cur.execute(f"INSERT INTO Developer (Name) VALUES {name}")
    self.conn.commit()
    return redirect("/admin")

@app.route("/add/publisher", methods=["POST"])
def addPublisher():
    name = request.form["Name"]
    self.cur.execute(f"INSERT INTO Publisher (Name) VALUES {name}")
    self.conn.commit()
    return redirect("/admin")

@app.route("/add/tag", methods=["POST"])
def addTag():
    name = request.form["Name"]
    self.cur.execute(f"INSERT INTO Tag (Name) VALUES {name}")
    self.conn.commit()
    return redirect("/admin")

@app.route("/add/game", methods=["POST"])
def addGame():
    name = request.form["Name"]
    Description = request.form["Description"]
    DeveloperID = request.form["DeveloperID"]
    PublisherID = request.form["PublisherID"]
    Rating = request.form["Rating"]
    Price = request.form["Price"]
    ReleaseDate = request.form["ReleaseDate"]
    self.cur.execute(f"INSERT INTO Developer (Name, Description, DeveloperID, PublisherID, Rating, Price, ReleaseDate) VALUES {name}, {Description}, {DeveloperID}, {PublisherID}, {Rating}, {Price}, {ReleaseDate}")
    self.conn.commit()
    return redirect("/admin")

@app.route("/add/dlc", methods=["POST"])
def addDLC():
    name = request.form["Name"]
    GameID = request.form["GameID"]
    Price = request.form["Price"]
    self.cur.execute(f"INSERT INTO Developer (Name, GameID, Price) VALUES {name}, {GameID}, {Price}")
    self.conn.commit()
    return redirect("/admin")

@app.route("/add/gametag", methods=["POST"])
def addGametag():
    GameID = request.form["GameID"]
    TagID = request.form["TagID"]
    self.cur.execute(f"INSERT INTO Developer (Name, GameID, TagID) VALUES {name}, {GameID}, {TagID}")
    self.conn.commit()
    return redirect("/admin")

if __name__ == "__main__":
        app.run(host="0.0.0.0", port=5000, debug=True)