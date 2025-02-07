from flask import Flask, request, jsonify
from firebase_admin import credentials, initialize_app, db
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os

app = Flask(__name__)

# Initialize Firebase Admin SDK
# Replace with your Firebase credentials path
cred = credentials.Certificate("alnumunai/firebase/config.js")
initialize_app(cred, {
    # Replace with your Firebase database URL
    'databaseURL': 'pavan-ce10b.firebaseapp.com"'
})


class DomainRecommender:
    def __init__(self):
        self.domains = {
            'ai': {
                'name': 'AI & Machine Learning',
                'keywords': 'machine learning artificial intelligence deep learning neural networks nlp computer vision pytorch tensorflow keras data science algorithms',
                'core_skills': ['Python', 'Mathematics', 'Deep Learning', 'Statistics'],
                'projects': ['Image Classification', 'Natural Language Processing', 'Predictive Models']
            },
            'web': {
                'name': 'Web Development',
                'keywords': 'web development frontend backend fullstack javascript react angular vue nodejs express django html css apis rest graphql',
                'core_skills': ['JavaScript', 'HTML/CSS', 'React', 'Node.js'],
                'projects': ['Web Applications', 'RESTful APIs', 'E-commerce Sites']
            },
            'data': {
                'name': 'Data Science',
                'keywords': 'data science analytics visualization statistics sql database hadoop spark big data etl pandas numpy matplotlib',
                'core_skills': ['Python', 'SQL', 'Statistics', 'Data Visualization'],
                'projects': ['Data Analysis', 'Business Intelligence', 'Statistical Modeling']
            },
            'cloud': {
                'name': 'Cloud Computing',
                'keywords': 'cloud computing aws azure gcp kubernetes docker devops ci cd serverless microservices iaas paas',
                'core_skills': ['AWS/Azure/GCP', 'Docker', 'Kubernetes', 'Linux'],
                'projects': ['Cloud Migration', 'Infrastructure Automation', 'Container Orchestration']
            },
            'systems': {
                'name': 'Systems Design',
                'keywords': 'systems design architecture distributed systems scalability performance optimization networking security protocols',
                'core_skills': ['System Architecture', 'Distributed Systems', 'Performance Optimization'],
                'projects': ['High-Scale Systems', 'Distributed Applications', 'System Integration']
            }
        }

        self.vectorizer = TfidfVectorizer(stop_words='english')
        domain_texts = [domain['keywords'] for domain in self.domains.values()]
        self.domain_vectors = self.vectorizer.fit_transform(domain_texts)

    def get_recommendations(self, student_profile):
        profile_text = f"{student_profile.get('interests', '')} "
        profile_text += ' '.join(student_profile.get('skills', []))
        profile_text += ' '.join(student_profile.get('projects', []))

        profile_vector = self.vectorizer.transform([profile_text])
        similarity_scores = cosine_similarity(
            profile_vector, self.domain_vectors)[0]

        domain_scores = list(zip(self.domains.keys(), similarity_scores))
        sorted_recommendations = sorted(
            domain_scores, key=lambda x: x[1], reverse=True)

        return [
            {
                'domain_id': domain_id,
                'name': self.domains[domain_id]['name'],
                'score': float(score),
                'core_skills': self.domains[domain_id]['core_skills'],
                'projects': self.domains[domain_id]['projects']
            }
            for domain_id, score in sorted_recommendations
        ]


# Initialize recommender
recommender = DomainRecommender()


def get_user_profile(user_id):
    """Fetch user profile from Firebase"""
    try:
        user_ref = db.reference(f'users/{user_id}')
        user_data = user_ref.get()

        if not user_data:
            return None

        return {
            'interests': user_data.get('interests', ''),
            'skills': user_data.get('skills', []),
            'projects': user_data.get('projects', [])
        }
    except Exception as e:
        print(f"Error fetching user profile: {e}")
        return None


def update_user_recommendations(user_id, recommendations):
    """Update user's recommendations in Firebase"""
    try:
        user_ref = db.reference(f'users/{user_id}/recommendations')
        user_ref.set({
            'timestamp': {'.sv': 'timestamp'},
            'domains': recommendations
        })
        return True
    except Exception as e:
        print(f"Error updating recommendations: {e}")
        return False


@app.route('/api/recommendations/<user_id>', methods=['GET'])
def get_recommendations(user_id):
    """Get domain recommendations for a user"""
    try:
        # Fetch user profile from Firebase
        user_profile = get_user_profile(user_id)

        if not user_profile:
            return jsonify({
                'error': 'User profile not found'
            }), 404

        # Generate recommendations
        recommendations = recommender.get_recommendations(user_profile)

        # Update recommendations in Firebase
        update_success = update_user_recommendations(user_id, recommendations)

        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'updated_in_firebase': update_success
        })

    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/recommendations/batch', methods=['POST'])
def batch_recommendations():
    """Generate recommendations for multiple users"""
    try:
        user_ids = request.json.get('user_ids', [])
        results = {}

        for user_id in user_ids:
            user_profile = get_user_profile(user_id)
            if user_profile:
                recommendations = recommender.get_recommendations(user_profile)
                update_success = update_user_recommendations(
                    user_id, recommendations)
                results[user_id] = {
                    'success': True,
                    'recommendations': recommendations,
                    'updated_in_firebase': update_success
                }
            else:
                results[user_id] = {
                    'success': False,
                    'error': 'User profile not found'
                }

        return jsonify(results)

    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/profile/<user_id>', methods=['PUT'])
def update_profile(user_id):
    """Update user profile and generate new recommendations"""
    try:
        profile_data = request.json

        # Update profile in Firebase
        user_ref = db.reference(f'users/{user_id}')
        user_ref.update(profile_data)

        # Generate new recommendations
        user_profile = get_user_profile(user_id)
        recommendations = recommender.get_recommendations(user_profile)
        update_success = update_user_recommendations(user_id, recommendations)

        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'updated_in_firebase': update_success
        })

    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


if __name__ == '__main__':
    app.run(debug=True)
