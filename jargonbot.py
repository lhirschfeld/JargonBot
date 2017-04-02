# Lior Hirschfeld
# JargonBot

# -- Imports --
import re
import pickle
import praw
import random

from time import sleep
from define import getDefinition
from collections import Counter
from nltk.stem import *

# -- Methods --
def jargon(lim, rate, subs, machineLearning=False):
    # -- Setup Variables --
    r = praw.Reddit('bot3')
    stemmer = PorterStemmer()
    ml = machineLearning

    with open('ids.pickle', 'rb') as handle:
        ids = pickle.load(handle)
    with open('languages.pickle', 'rb') as handle:
        languages = pickle.load(handle)
    with open('count.txt', 'r') as handle:
        count = [line.split()[0] for line in handle.readlines()]
        countStemmed = [stemmer.stem(word) for word in count]

    if ml:
        responses = []
        # Model Takes: [Word Popularity, Word Length, Comment Length]
        with open('model.pickle', 'rb') as handle:
            model = pickle.load(handle)

    searchReddit(lim, rate, subs, ml)

# Search Reddit for words that need to be defined, and define them.
def searchReddit(lim, rate, subs, ml):
    while True:
        for sub in subs:
            searchSub(sub, lim, ml)
        with open('ids.pickle', 'wb') as handle:
            pickle.dump(ids, handle, protocol=pickle.HIGHEST_PROTOCOL)
        sleep(rate)

# Search a sub for words that need to be defined, and define them.
def searchSub(sub, lim, ml):
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
                    for item in countStemmed:
                        if item == word:
                            word = item
                            break
                    if ml:
                        # If ML, after basic checks, predict using the model
                        # to decide whether to reply.
                        popularity = count.find(word)
                        if popularity = -1:
                            popularity = 1000000
                        info = [popularity, len(word), len(com.body)]

                        if popularity > 10000:
                            # Sometimes, randomly reply to train the model.
                            if random.random() < .0001:
                                reply(com, word, info)
                            model.predict(info) > 0:
                            reply(com, word, info, ml)
                        break
                    else:
                        if word not in count[:80000]:
                            reply(com, word)
                            break
            ids.append(com.id)
            comment_queue.extend(com.replies)

# Reply to a comment with a word definition.
def reply(com, word, info=None, ml):
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

            if ml:
                responses[com.id] = info
        except praw.exceptions.APIException as error:
            print("Hit rate limit error.")
            with open('ids.pickle', 'wb') as handle:
                pickle.dump(ids, handle, protocol=pickle.HIGHEST_PROTOCOL)
            sleep(600)
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

jargon(50, 10, ["test"])
