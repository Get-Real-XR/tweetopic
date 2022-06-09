from dash import Dash, dcc, html
import plotly.express as px
from base64 import b64encode
import io

from bertopic import BERTopic
import tweet_wrangling


def visualize_modeL(topic_model: BERTopic, tweets):
	docs, topics, probabilities, timestamps = tweet_wrangling.dict_zip(tweets,
	                                    ["docs", "reduced_topics", "reduced_probabilities", "created_at"]).values()

	results, score = topic_model.find_topics("technology augmented_reality virtual_reality", top_n=20)

	topics_over_time = topic_model.topics_over_time(docs, topics, timestamps, nr_bins=20)


	figures = [
		# topic_model.visualize_topics(top_n_topics=30),
		topic_model.visualize_topics(),
		topic_model.visualize_term_rank(topics=list(range(30))),
		topic_model.visualize_hierarchy(topics=results),
		topic_model.visualize_heatmap(results),
		topic_model.visualize_barchart(results),
		topic_model.visualize_topics_over_time(topics_over_time=topics_over_time, topics=results)]

	render(figures)


# topic_model.visualize_distribution(probabilities[doc_id]),
#
# topic_model.visualize_topics_per_class(),
# topic_model.visualize_distribution(probabilities)]


def render(figures):
	app = Dash(__name__)

	# html easily obtainable like so
	# buffer = io.StringIO()
	# for fig in figures:
	# 	fig.write_html(buffer)
	# html_bytes = buffer.getvalue().encode()
	# encoded = b64encode(html_bytes).decode()

	app.layout = html.Div([
		html.H2('GRV Topic Modeling Visualization Demo'),
		*[dcc.Graph(id=f"graph{i}", figure=f) for i, f in enumerate(figures)]
	])

	app.run_server(debug=True)
