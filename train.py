import os
from datetime import datetime as dt
from pathlib import Path

import tweet_wrangling

from bertopic import BERTopic


def train():
	stamp = str(dt.now()).partition(".")[0]
	date, time = stamp.partition(" ")[::2]
	run_dir = Path(f"data/runs/{date}/{time}")
	print(f"Training {run_dir}.")

	csv_path = run_dir / f"{stamp}.csv"
	model_path = run_dir / f"{stamp}.model"
	reducedmodel_path = run_dir / f"{stamp}.reducedmodel"
	os.makedirs(run_dir, exist_ok=True)

	print("Gathering tweets...")
	tweets = tweet_wrangling.train_tweets()
	docs = [t["docs"] for t in tweets]

	print(f"Training topic model on {len(docs)} docs...")
	topic_model: BERTopic = BERTopic(verbose=True, calculate_probabilities=True)
	topics, probs = topic_model.fit_transform(docs)
	print(f"Saving {model_path}.")
	topic_model.save(str(model_path))

	print("Reducing topic dimensionality.")
	reduced_topics, reduced_probs = topic_model.reduce_topics(docs, topics, probs, nr_topics=50)
	print(f"Saving {reducedmodel_path}")
	topic_model.save(str(reducedmodel_path))

	print("Preparing CSV data.")

	new_data = [
		{
			"topics": topic,
			"probabilities": probability,
			"reduced_topics": reduced_topic,
			"reduced_probabilities": reduced_probability
		}
		for topic, probability, reduced_topic, reduced_probability in
		zip(topics, probs, reduced_topics, reduced_probs)
	]

	fieldnames = ["subscription_id", "subscription_name", "user_id", "user_name", "tweet_id", "text", "created_at", "doc", "topics", "probabilities", "reduced_topics", "reduced_probabilities"]
	print(f"Saving to {csv_path}")
	tweets = [tweet | data for tweet, data in zip(tweets, new_data)]
	tweet_wrangling.save_tweets(tweets, csv_path, fieldnames)



if __name__ == "__main__":
	train()