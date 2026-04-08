from flask import Flask, render_template, request, redirect, session
import pymysql
import credentials 
import datetime


app= Flask(__name__, template_folder='template')

app.secret_key = "supersecretkey"

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
        query = "SELECT g.GameID, g.Name, g.Rating, g.Price, g.ReleaseDate, GROUP_CONCAT(t.Name ORDER BY t.Name SEPARATOR ', ') AS Tags FROM Game as g LEFT JOIN Gametag as gt on g.GameID=gt.GameID LEFT JOIN Tag as t on gt.TagID=t.TagID WHERE 1=1"
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
        query = f"SELECT g.GameID, g.Name, g.Description, g.Rating, g.Price, g.ReleaseDate, d.Name AS DeveloperName, p.Name AS PublisherName, GROUP_CONCAT(DISTINCT t.Name ORDER BY t.Name SEPARATOR ',') AS Tags, GROUP_CONCAT(DISTINCT CONCAT(DLC.DLCID, ':', DLC.Name, ':', DLC.Price) SEPARATOR ',') AS DLCs FROM Game as g LEFT JOIN Developer as d on g.DeveloperID=d.DeveloperID LEFT JOIN Publisher as p on g.PublisherID=p.PublisherID LEFT JOIN Gametag as gt on g.GameID=gt.GameID LEFT Join Tag as t on gt.TagID=t.TagID LEFT JOIN DLC on g.GameID=DLC.GameID WHERE g.GameID={GameID} GROUP BY g.GameID"
        try:
            self.cur.execute(query)
            result = self.cur.fetchone()
        except:
            result = "Failed to fetch game data"
        
        return result
    
    def selectDevelopers(self):
        self.cur.execute("SELECT * FROM Developer")
        developers = self.cur.fetchall()
        return developers
    
    def selectPublishers(self):
        self.cur.execute("SELECT * FROM Publisher")
        publishers = self.cur.fetchall()
        return publishers
    
    def selectGames(self):
        self.cur.execute("SELECT * FROM Game")
        games = self.cur.fetchall()
        return games
    
    def selectTags(self):
        self.cur.execute("SELECT * FROM Tag")
        tags = self.cur.fetchall()
        return tags

    def insertDeveloper(self, name):
        try:
            query = "INSERT INTO Developer (Name) VALUES (%s)"
            self.cur.execute(query, (name,))
            self.con.commit()
            result = "Success"
        except:
            result = "Failure"
        return result
    
    def insertPublisher(self, name):
        try:
            query = "INSERT INTO Publisher (Name) VALUES (%s)"
            self.cur.execute(query, (name,))
            self.con.commit()
            result = "Success"
        except:
            result = "Failure"
        return result

    def insertTag(self, name):
        try:
            query = "INSERT INTO Tag (Name) VALUES (%s)"
            self.cur.execute(query, (name,))
            self.con.commit()
            result = "Success"
        except:
            result = "Failure"
        return result
    
    def insertGame(self, name, Description, DeveloperID, PublisherID, Rating, Price, ReleaseDate):
        try:
            query = "INSERT INTO Game (Name, Description, DeveloperID, PublisherID, Rating, Price, ReleaseDate) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            self.cur.execute(query, (name, Description, DeveloperID, PublisherID, Rating, Price, ReleaseDate))
            self.con.commit()
            result = "Success"
        except:
            result = "Failure"
        return result
      
    def insertDLC(self, name, GameID, Price):
        try:
            query = "INSERT INTO DLC (Name, GameID, Price) VALUES (%s, %s, %s)"
            self.cur.execute(query, (name, GameID, Price))
            self.con.commit()
            result = "Success"
        except:
            result = "Failure"
        return result

    def insertGametag(self, GameID, TagID):
        try:
            query = "INSERT INTO Gametag (GameID, TagID) VALUES (%s, %s)"
            self.cur.execute(query, (GameID, TagID))
            self.con.commit()
            result = "Success"
        except:
            result = "Failure"
        return result

    def createPurchase(self, UserID):
        try:
            query = "INSERT INTO Purchase (UserID, Date) Values (%s, NOW())"
            self.cur.execute(query, (UserID,))
            self.con.commit()
            self.cur.execute("SELECT LAST_INSERT_ID()")
            purchaseID = self.cur.fetchone()[0]

            return purchaseID
        except Exception as e:
            print(e)
            return None

    
    def addPurchaseItem(self, PurchaseID, ID, Price, itemType):
        try:
            if itemType == "Game":
                query = "INSERT INTO PurchaseItem (PurchaseID, GameID, Price) Values (%s, %s, %s)"
                self.cur.execute(query, (PurchaseID, ID, Price))
                self.con.commit()
            elif itemType == "DLC":
                query = "INSERT INTO PurchaseItem (PurchaseID, DLCID, Price) Values (%s, %s, %s)"
                self.cur.execute(query, (PurchaseID, ID, Price))
                self.con.commit()
            else:
                return "Failure"
            result = "Success"
        except:
            result = "Failure"
        return result

