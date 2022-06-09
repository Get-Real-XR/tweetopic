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


def nested_csvs(dir):
    """
    Finds all csv's in <dir> and its children.

    :param dir: directory in which to search
    :return: list of pathlike objects to csv files
    """
    return Path(dir).glob('**/*.csv')


def _import_from_file(*paths):
    """
    Generates tweets from <paths> as positional arguments to csv(s).

    :param paths: pathlike object(s) pointing to csv files
    :return: tweet (dict) generator
    """
    for path in paths:
        with open(path) as csvfile:
            yield from DictReader(csvfile)


def import_from_file(*paths):
    """
    Returns a list of tweets from <paths> as positional arguments to csv(s).

    :param paths: pathliek objects(s) pointing to csv files
    :return: list of tweets (dicts)
    """
    return list(_import_from_file(*paths))


def dedup_tweets(tweets):
    """
    Generates deduplicated (by tweet_id) tweets from tweets iterator.

    :param tweets: tweet (dict) iterator
    :return: tweet (dict) generator
    """
    ids = set()
    for tweet in tweets:
        id = tweet["user_id"]
        if id in ids:
            continue
        else:
            ids.add(id)
            yield tweet


def clean_text(text):
    """
    Returns cleaned string from <text> string. For use in "docs" tweet field.

    :param text: string to clean
    :return: cleaned string
    """
    text = re.sub(r'http\S*\b', '', text)  # eliminate links
    text = re.sub(r'@\S*\b', '', text)  # eliminate usernames
    text = re.sub(r"[^A-Za-z.,'?/\[\]()]", ' ', text)  # replace unwanted characters with spaces
    text = re.sub(r"^\.", '', text)  # eliminate leading period
    text = re.sub(r'[\s\n]+', ' ', text)  # compress whitespace
    text = text.strip()
    return text

def _clean_tweet(tweet):
    """
    Obtains the "docs" value from cleaned "text" value of <tweet>, then returns a new tweet updated with "docs" item.

    :param tweet: tweet (dict)
    :return: tweet w/ "docs" item (dict)
    """
    """Cleans the text of the tweet."""
    return tweet | {"docs": clean_text(tweet["text"])}


def _make_encodable_text(text):
    """
   Makes text encodable to output via brute force.

    :param text: str
    :return: OUTPUT_ENCODING compatible string
    """
    return text.encode(OUTPUT_ENCODING, 'ignore').decode(OUTPUT_ENCODING)


def _make_encodable_values_tweet(tweet):
    """
    Returns a new tweet with all values OUPUG_ENCODING compatiple.

    :param tweet: tweet (dict)
    :return: OUTPUT_ENCODING compatible tweet (dict)
    """
    """Brute forces tweet values compatability with OUTPUT_ENCODING."""
    return {k: _make_encodable_text(v) for k, v in tweet.items()}


def process_tweet(tweet):
    """
    Returns encodable tweet with the "docs" item or None if any of the values are empty.

    :param tweet:  tweet (dict)
    :return: encodable tweet with "docs" item
    """
    if all(tweet.values()):
        tweet = _clean_tweet(tweet)
        tweet = _make_encodable_values_tweet(tweet)
        return tweet
    else:
        return None


def _process_tweets(tweets):
    """
    Generates encodable tweets with "docs" item for every tweet (dict) without any empty values in <tweets> iterable.

    :param tweets: tweet (dict) iterator
    :return: tweet (dict) generator
    """
    for tweet in tweets:
        if tweet := process_tweet(tweet):
            yield tweet
        else:
            continue


def save_tweets(tweets, path, fieldnames):
    """
    Saves tweets from <tweets> iterable to csv <path>..

    :param tweets: tweet (dict) iterable
    :param path: pathlike object to csv file
    :param fieldnames: list of fields corresponding to the tweet fields to save as csv columns
    """
    os.makedirs(path.parent, exist_ok=True)
    with open(path, "w+") as f:
        print(f"Saving to {path}...")
        writer = DictWriter(f, fieldnames)
        writer.writeheader()
        writer.writerows(tweets)
        print("Done saving.")


def _load_tweets(input_dir, limit=None, filter_by=None):
    """
    Generates up to <limit> tweets passing <filter_by> from csv files in <input_dir> or its children.

    :param input_dir: input directory to recursively search for csv files
    :param limit: max number of tweets to generate
    :param filter_by: filter predicate function[tweet -> bool]
    :return: processed tweet (dict) generator
    """
    tweets = _import_from_file(*nested_csvs(input_dir))
    tweets = _process_tweets(tweets)
    if filter_by:
        tweets = filter(filter_by, tweets)
    tweets = itertools.islice(tweets, limit)
    yield from tweets


def load_tweets(input_dir, limit=None, filter_by=None):
    """
    Returns a list of up to <limit> tweets passing <filter_by> from csv files in <input_dir> or its children.
    :param input_dir: input directory to recursively search for csv files
    :param limit: max number of tweets to generate
    :param filter_by: filter predicate function[tweet -> bool]
    :return: processed tweet (dict) list
    """
    """
    Returns a list of tweets obtained by load.
    Useful when you want eager execution and to keep the results.
    See load for more details.
    """
    tweets = _load_tweets(input_dir, limit, filter_by)
    tweets = tqdm(tweets)
    return list(tweets)


def train_tweets(limit=None):
    """
    Generates of up to <limit> processed tweets (dicts) from csv files "data/source".
    :param limit: max number of tweets to generate
    :return: processed tweet (dict) generator
    """
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


def _dict_zip(dicts, keys):
    """
    Like zip but for dictionaries! _dict_zip is generator-based. For list based: see dict_zip.

    :param dicts: iterable of dicts
    :param keys: list of keys corresponding to the keys to retain from the dicts in <dicts>
    :return: a dictionary with <keys>, with generators yielding key-corresponding values from each dict in <dicts>
    """
    tee = itertools.tee(dicts, len(keys))
    values = [map(dict.get, t, itertools.repeat(key)) for t, key in zip(tee, keys)]
    return dict(zip(keys, values))


def dict_zip(dicts, keys=None):
    """
    Like zip but for dictionaries! dict_zip is list-based. For generator based: _see dict_zip.

	:param dicts: list of dicts
	:param keys: list of keys corresponding to the keys to retain from the dicts in <dicts>
	:return: a dictionary with <keys>, each valued with a list of each key-corresponding values for dict in <dicts>
	"""
    if not keys:
        # assume each of d has same keys
        keys = dicts[0].keys()
    values = [list(map(dict.get, dicts, itertools.repeat(key))) for key in keys]
    return dict(zip(keys, values))



if __name__ == "__main__":
    train_tweets()