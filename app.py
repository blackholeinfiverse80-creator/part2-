from flask import Flask, request, jsonify
from models import db, Generation
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/context_intelligence.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()

def get_related_context(text, top_k=3):
    gens = Generation.query.filter(Generation.text.isnot(None)).all()
    if not gens:
        return []
    
    # Simple keyword-based similarity for demo
    text_words = set(text.lower().split())
    rankings = []
    
    for g in gens:
        gen_words = set(g.text.lower().split())
        similarity = len(text_words.intersection(gen_words)) / max(len(text_words.union(gen_words)), 1)
        ranking = 0.7 * similarity + 0.3 * (g.score / 10.0)  # Normalize score
        rankings.append((g, ranking))
    
    rankings.sort(key=lambda x: x[1], reverse=True)
    return [{"text": g.text, "score": round(ranking, 3)} for g, ranking in rankings[:top_k]]

@app.route('/')
def root():
    return jsonify({
        "message": "Creator Core API",
        "version": "1.0.0",
        "endpoints": {
            "generate": "POST /generate",
            "feedback": "POST /feedback", 
            "history": "GET /history"
        }
    })

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