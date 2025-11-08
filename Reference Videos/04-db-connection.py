from flask import Flask, request, jsonify, abort
from model import db, Student

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def create_tables():
    db.create_all()

app.before_request(create_tables)

@app.route("/students", methods = ['GET'])
def get_students():
    students = Student.query.all()
    return jsonify([students.to_dict() for student in students])

@app.route("/students/<int:student_id>", methods = ["GET"])
def get_student(student_id):
    student = Student.query.get_or_404(student_id)
    return jsonify(student.to_dict())

@app.route("/student", methods=['POST'])
def create_student():
    print(request.json)
    
    if not request.json or not 'name' in request.json:
        abort(400)
    
    student = Student(
        name = request.json['name'],
        age = request.json.get("age", ""),
        grade = request.json.get('grade', "")

    )

    try:
        db.session.add(student)
        db.session.commit()
    
    except Exception as e:
        print(e)
        return jsonify({'error': 'Student already exists'}), 409
    
    return jsonify(student.to_dict()), 201

@app.route('/students/<int:student_id>', methods = ['PUT'])
def update_student(student_id):
    try:
        student = Student.query.get_or_404(student_id)
        if not request:
            abort(400)
        
        student.name = request.json.get('name', student.name)
        student.age = request.json.get('age', student.age)
        student.grade = request.json.get('grade', student.grade)

        db.session.commit()
    except Exception as e:
        print(e)
        return jsonify({"error": "Student does not exist"})
    
    return jsonify(student.to_dict()), 200



@app.route('/student/<int:student_id>', methods = ["DELETE"])
def delete_student(student_id):
    try:
        student = Student.query.get_or_404(student_id)
        db.session.delete(student)
        db.session.commit()
    
    except Exception as e:
        print(e)
        return jsonify({"error": "Student does not exist"})
    
    return jsonify({'return': True, "message": f"student {student_id} deleted"})



if __name__ == "__main__":
    app.run(debug=True)
