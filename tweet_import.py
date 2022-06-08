import collections
import datetime
import itertools

import os
from typing import Callable, Any
from datetime import datetime
from tqdm import tqdm
from csv import DictReader, DictWriter, reader
from pathlib import Path
import re
import subprocess
from collections.abc import Sized, Iterable, Iterator

from typing import TypedDict

OUTPUT_ENCODING = 'utf8'

SOURCE_DIR = Path("source")


def get_encoding(path) -> str:
    """Attempts to predict the encoding of filename."""
    out = subprocess.Popen(['file', '-I', path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = out.communicate()[0]
    enc = out.lstrip().split()[2].decode().partition('=')[2]
    print(f'''Detected encoding: {enc}.''')
    return enc


def nested_csvs(path):
    """Returns a list of csv files as pathlike objects."""
    return Path(path).glob('**/*.csv')


def import_from_file(*paths):
    """Generates tweets from path(s) to csvs as positional arguments."""
    for path in paths:
        with open(path, encoding=get_encoding(path)) as csvfile:
            for tweet in DictReader(csvfile):
                yield tweet


def import_from_dir(*dirs):
    """Generate all tweets from directory/ies w/ paths as positional arguments."""
    for dir in dirs:
        for path in nested_csvs(dir):
            yield from import_from_file(path)


def dedup_tweets(tweets):
    """Generates deduplicated tweets from tweets iterator."""
    ids = set()
    for tweet in tweets:
        id = tweet["user_id"]
        if id in ids:
            continue
        else:
            yield tweet
            ids.add(id)


def clean_text(text):
    """Returns cleaned text from a text input."""
    text = re.sub('http\\S*\\b', '', text)
    text = re.sub('@\\S*\\b', '', text)
    text = re.sub("[^\\w.,'?/\\[\\]()]", ' ', text)
    text = re.sub("(?<=\\B)[.,'?]", '', text)
    text = re.sub('[\\s\\n]+', ' ', text)
    text = text.strip()
    return text

def clean_tweet(tweet):
    """Cleans the text of the in-place tweet."""
    return tweet | {"clean": clean_text(tweet["text"])}


def make_encodable_text(text):
    """Makes text encodable to output via brute force."""
    return text.encode(OUTPUT_ENCODING, 'ignore').decode(OUTPUT_ENCODING)


def make_encodable_values_tweet(tweet):
    """Brute forces tweet values compatability with OUTPUT_ENCODING."""
    return {k: make_encodable_text(v) for k, v in tweet.items()}


def validate_tweet(tweet):
    """
    Ensure all fields are populated.
    """
    return all(tweet.values())


def process_tweet(tweet):
    tweet = clean_tweet(tweet)
    tweet = make_encodable_values_tweet(tweet)
    valid = validate_tweet(tweet)
    return tweet, valid


def process_tweets(tweets):
    for tweet in tweets:
        try:
            tweet, valid = process_tweet(tweet)
            if valid:
                yield tweet
            else:
                continue
        except TypeError:
            continue


def write_tweets(tweets, path):
    """
    WARNING:
    DO NOT NEST import_tweets_from_file INSIDE write_tweets
    (unless you want the imported file to be immediately overwritten, I guess?);
    solution: write_tweets(list(import_tweets_from_file(_)), _).
    """
    fieldnames = ["user_name", "clean", "tweet_id", "text", "user_id", "created_at", "subscription_id", "subscription_name"]
    os.makedirs(path.parent, exist_ok=True)
    with open(path, "w+") as f:
        writer = DictWriter(f, fieldnames)
        writer.writeheader()
        for tweet in tweets:
            writer.writerow(tweet)
            yield tweet


def load(input_dir, output_file=None, filter_by=None, limit=None):
    tweets = import_from_dir(input_dir)
    tweets = dedup_tweets(tweets)
    tweets = process_tweets(tweets)
    if filter_by:
        tweets = filter(filter_by, tweets)
    if output_file:
        tweets = write_tweets(tweets, output_file)
    tweets = itertools.islice(tweets, limit)
    yield from tweets


def load_list(input_dir, output_file=None, filter_by=None, limit=None):
    """
    Returns a list of tweets obtained by load.
    Useful when you want eager execution and to keep the results.
    See load for more details.
    """
    return list(load(input_dir, output_file, filter_by, limit))


def load_deque(input_dir, output_file, filter_by=None, limit=None):
    """
    Exhausts tweets generator obtained by load. Returns None.
    Useful when you want eager execution to save results to a file, but don't need said results in python.
    See load for more details.
    """
    collections.deque(load(input_dir, filter_by, limit), maxlen=0)




if __name__ == '__main__':
    list(tqdm(load()))
    print('Done!')