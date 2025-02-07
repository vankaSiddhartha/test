from flask import Flask, request, jsonify
import re
from typing import Dict, Union

app = Flask(__name__)


def analyze_feedback(feedback: Dict[str, Union[int, str]]) -> Dict[str, Union[float, str]]:
    """Analyze feedback sentiment using a simple rule-based approach."""
    sentiment_scores = {
        'numerical_sentiment': 0.0,
        'text_sentiment': 0.0,
        'overall_sentiment': 0.0,
        'summary': ''
    }

    # Analyze rating (1-5 scale)
    rating_sentiment = (feedback['rating'] - 1) / 4  # Normalize to 0-1

    # Analyze connection quality
    quality_scores = {
        'excellent': 1.0, 'good': 0.75, 'fair': 0.5, 'poor': 0.25, '': 0.5
    }
    quality_sentiment = quality_scores.get(feedback['quality'].lower(), 0.5)

    # Text analysis of comments
    comments = feedback.get('comments', '').lower()

    positive_words = {
        'great': 1.0, 'excellent': 1.0, 'good': 0.8, 'nice': 0.8,
        'helpful': 0.9, 'smooth': 0.9, 'clear': 0.8, 'awesome': 1.0,
        'perfect': 1.0, 'wonderful': 1.0, 'fantastic': 1.0, 'easy': 0.8,
        'enjoyed': 0.9, 'pleasure': 0.9, 'effective': 0.8
    }

    negative_words = {
        'bad': -0.8, 'poor': -0.8, 'terrible': -1.0, 'awful': -1.0,
        'horrible': -1.0, 'unclear': -0.7, 'difficult': -0.7,
        'issue': -0.6, 'problem': -0.6, 'lag': -0.8, 'stuck': -0.7,
        'freeze': -0.8, 'disconnect': -0.9, 'crash': -0.9
    }

    # Calculate text sentiment
    words = re.findall(r'\w+', comments)
    sentiment_sum = 0
    sentiment_count = 0

    for word in words:
        if word in positive_words:
            sentiment_sum += positive_words[word]
            sentiment_count += 1
        elif word in negative_words:
            sentiment_sum += negative_words[word]
            sentiment_count += 1

    text_sentiment = 0.5  # Neutral default
    if sentiment_count > 0:
        text_sentiment = (sentiment_sum / sentiment_count +
                          1) / 2  # Normalize to 0-1

    # Calculate overall sentiment
    sentiment_scores['numerical_sentiment'] = rating_sentiment
    sentiment_scores['text_sentiment'] = text_sentiment
    sentiment_scores['overall_sentiment'] = (
        rating_sentiment * 0.4 +
        quality_sentiment * 0.3 +
        text_sentiment * 0.3
    )

    # Generate summary
    if sentiment_scores['overall_sentiment'] >= 0.8:
        summary = "Very Positive Feedback"
    elif sentiment_scores['overall_sentiment'] >= 0.6:
        summary = "Positive Feedback"
    elif sentiment_scores['overall_sentiment'] >= 0.4:
        summary = "Neutral Feedback"
    elif sentiment_scores['overall_sentiment'] >= 0.2:
        summary = "Negative Feedback"
    else:
        summary = "Very Negative Feedback"

    sentiment_scores['summary'] = summary
    return sentiment_scores

"""Flask Api to intract with frontend"""
@app.route('/analyze', methods=['POST'])
def analyze():
    """API Endpoint to analyze feedback."""
    data = request.get_json()

    # Validate input
    if not data or 'rating' not in data or 'quality' not in data or 'comments' not in data:
        return jsonify({"error": "Invalid input"}), 400

    result = analyze_feedback(data)
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)
