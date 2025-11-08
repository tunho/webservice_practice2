from flask import Flask, request, jsonify
from model import db, Student
from datetime import datetime

app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# 생성 테이블 생성 
with app.app_context():
    db.create_all()



# 공통 응답 포맷을 하기 위해서 만든 함수 

def make_response(status: str, data=None, message=None, code=200):
    body = {"status": status}
    if message is not None:
        body["message"] = message
    if data is not None:
        body["data"] = data
    return jsonify(body), code



# Middleware/ 요청 로그 (C)

@app.before_request
def log_request():
    print(
        f"[{datetime.now()}] {request.method} {request.path} "
        f"Headers={dict(request.headers)} "
        f"Body={request.get_json(silent=True)}"
    )



# 에러 코드

@app.errorhandler(400)
def bad_request(e):
    return make_response("fail", message="Bad Request", code=400)

@app.errorhandler(404)
def not_found(e):
    return make_response("fail", message="Resource Not Found", code=404)

@app.errorhandler(500)
def internal_error(e):
    return make_response("error", message="Internal Server Error", code=500)



# 1) POST: 3개 B


# POST 1 학생 생성
@app.route("/students", methods=["POST"])
def create_student():
    data = request.get_json(silent=True)

    if not data or "name" not in data:
        return make_response("fail", message="name is required", code=400)

    name = data["name"]
    age = data.get("age")
    grade = data.get("grade")
    is_active = data.get("is_active", True)

    # 이름 중복 체크 → 409 (Conflict)
    if Student.query.filter_by(name=name).first():
        return make_response(
            "fail",
            message="Student with this name already exists",
            code=409
        )

    student = Student(name=name, age=age, grade=grade, is_active=is_active)
    db.session.add(student)
    db.session.commit()

    return make_response("success", data=student.to_dict(), code=201)


# POST 2 학생 활성화 (is_active True로 변경)
@app.route("/students/<int:student_id>/activate", methods=["POST"])
def activate_student(student_id):
    student = Student.query.get(student_id)
    if not student:
        return make_response("fail", message="Student not found", code=404)

    student.is_active = True
    db.session.commit()
    return make_response(
        "success",
        message="Student activated",
        data=student.to_dict(),
        code=200
    )

# POST 3 학생 비활성화 (is_active False로 변경)
@app.route("/students/<int:student_id>/deactivate", methods=["POST"])
def deactivate_student(student_id):
    student = Student.query.get(student_id)
    if not student:
        return make_response("fail", message="Student not found", code=404)

    if not student.is_active:
        return make_response("fail", message="Student already inactive", code=400)

    student.is_active = False
    db.session.commit()

    return make_response(
        "success",
        message="Student deactivated",
        data=student.to_dict(),
        code=200
    )



# 2) GET: 2개  B


# GET 1 전체 학생 조회
@app.route("/students", methods=["GET"])
def get_students():
    students = Student.query.all()
    return make_response(
        "success",
        data=[s.to_dict() for s in students],
        code=200
    )


# GET 2 특정 학생 조회
@app.route("/students/<int:student_id>", methods=["GET"])
def get_student(student_id):
    student = Student.query.get(student_id)
    if not student:
        return make_response("fail", message="Student not found", code=404)
    return make_response("success", data=student.to_dict(), code=200)



# 3) PUT: 2개 B


# PUT 1 학생 정보 전체 수정(Partial Update 허용)
@app.route("/students/<int:student_id>", methods=["PUT"])
def update_student(student_id):
    student = Student.query.get(student_id)
    if not student:
        return make_response("fail", message="Student not found", code=404)

    data = request.get_json(silent=True)
    if not data:
        return make_response("fail", message="JSON body required", code=400)

    student.name = data.get("name", student.name)
    student.age = data.get("age", student.age)
    student.grade = data.get("grade", student.grade)
    student.is_active = data.get("is_active", student.is_active)

    db.session.commit()
    return make_response(
        "success",
        message="Student updated",
        data=student.to_dict(),
        code=200
    )


# PUT 2 학생 성적(grade)만 수정
@app.route("/students/<int:student_id>/grade", methods=["PUT"])
def update_student_grade(student_id):
    student = Student.query.get(student_id)
    if not student:
        return make_response("fail", message="Student not found", code=404)

    data = request.get_json(silent=True)
    if not data or "grade" not in data:
        return make_response("fail", message="grade is required", code=400)

    student.grade = data["grade"]
    db.session.commit()
    return make_response(
        "success",
        message="Grade updated",
        data=student.to_dict(),
        code=200
    )







# 4) DELETE: 2개  B

# DELETE 1 특정 학생 삭제
@app.route("/students/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):
    student = Student.query.get(student_id)
    if not student:
        return make_response("fail", message="Student not found", code=404)

    db.session.delete(student)
    db.session.commit()

    return make_response(
        "success",
        message=f"Student {student_id} deleted",
        code=200
    )


# DELETE 2 비활성 학생 전체 삭제
@app.route("/students/inactive", methods=["DELETE"])
def delete_inactive_students():
    inactive_students = Student.query.filter_by(is_active=False).all()

    if not inactive_students:

        return make_response(
            "fail",
            message="No inactive students to delete",
            code=404
        )

    for s in inactive_students:
        db.session.delete(s)
    db.session.commit()

    return make_response(
        "success",
        message="All inactive students deleted",
        code=200
    )



# 서버 일시적으로 사용 불가 사
@app.route("/students/db-error", methods=["GET"])
def db_error_demo():
    
    return make_response("error", message="Service temporarily unavailable", code=503)


 # 0으로 나눌 때
@app.route("/students/error", methods=["GET"])
def internal_error_demo():
   
    1 / 0
    return make_response("error", message="This will never be reached", code=500)



if __name__ == "__main__":
    app.run(debug=True)
