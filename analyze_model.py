import itertools

import numpy
from bertopic import BERTopic, plotting
from pathlib import Path
import tweet_wrangling

import visualize

models = list(Path("data").glob("**/*.model"))
most_recent_model = max(models)
stamp = most_recent_model.stem
tweets_path = Path("data").glob(f"**/{stamp}.csv")

topic_model: BERTopic = BERTopic.load(str(most_recent_model))
tweets = tweet_wrangling.import_from_file(*tweets_path)

docs, topics, probabilities = tweet_wrangling.dict_zip(tweets, ["docs", "topics", "probabilities"]).values()

figures = [
    topic_model.visualize_topics(top_n_topics=30),
    topic_model.visualize_hierarchy(),
    topic_model.visualize_topics(),
    topic_model.visualize_term_rank(),
    topic_model.visualize_distribution(),
    topic_model.visualize_hierarchy(),
    topic_model.visualize_heatmap(),
    topic_model.visualize_barchart()]

topic_model.visualize_topics_over_time(),

topic_model.visualize_topics_per_class(),
# topic_model.visualize_distribution(probabilities)]



visualize.visualize_modeL(topic_model)
# topic_model.reduce_topics(*data.values(), nr_topics=30)

