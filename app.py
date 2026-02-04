from flask import Flask, request, jsonify
from models import db, Generation
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Simple TF-IDF based similarity instead of sentence transformers
vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///context_intelligence.db'
db.init_app(app)

with app.app_context():
    db.create_all()

def get_related_context(text, top_k=3):
    gens = Generation.query.filter(Generation.text.isnot(None)).all()
    if not gens:
        return []
    
    texts = [g.text for g in gens] + [text]
    try:
        tfidf_matrix = vectorizer.fit_transform(texts)
        similarities = cosine_similarity(tfidf_matrix[-1:], tfidf_matrix[:-1]).flatten()
    except:
        return []
    
    # Normalize scores
    scores = [g.score for g in gens]
    min_score = min(scores) if scores else 0
    max_score = max(scores) if scores else 1
    if max_score == min_score:
        norm_scores = [0.5] * len(scores)
    else:
        norm_scores = [(s - min_score) / (max_score - min_score) for s in scores]
    
    rankings = []
    for i, g in enumerate(gens):
        sim = similarities[i] if i < len(similarities) else 0
        ranking = 0.7 * sim + 0.3 * norm_scores[i]
        rankings.append((g, ranking))
    rankings.sort(key=lambda x: x[1], reverse=True)
    return [{"text": g.text, "score": round(ranking, 3)} for g, ranking in rankings[:top_k]]

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    prompt = data.get('prompt', '')
    # Simulate generation - in real scenario, this would call an AI model
    generated_text = prompt + " generated content."
    
    # Save to DB (no embedding needed with TF-IDF)
    gen = Generation(text=generated_text)
    db.session.add(gen)
    db.session.commit()
    
    # Get related context
    related_context = get_related_context(generated_text, 3)
    
    return jsonify({"generated_text": generated_text, "related_context": related_context})

@app.route('/feedback', methods=['POST'])
def feedback():
    data = request.json
    gen_id = data.get('generation_id')
    command = data.get('command')  # e.g. "+2", "-1"
    
    gen = Generation.query.get(gen_id)
    if not gen:
        return jsonify({"error": "Generation not found"}), 404
    
    # Parse command
    if command.startswith('+'):
        adjust = float(command[1:])
    elif command.startswith('-'):
        adjust = -float(command[1:])
    else:
        return jsonify({"error": "Invalid command"}), 400
    
    gen.score += adjust
    db.session.commit()
    
    return jsonify({"message": "Feedback applied", "new_score": gen.score})

@app.route('/history', methods=['GET'])
def history():
    gens = Generation.query.order_by(Generation.created_at.desc()).all()
    result = [{"id": g.id, "text": g.text, "score": g.score, "created_at": g.created_at.isoformat()} for g in gens]
    return jsonify(result)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)