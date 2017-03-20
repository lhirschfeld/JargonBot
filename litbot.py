import re
from time import sleep
import pickle

import praw
from lookup import findItem

r = praw.Reddit('bot2')

m = re.compile(r"[Ii]nfo:.*")

def respond(lim, rate, subs):
    with open('ids.pickle', 'rb') as handle:
        ids = pickle.load(handle)
    while True:
        try:
            for sub in subs:
                subreddit = r.subreddit(sub)
                for submission in subreddit.hot(limit=lim):
                    comment_queue = submission.comments[:]
                    while comment_queue:
                        com = comment_queue.pop(0)
                        try:
                            com.body
                        except:
                            continue
                        if com.body and ("Info:" in com.body or "info:" in com.body) and com.id not in ids:
                            print("Found Comment:" + com.id)
                            reply = ""
                            for item in m.findall(com.body)[:10]:
                                for s in item[5:].split(","):
                                    try:
                                        temp = findItem(s)
                                    except:
                                        temp = ""
                                    reply += temp
                                    if temp != "":
                                        reply += "\n\n---------\n\n"
                                    sleep(1)
                            if reply != "":
                                reply += " ^All ^data ^from ^goodreads.com. ^I ^am ^a ^bot."
                                reply += " ^Reply ^to ^me ^with ^up ^to ^7 ^[[book ^names]]."
                                reply += " ^Please ^contact ^/u/liortulip"
                                reply += " ^with ^any ^questions ^or ^concerns."
                                try:
                                    com.reply(reply)
                                except praw.exceptions.APIException as error:
                                    print("Hit rate limit error.")
                                    sleep(600)
                                    com.reply(reply)
                                print("Replied")
                            else:
                                print("False Reply ^")
                            ids.append(com.id)
                        comment_queue.extend(com.replies)
            with open('ids.pickle', 'wb') as handle:
                pickle.dump(ids, handle, protocol=pickle.HIGHEST_PROTOCOL)
            sleep(rate)
        except:
            print("I encountered an error.")
            sleep(300)
            print("Restarting...")

respond(50,10, ["fantasy", "comicbooks"])
