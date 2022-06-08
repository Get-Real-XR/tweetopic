import os
from datetime import datetime as dt
from pathlib import Path
import re

import tweet_import

from bertopic import BERTopic

from tweet_import import to_docs

topic_model = None
def train():
	global topic_model
	stamp = str(dt.now())
	date, time = stamp.partition(" ")[::2]

	input_dir = Path("data/source")
	run_dir = Path(f"data/runs/{date}/")

	output_file = run_dir/f"{stamp}.csv"
	model_path = run_dir/f"{stamp}.model"


	if os.path.exists("data/processed/tweets.csv"):
		tweets = tweet_import.load_list(input_dir="data/processed", limit=None)
	else:
		no_link = lambda t: "http" not in t["text"]
		tweets = tweet_import.load_list(input_dir, output_file=Path("data/processed/tweets.csv"), filter_by=no_link, limit=None)
		print(len(tweets))

	print("Loaded")
	docs = to_docs(tweets)

	topic_model = BERTopic(verbose=True, calculate_probabilities=True)
	topic_model.fit(docs)
	os.makedirs(model_path.parent)

	tweet_import.write_tweets(tweets, output_file)
	topic_model.save(model_path)