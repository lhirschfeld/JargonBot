import re
from time import sleep
import pickle

import praw
from define import getDefinition
from collections import Counter

r = praw.Reddit('bot3')

def analyze(sub):
    subreddit = r.subreddit(sub)
    words = []
    for submission in subreddit.hot(500):
        comment_queue = submission.comments[:]
        while comment_queue:
            com = comment_queue.pop(0)
            try:
                com.body
            except:
                continue
            for word in com.body.split():
                # TODO: Stem and remove stopwords
                words.append(word)
    words = Counter(words)
    # TODO

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
                            # except AssertionError as e:
                            # TODO: MAKE except specific
                            continue
                        if com.body and ("Info:" in com.body or "info:" in com.body) and com.id not in ids:
                            print("Found Comment:" + com.id)
                            reply = ""
                            # Get the definition of the word (if it exists)
                            if True: # Do this if the word has a found definition
                                reply += "\n\n---------\n\n"
                            if reply != "":
                                reply += " ^All ^data ^from ^merriam-webster.com. ^I ^am ^a ^bot."
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

respond(50,10, ["test"])
