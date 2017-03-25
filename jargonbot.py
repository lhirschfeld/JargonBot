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
with open('count.txt', 'r') as handle:
    count = [line.split()[0] for line in handle.readlines()]
    topWords = count[:80000]

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
    if sub not in languages:
        analyze(sub)

    subreddit = r.subreddit(sub)
    subWords = [pair[0] for pair in languages[sub].most_common(10000)]
    for submission in subreddit.hot(limit=lim):
        comment_queue = submission.comments[:]
        while comment_queue:
            com = comment_queue.pop(0)
            if not hasattr(com, 'body') or com.id in ids:
                continue
            for word in com.body.split():
                # Stem the word and check if it is rare enough to be defined.
                # Find the most similar word in count to the stemmed word.
                word = stemmer.stem(word)
                if word not in subWords:
                    for item in count:
                        if item.find(word) == 0:
                            word = item
                            break
                    if word not in topWords:
                        reply(com, word)
                        break
            ids.append(com.id)
            comment_queue.extend(com.replies)

# Reply to a comment with a word definition.
def reply(com, word):
    print("Found Comment:" + com.id + ", " + word)
    reply = ""
    # Get the definition of the word (if it exists)
    result = getDefinition(word)

    if result != None:
        # A definition has been found.
        reply += "Definition of " + word.upper() + ": " + result[0].capitalize() + ".\n\n"
        reply += "*" + result[1].capitalize() + ".*"
        reply += "\n\n---------\n\n"
        reply += " ^All ^data ^from ^http://www.oed.com/. ^I ^am ^a ^bot."
        reply += " ^Please ^contact ^/u/liortulip"
        reply += " ^with ^any ^questions ^or ^concerns."
        try:
            com.reply(reply)
        except praw.exceptions.APIException as error:
            print("Hit rate limit error.")
            ids.append(com.id)
            with open('ids.pickle', 'wb') as handle:
                pickle.dump(ids, handle, protocol=pickle.HIGHEST_PROTOCOL)
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
    for submission in subreddit.hot(limit=300):
        comment_queue = submission.comments[:]
        while comment_queue:
            com = comment_queue.pop(0)
            if hasattr(com, 'body'):
                for word in com.body.split():
                    # Stem the word and add it to the counter.
                    word = stemmer.stem(word)
                    words[word] += 1
    languages[sub] = words
    with open('languages.pickle', 'wb') as handle:
        pickle.dump(languages, handle, protocol=pickle.HIGHEST_PROTOCOL)
    print("Analyzation complete.")

searchReddit(50, 10, ["test"])