@app.route("/")
def index():
    db = Database()
    return render_template('index.html')

@app.route("/register", methods=["GET","POST"])
def register():
    db = Database()

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]

        query = "INSERT INTO User (Username, Password, Email) VALUES (%s, %s, %s)"
        db.cur.execute(query, (username, password, email))
        db.con.commit()

        db.close()

        return redirect("/login")

    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():

    db = Database()

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        query = "SELECT * FROM User WHERE Username=%s AND Password=%s"
        db.cur.execute(query, (username, password))

        user = db.cur.fetchone()

        db.close()

        if user:
            session["username"] = user["Username"]
            session["UserID"] = user["UserID"]
            return redirect("/")
        else:
            return "Invalid login"

    return render_template("login.html")

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

@app.route("/order", methods=['GET', 'POST'])
def order():
    db = Database()
    cart = session.get("cart", [])
    cartItems = []
    totalCost = 0.0

    for item in cart:
        if item["type"] == "Game":
            query = "SELECT * FROM Game WHERE GameID=%s"
        elif item["type"] == "DLC":
            query = "SELECT * FROM DLC WHERE DLCID=%s"
        else:
            continue
        
        db.cur.execute(query, (item["ID"],))
        result = db.cur.fetchone()
        if result:
            totalCost += float(result["Price"])
            cartItems.append(result)

    if request.method == "POST":
        purchaseID = db.createPurchase(session["UserID"])
        if purchaseID:
            for item in cartItems:
                if "DLCID" in item:
                    db.addPurchaseItem(purchaseID, item["DLCID"], item["Price"], "DLC")
                else:
                    db.addPurchaseItem(purchaseID, item["GameID"], item["Price"], "Game")
    db.close()
    return render_template('order.html', cartItems=cartItems, totalCost=totalCost)

@app.route("/game/<int:GameID>") # Dynamically generate a homepage for each game using the gameID as page URL
def gamepage(GameID):
    db = Database()
    gameData = db.getGameAttributes(GameID)
    if gameData["Tags"]:
        Tags = gameData["Tags"].split(',')
    else:
        Tags = ""
    if gameData["DLCs"]:
        DLCArray = gameData["DLCs"].split(',')
        DLC = []
        for item in DLCArray:
            DLCID, Name, Price = item.split(":")
            DLC.append({"DLCID": DLCID, "Name": Name, "Price": Price})
    else:
        DLC = ""
    db.close()
    return render_template('gamepage.html', gameData=gameData, Tags=Tags, DLC=DLC)

@app.route("/cart/<int:GameID>/game")
def cartGame(GameID):
    cart = session.get("cart", [])
    item = {"type": "Game", "ID": GameID}
    cart.append(item)
    session["cart"] = cart
    return redirect("/list")

