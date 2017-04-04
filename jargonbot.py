# Lior Hirschfeld
# JargonBot

# -- Imports --
import re
import pickle
import praw
import random

from datetime import datetime
from time import sleep
from define import getDefinition
from collections import Counter
from nltk.stem import *
from textblob import TextBlob
from sklearn import linear_model

# -- Setup Variables --
r = praw.Reddit('bot3')
stemmer = PorterStemmer()
responses = []

with open('ids.pickle', 'rb') as handle:
    ids = pickle.load(handle)
with open('languages.pickle', 'rb') as handle:
    languages = pickle.load(handle)
with open('count.txt', 'r') as handle:
    count = [line.split()[0] for line in handle.readlines()]
    countStemmed = [stemmer.stem(word) for word in count]

# Model Takes: [Word Popularity, Word Length, Comment Length]
# Models is a dictionary with a touple at each key containing:
# (linear regression, randomness rate)
with open('models.pickle', 'rb') as handle:
    try:
        models = pickle.load(handle)
    except EOFError:
        models = {}

# -- Methods --
def jargon(lim, rate, subs, ml=False):
    searchReddit(lim, rate, subs, ml)

# Search Reddit for words that need to be defined, and define them.
def searchReddit(lim, rate, subs, ml):
    while True:
        for sub in subs:
            searchSub(sub, lim, ml)
        with open('ids.pickle', 'wb') as handle:
            pickle.dump(ids, handle, protocol=pickle.HIGHEST_PROTOCOL)

        if ml:
            updateModels()
        sleep(rate)

# Update the machine learning model and save it.
def updateModels():
    global responses, models
    currentTime = datetime.now()
    oldResponses = [(currentTime - r["time"]).total_seconds() > 3600
                             for r in responses]
    responses = [(currentTime - r["time"]).total_seconds() < 3600
                             for r in responses]
    for r in oldResponses:
        result = 0
        url = "https://reddit.com/" + r["sID"] + "?comment=" + r["cID"]
        submission = reddit.get_submission(url=url)
        comment_queue = submission.comments[:]
        if comment_queue:
            com = comment_queue.pop(0)
            result += com.score
            comment_queue.extend(com.replies)
        while comment_queue:
            com = comment_queue.pop(0)
            text = TextBlob(com.text)
            result += text.sentiment.polarity * com.score
        models[r["sub"]][0].fit([[r["popularity"], r["wLength"], r["cLength"]]],
                              [result])

        # Update odds of random choice
        models[r]["sub"][1] *= 0.96
    with open('models.pickle', 'wb') as handle:
        pickle.dump(models, handle, protocol=pickle.HIGHEST_PROTOCOL)

# Search a sub for words that need to be defined, and define them.
def searchSub(sub, lim, ml):
    global models
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
                        if sub not in models:
                            models[sub] = (linear_model.LinearRegression(), 1)
                            models[sub][0].fit([[1000000, 10, 10]], [10])
                        # If ML, after basic checks, predict using the model
                        # to decide whether to reply.
                        if word in count:
                            popularity = count.index(word)
                        else:
                            popularity = 1000000

                        info = {"popularity": popularity, "wLength": len(word),
                                "cLength": len(com.body), "cID": com.id,
                                "sID": submission.id, "sub": sub}

                        if popularity > 10000:
                            # Sometimes, randomly reply to train the model.
                            if random.random() < models[sub][1]:
                                reply(com, word, ml, info=info)
                            elif models[sub][0].predict([[info["popularity"],
                                    info["wLength"], info["cLength"]]]) > 0:
                                reply(com, word, ml, info=info)
                        break
                    else:
                        if word not in count[:80000]:
                            reply(com, word, ml)
                            break
            ids.append(com.id)
            comment_queue.extend(com.replies)

# Reply to a comment with a word definition.
def reply(com, word, ml, info=None):
    global responses
    print("Found Comment:" + com.id)
    reply = ""
    # Get the definition of the word (if it exists)
    result = getDefinition(word)

    if result != None:
        # A definition has been found.
        reply += """Definition of {}: {}.\n\n
                    *{}.*""".format(word.upper(), result[0].capitalize(),
                                    result[1].capitalize())
        if ml:
            reply += """
                    \n\n---------\n\n
                    I am a bot which attempts to define difficult words
                    automatically. I use machine learning to do this, and I can
                    use your feedback to improve. Feel free to leave a comment
                    to let me know what you thought of this definition!
                    """
        reply += """\n\nAll data from http://www.oed.com/. Please contact
                    /u/liortulip with any questions or concerns."""

        try:
            cID = com.reply(reply)

            if ml:
                info["time"] = datetime.now()
                info["cID"] = cID
                responses.append(info)
            print("Replied")
        except praw.exceptions.APIException as error:
            print("Hit rate limit error.")
            with open('ids.pickle', 'wb') as handle:
                pickle.dump(ids, handle, protocol=pickle.HIGHEST_PROTOCOL)
            sleep(600)
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

jargon(50, 10, ["test"], ml=True)
