from bertopic import BERTopic, plotting
from pathlib import Path
import tweet_import
import plotly

models = list(Path("data").glob("**/*.model"))

most_recent_model = max(models)

stamp = most_recent_model.stem

tweets = tweet_import.load_list(input_dir="data/processed", limit=None)
docs = tweet_import.to_docs(tweets)

topic_model: BERTopic = BERTopic.load(str(most_recent_model))

topics, probs = topic_model.transform(docs)


topic_model.reduce_topics(docs, topics, nr_topics=20)

fig = topic_model.visualize_topics()