@app.route("/cart/<int:DLCID>/dlc")
def cartDLC(DLCID):
    cart = session.get("cart", [])
    item = {"type": "DLC", "ID": DLCID}
    cart.append(item)
    session["cart"] = cart
    return redirect("/list")

@app.route("/rmcart/<int:ID>/game")
def rmcartGame(ID):
    cart = session.get("cart", [])
    for item in cart:
        if item["ID"] == ID and item["type"] == "Game":
            cart.remove(item)
            break
    session["cart"] = cart
    return redirect("/order")

@app.route("/rmcart/<int:ID>/dlc")
def rmcartDLC(ID):
    cart = session.get("cart", [])
    for item in cart:
        if item["ID"] == ID and item["type"] == "DLC":
            cart.remove(item)
            break
    session["cart"] = cart
    return redirect("/order")

# BELOW THIS POINT IS SIMPLY PAGES TO ADD DATA TO THE DATABASE AND WILL NOT BE NECESSARY FOR THE FINAL PRODUCT
@app.route("/admin")
def adminPanel():
    db = Database()
    developers = db.selectDevelopers()
    publishers = db.selectPublishers()
    games = db.selectGames()
    tags = db.selectTags()
    db.close()
    return render_template(
        "admin.html",
        developers=developers,
        publishers=publishers,
        games=games,
        tags=tags
    )

#ALLOWS USER REVIEWS
@app.route("/add_review", methods=["POST"])
def add_review():

    if "username" not in session:
        return redirect("/login")

    db = Database()

    username = session["username"]
    gameID = request.form["gameID"]
    rating = request.form["rating"]
    reviewText = request.form["reviewText"]

    query = "SELECT UserID FROM user WHERE Username=%s"
    db.cur.execute(query, (username,))
    user = db.cur.fetchone()

    userID = user["UserID"]

    insert = """
    INSERT INTO review (UserID, GameID, StarRating, Message)
    VALUES (%s, %s, %s, %s)
    """

    db.cur.execute(insert, (userID, gameID, rating, reviewText))
    db.con.commit()

    db.close()

    return redirect(request.referrer)

@app.route("/add/developer", methods=["POST"])
def addDeveloper():
    db = Database()
    name = request.form["Name"]
    db.insertDeveloper(name)
    db.close()
    return redirect("/admin")

@app.route("/add/publisher", methods=["POST"])
def addPublisher():
    db = Database()
    name = request.form["Name"]
    db.insertPublisher(name)
    db.close()
    return redirect("/admin")

@app.route("/add/tag", methods=["POST"])
def addTag():
    db = Database()
    name = request.form["Name"]
    db.insertTag(name)
    db.close()
    return redirect("/admin")

@app.route("/add/game", methods=["POST"])
def addGame():
    db = Database()
    name = request.form["Name"]
    Description = request.form["Description"]
    DeveloperID = request.form["DeveloperID"]
    PublisherID = request.form["PublisherID"]
    Rating = request.form["Rating"]
    Price = request.form["Price"]
    ReleaseDate = request.form["ReleaseDate"]
    db.insertGame(name, Description, DeveloperID, PublisherID, Rating, Price, ReleaseDate)
    db.close()
    return redirect("/admin")

@app.route("/add/dlc", methods=["POST"])
def addDLC():
    db = Database()
    name = request.form["Name"]
    GameID = request.form["GameID"]
    Price = request.form["Price"]
    db.insertDLC(name, GameID, Price)
    db.close()
    return redirect("/admin")

@app.route("/add/gametag", methods=["POST"])
def addGametag():
    db = Database()
    GameID = request.form["GameID"]
    TagID = request.form["TagID"]
    db.insertGametag(GameID, TagID)
    db.close()
    return redirect("/admin")

if __name__ == "__main__":
        app.run(host="0.0.0.0", port=5000, debug=True)