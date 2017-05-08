# Lior Hirschfeld
# JargonBot

# -- Imports --
import re
import pickle
import random
import praw

from custombot import RedditBot
from time import sleep
from define import getDefinition
from collections import Counter
from nltk.stem import *
from sklearn import linear_model

# -- Setup Variables --
jargonBot = RedditBot('jargonBot')
stemmer = PorterStemmer()

with open('count.txt', 'r') as handle:
    count = [line.split()[0] for line in handle.readlines()]
    countStemmed = [stemmer.stem(word) for word in count]
with open('languages.pickle', 'rb') as handle:
    languages = pickle.load(handle)
# -- Methods --
def jargon(lim, rate, subs, ml=False):
    searchReddit(lim, rate, subs, ml)

# Search Reddit for words that need to be defined, and define them.
def searchReddit(lim, rate, subs, ml):
        for sub in subs:
            searchSub(sub, lim, ml)
        jargonBot.updateIds()
        if ml:
            jargonBot.updateModels(["popularity", "wLength", "cLength"])
        sleep(rate)

# Search a sub for words that need to be defined, and define them.
def searchSub(sub, lim, ml):
    if sub not in languages:
        analyze(sub)

    subreddit = jargonBot.r.subreddit(sub)
    subWords = [pair[0] for pair in languages[sub].most_common(10000)]
    for submission in subreddit.hot(limit=lim):
        comment_queue = submission.comments[:]
        while comment_queue:
            com = comment_queue.pop(0)
            if not hasattr(com, 'body') or com.id in jargonBot.ids:
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
                        if sub not in jargonBot.models:
                            jargonBot.createModel(sub, ([[1000000, 10, 10]], [10]))

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
                            if random.random() < jargonBot.models[sub][1]:
                                reply(com, word, ml, info=info)
                            elif jargonBot.models[sub][0].predict([[info["popularity"],
                                    info["wLength"], info["cLength"]]]) > 0:
                                reply(com, word, ml, info=info)
                        break
                    else:
                        if word not in count[:80000]:
                            reply(com, word, ml)
                            break
            jargonBot.ids.append(com.id)
            comment_queue.extend(com.replies)

# Reply to a comment with a word definition.
def reply(com, word, ml, info=None):
    reply = ""
    # Get the definition of the word (if it exists)
    result = getDefinition(word)

    if result != None:
        # A definition has been found.
        reply += """Definition of **{}**: {}.\n\n>*{}.*""".format(word.lower(), result[0].capitalize(),
                                    result[1].capitalize())
        if ml:
            reply += """\n\nI am a bot which attempts to define difficult words automatically. I use machine learning to do this, and I can use your feedback to improve. Feel free to leave a comment to let me know what you thought of this definition!"""
        reply += "\n\n---------\n\n^Check ^out ^my ^[code](https://github.com/lhirschfeld/JargonBot). "
        reply += " ^Please ^contact ^/u/liortulip ^with"
        reply += " ^any ^questions ^or ^concerns."

        try:
            cID = com.reply(reply)

            if ml:
                info["time"] = datetime.now()
                info["cID"] = cID
                jargonBot.responses.append(info)
            print("Replied")
        except praw.exceptions.APIException as error:
            print("Hit rate limit error.")
            jargonBot.updateIds()
            sleep(600)

# Analyze the language of a particular sub.
def analyze(sub):
    print("Analyzing:", sub)
    subreddit = jargonBot.r.subreddit(sub)
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

while True:
    for i in range(10):
        jargon(50, 10, ["science", "math", "askreddit"])
    for i in range(10):
        jargon(50, 10, ["science", "math", "askreddit"], ml=True)
