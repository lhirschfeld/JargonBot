# Lior Hirschfeld
# JargonBot

# -- Imports --
import re
import pickle
import praw

from time import sleep
from define import getDefinition
from collections import Counter
from nltk.stem import *

# -- Setup Global Variables --
r = praw.Reddit('bot3')
stemmer = PorterStemmer()

with open('ids.pickle', 'rb') as handle:
    ids = pickle.load(handle)
with open('languages.pickle', 'rb') as handle:
    languages = pickle.load(handle)

# -- Methods --

# Search Reddit for words that need to be defined, and define them.
def searchReddit(lim, rate, subs):
    while True:
        for sub in subs:
            searchSub(sub, lim)
        with open('ids.pickle', 'wb') as handle:
            pickle.dump(ids, handle, protocol=pickle.HIGHEST_PROTOCOL)
        sleep(rate)

# Search a sub for words that need to be defined, and define them.
def searchSub(sub, lim):
    subreddit = r.subreddit(sub)
    subWords = [pair[0] for pair in languages[sub].most_common(5000)]
    for submission in subreddit.hot(limit=lim):
        comment_queue = submission.comments[:]
        while comment_queue:
            com = comment_queue.pop(0)
            if not hasattr(com, 'body') or com.id in ids:
                continue
            for word in com.body:
                # Stem the word and check if it is rare enough to be defined.
                word = stemmer.stem(word)
                if word not in subWords:
                    reply(com, word)
                    break
            ids.append(com.id)
            comment_queue.extend(com.replies)

# Reply to a comment with a word definition.
def reply(com, word):
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

# Analyze the language of a particular sub.
def analyze(sub):
    print("Analyzing:", sub)
    subreddit = r.subreddit(sub)
    words = Counter()
    for submission in subreddit.hot(2000):
        comment_queue = submission.comments[:]
        while comment_queue:
            com = comment_queue.pop(0)
            if hasattr(com, 'body'):
                for word in com.body.split():
                    # Stem the word and add it to the counter.
                    word = stemmer.stem(word)
                    words[word] += 1
    words = Counter(words)
    languages[sub] = words
    with open('languages.pickle', 'wb') as handle:
        pickle.dump(languages, handle, protocol=pickle.HIGHEST_PROTOCOL)
    print("Analyzation complete.")

searchReddit(50, 10, ["test"])
