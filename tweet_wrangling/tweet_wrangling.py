import collections
import itertools

import os
from tqdm import tqdm
from csv import DictReader, DictWriter
from pathlib import Path
import re
import subprocess

OUTPUT_ENCODING = 'utf8'

SOURCE_DIR = Path("source")

# todo determine if there is a ready-made solution
# def get_encoding(path) -> str:
#     """Attempts to predict the encoding of filename."""
#     out = subprocess.Popen(['file', '-I', path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
#     out = out.communicate()[0]
#     enc = out.lstrip().split()[2].decode().partition('=')[2]
#     print(f'Detected encoding for {path}: {enc}.')
#     return enc


def nested_csvs(path):
    """Returns a list of csv files as pathlike objects."""
    return Path(path).glob('**/*.csv')


def _import_from_file(*paths):
    """Generates tweets from path(s) to csvs as positional arguments."""
    for path in paths:
        with open(path) as csvfile:
            for tweet in DictReader(csvfile):
                yield tweet

def import_from_file(*paths):
    return list(_import_from_file(*paths))


def dedup_tweets(tweets):
    """Generates deduplicated tweets from tweets iterator."""
    ids = set()
    for tweet in tweets:
        id = tweet["user_id"]
        if id in ids:
            continue
        else:
            ids.add(id)
            yield tweet


def clean_text(text):
    """Returns cleaned text from a text input."""
    text = re.sub(r'http\S*\b', '', text)  # eliminate links
    text = re.sub(r'@\S*\b', '', text)  # eliminate usernames
    text = re.sub(r"[^\w.,'?/\[\]()]", ' ', text)  # replace unwanted characters with spaces
    text = re.sub(r"^\.", '', text)  # eliminate leading period
    text = re.sub(r'[\s\n]+', ' ', text)  # compress whitespace
    text = text.strip()
    return text

def _clean_tweet(tweet):
    """Cleans the text of the in-place tweet."""
    return tweet | {"docs": clean_text(tweet["text"])}


def _make_encodable_text(text):
    """Makes text encodable to output via brute force."""
    return text.encode(OUTPUT_ENCODING, 'ignore').decode(OUTPUT_ENCODING)


def _make_encodable_values_tweet(tweet):
    """Brute forces tweet values compatability with OUTPUT_ENCODING."""
    return {k: _make_encodable_text(v) for k, v in tweet.items()}


def process_tweet(tweet):
    if all(tweet.values()):
        tweet = _clean_tweet(tweet)
        tweet = _make_encodable_values_tweet(tweet)
        return tweet
    else:
        return None


def _process_tweets(tweets):
    for tweet in tweets:
        if tweet := process_tweet(tweet):
            yield tweet
        else:
            continue


def save_tweets(tweets, path, fieldnames):
    os.makedirs(path.parent, exist_ok=True)
    with open(path, "w+") as f:
        print(f"Saving to {path}...")
        writer = DictWriter(f, fieldnames)
        writer.writeheader()
        writer.writerows(tweets)
        print("Done saving.")


def _load_tweets(input_dir, limit=None, filter_by=None):
    tweets = _import_from_file(*nested_csvs(input_dir))
    tweets = _process_tweets(tweets)
    if filter_by:
        tweets = filter(filter_by, tweets)
    tweets = itertools.islice(tweets, limit)
    yield from tweets


def load_tweets(input_dir, limit=None, filter_by=None):
    """
    Returns a list of tweets obtained by load.
    Useful when you want eager execution and to keep the results.
    See load for more details.
    """
    tweets = _load_tweets(input_dir, limit, filter_by)
    tweets = tqdm(tweets)
    return list(tweets)


def train_tweets(limit=None):
    if not os.path.exists("data/processed/tweets.csv"):
        if not os.path.exists("data/processed/"):
            os.makedirs("data/processed/", exist_ok=True)
        print("Tweets not processed. Processing...")
        filter_by = lambda t: "http" not in t["text"]
        input_dir = Path("data/source/")
        output_file = Path("data/processed/tweets.csv")
        tweets = load_tweets(input_dir, limit=None, filter_by=filter_by)
        fieldnames = \
            ["subscription_id", "subscription_name", "user_id", "user_name", "tweet_id", "text", "created_at", "docs"]
        save_tweets(tweets, output_file, fieldnames)
        print("Processed.")

    print("Loading from processed...")
    input_dir = Path("data/processed/")
    return load_tweets(input_dir, limit)


def _dict_zip(dicts, keys=None):
    if not keys:
        # assume each of d has same keys
        keys = dicts[0].keys()
    tee = itertools.tee(dicts, len(keys))
    values = [map(dict.get, t, itertools.repeat(key)) for t, key in zip(tee, keys)]
    return dict(zip(keys, values))


def dict_zip(dicts, keys=None):
    if not keys:
        # assume each of d has same keys
        keys = dicts[0].keys()
    values = [list(map(dict.get, dicts, itertools.repeat(key))) for key in keys]
    return dict(zip(keys, values))



if __name__ == "__main__":
    train_tweets()