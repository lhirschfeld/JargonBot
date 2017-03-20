import requests
import xmltodict
from time import sleep

def findItem(name):
    print(name)
    def getSearchURL(n):
        words = n.split()
        url = "https://www.goodreads.com/search/index.xml?q="
        for word in words:
            url += word + "+"
        url = url[:-1]
        url += "&key=RXNaq83VFkZogIzLUb7ekA"
        return url
    def getReviewURL(id_):
        url = "https://www.goodreads.com/book/show.xml?id=" + id_
        url += "&key=" + "RXNaq83VFkZogIzLUb7ekA"
        return url

    #Ignore posts by the bot itself.
    if name == "Goodreads" or name == "item names" or name == "Author":
        return ""

    r = requests.get(getSearchURL(name))
    data = xmltodict.parse(r.text)

    stats = data.popitem()[1]["search"]["results"].popitem()[1][0]
    book = stats.popitem()[1]
    bookID = book["id"].popitem()[1]
    authorID = book["author"]["id"].popitem()[1]
    # Title line
    response = "[**" + book["title"] + "**]"
    response += "(" + book["image_url"] + ")"

    # Get additional info
    response += "\n\n"
    response += " ^Written ^by ^*" + "* ^*".join(book["author"]["name"].split()) + "*"
    response += " ^| ^Published ^in ^" + stats["original_publication_year"].popitem()[1]
    response += " ^[[Book]]"
    response += "(http://www.goodreads.com/book/show/" + bookID + ")"
    response += " ^[[Author]]"
    response += "(http://www.goodreads.com/author/show/" + authorID + ")"

    sleep(1)

    r = requests.get(getReviewURL(bookID))
    data = xmltodict.parse(r.text)
    description = data.popitem()[1]["book"]["description"]
    #HTML to reddit formatting
    description = description.replace("<br /><br />", '"\n\n>')
    description = description.replace("<br />", "")
    description = description.replace("<i>", "").replace("</i>", "")
    description = description.replace("<b>", "").replace("</b>", "")

    if "Librarian's note" in description:
        description = description[:description.index("Librarian's note")]

    response += "\n\n" + '>' + description
    return response
