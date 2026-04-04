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
        query = "SELECT g.GameID, g.Name, g.Rating, g.Price, GROUP_CONCAT(t.Name ORDER BY t.Name SEPARATOR ', ') AS Tags FROM Game as g LEFT JOIN GameTag as gt on g.GameID=gt.GameID LEFT JOIN Tag as t on gt.TagID=t.TagID GROUP BY g.GameID WHERE 1=1"
        params = []

        if sort == "Alphabetical":
            query += " ORDER BY Name ASC"
        elif sort == "TopRated":
            query += " ORDER BY Rating DESC"
        elif sort == "MostRecent":
            query += " ORDER BY ReleaseDate DESC"

        if time == "Today":
            query += " AND ReleaseDate >= CURDATE()"
        elif time == "ThisWeek":
            query += " AND ReleaseDate >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
        elif time == "ThisMonth":
            query += " AND ReleaseDate >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)"
        elif time == "ThisYear":
            query += " AND ReleaseDate >= DATE_SUB(CURDATE(), INTERVAL 365 DAY)"

        if tagSelect:
            placeholders = ",".join(["%s"] * len(tagSelect))
            query += f" AND Tag IN ({placeholders})"
            params.extend(tagSelect)

        query += " LIMIT 50"

        query += f" OFFSET {offset}"

        self.cur.execute(query, params)
        return self.cur.fetchall()


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
        offset = (page - 1) * 50

        # Run SQL query using the form data
        gamesList = db.getGamesList(selectedSort, selectedTime, selectedTags, offset)
    else:
        # Default table on first load
        # get the page number and set the offset accordingly
        page = int(request.args.get("page", 1))
        offset = (page - 1) * 50

        
        gamesList = db.getGamesList("TopRated", None, [])

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
    return render_template('list.html', tags=tags, grid=grid, lastPage=lastPage)

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