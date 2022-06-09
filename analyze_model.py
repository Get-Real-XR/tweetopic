import itertools

import numpy
from bertopic import BERTopic, plotting
from pathlib import Path
import tweet_wrangling

import visualize

models = list(Path("data").glob("**/*.reducedmodel"))
most_recent_model = max(models)
stamp = most_recent_model.stem
tweets_path = Path("data").glob(f"**/{stamp}.csv")

topic_model: BERTopic = BERTopic.load(str(most_recent_model))
tweets = tweet_wrangling.import_from_file(*tweets_path)


visualize.visualize_modeL(topic_model, tweets)
# topic_model.reduce_topics(*data.values(), nr_topics=30)

