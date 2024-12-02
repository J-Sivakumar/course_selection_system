from flask import *
import sqlite3
app = Flask(__name__)
app.secret_key= '1234'   

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/stdlogin')
def stdlogin():
    return render_template('stdlogin.html') 


@app.route('/stdhome',methods=['POST','GET'])
def stdhome():
    if 'student_id' in session:
        with sqlite3.connect('users.db') as con:
            cursor = con.cursor()
            cursor.execute('Select * from Students where student_id ="'+session['student_id']+'"')
            data = cursor.fetchall()
            return render_template('stdhome.html',name=data[0][2])
        
    msg = "Invalid email/password"
    try:          
        with sqlite3.connect('users.db') as con:
            cursor = con.cursor()
            cursor.execute('Select * from Students where student_id ="'+request.form['student_id']+'"')
            data = cursor.fetchall()
            print(data)
            if data:
                if data[0][1]==request.form['password']:
                    msg = 'Login successfully'
                    if request.method =='POST':
                        session['student_id'] = request.form['student_id']
                    if 'student_id' in session:
                        return render_template('stdhome.html',name=data[0][2])
                    
                else:
                    msg = "Invalid email/password"
            
            
    except BaseException as e:
        msg =e
        con.rollback()
    finally:
        con.close()
    return render_template('stdlogin.html',msg=msg)
    

@app.route('/stdchangepwd')
def stdchangepwd():
    return render_template("stdupdatepwd.html")

@app.route('/stdupdatepwd', methods=['POST'])
def stdupdatepwd():
    data = []
    if request.method == 'POST':
        student_id = request.form['student_id']
        password = request.form['password']
        
        try:      
            with sqlite3.connect('users.db') as con:
                cursor = con.cursor()
                cursor.execute('UPDATE Students SET password = ? WHERE student_id = ?', (password, student_id))
                con.commit()
               
                cursor.execute('SELECT * FROM Students WHERE student_id = ?', (student_id,))
                data = cursor.fetchall()

        except sqlite3.Error as e:
            if con:
                con.rollback()
        finally:
            return render_template("stdprofile.html", data=data)
    
    return render_template("stdprofile.html", data=data)

@app.route('/stdprofile')
def stdprofile():
    if 'student_id' in session:
        try:      
            with sqlite3.connect('users.db') as con:
                cursor = con.cursor()
                cursor.execute('SELECT * FROM Students WHERE student_id = ?', (session['student_id'],))
                data = cursor.fetchall()  
                if data:
                    return render_template('stdprofile.html', data=data)  
                else:
                    return 'No student found with the given ID', 404
        except Exception as e:
            con.rollback()
            return str(e), 500  
    else:
        abort(401) 

@app.route('/stdlogout')
def stdlogout():
    if 'student_id' in session:
        session.pop('student_id',None)
        return render_template('stdlogout.html')
    return "You are already logout"


departments = {
    "Computer Science": ["1st Year", "2nd Year", "3rd Year", "4th Year"],
    "Civil Engineering": ["1st Year", "2nd Year", "3rd Year", "4th Year"],\
    "Electrical Engineering": ["1st Year", "2nd Year", "3rd Year", "4th Year"],
    "Mechanical Engineering": ["1st Year", "2nd Year", "3rd Year", "4th Year"],
}

years = {
    "1st Year": ["1", "2"],
    "2nd Year": ["3", "4"],
    "3rd Year": ["5", "6"],
    "4th Year": ["7", "8"],
}

def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row  
    return conn
dept=''
@app.route('/get_data',methods=['POST'])
def get_data():
    global dept
    data = request.json
    selection_type = data['type']
    selected_value = data['value']
    conn = get_db_connection()
    if selection_type == 'department':
        next_options = departments.get(selected_value, [])
        dept = selected_value
    elif selection_type == 'year':
        next_options = years.get(selected_value, [])
    elif selection_type == 'semester':
        courses = conn.execute('SELECT course_name FROM courses WHERE semester = ? and branch = ?', (selected_value,dept)).fetchall()
        result = [row['course_name'] for row in courses]
        return jsonify(result)
    elif selection_type == 'course':
        faculties = conn.execute('''SELECT t.staff_id, t.faculty_name, t.department, tc.course_id FROM  Teachers t ,  TeacherCourse tc , Courses c where t.staff_id = tc.staff_id and c.course_id=tc.course_id and course_name = ?''', (selected_value,)).fetchall()
        result = [row['faculty_name'] for row in faculties]
        return jsonify(result)
    conn.close()

    return jsonify(next_options)

@app.route('/get_next')
def get_next():
    return render_template('selectCourse.html')
@app.route('/stdUpdateTables', methods=[ 'POST'])
def std_update_tables():
    if request.method == 'POST':
        # Get form data
        semester = request.form.get('semester')
        course = request.form['course']
        faculty = request.form['faculty']

        con = sqlite3.connect('users.db')
        cur = con.cursor()

        cur.execute("SELECT course_id FROM Courses WHERE course_name=? AND semester=?", (course, semester))
        courseid = cur.fetchone()[0]

        cur.execute("SELECT staff_id FROM Teachers WHERE faculty_name=?", (faculty,))
        teacherid = cur.fetchone()[0]

        cur.execute("INSERT INTO Selections (studentid, courseid, teacherid) VALUES (?, ?, ?)", (session['student_id'], courseid, teacherid))
        con.commit()
        con.close()
        return render_template('stdhome.html')
    
    return render_template('stdUpdateTables.html')

@app.route('/display_selections')
def display_selections():
    sid=session['student_id']
    con = sqlite3.connect('users.db')
    cur = con.cursor()
    cur.execute("""
        SELECT 
            S.studentid, 
            St.student_name, 
            C.course_name, 
            T.faculty_name
        FROM 
            Selections S
        JOIN 
            Students St ON S.studentid = St.student_id
        JOIN 
            Courses C ON S.courseid = C.course_id
        JOIN 
            Teachers T ON S.teacherid = T.staff_id
    WHERE 
            S.studentid = ?
    """, (sid,))
    selections = cur.fetchall()
    con.close()

    return render_template('displaySelections.html', selections=selections)


# Staff


@app.route('/facultylogin')
def facultylogin():
    return render_template('facultylogin.html') 


@app.route('/facultyhome',methods=['POST','GET'])
def facultyhome():
    if 'staff_id' in session:
        with sqlite3.connect('users.db') as con:
            cursor = con.cursor()
            cursor.execute('Select * from Teachers where staff_id ="'+session['staff_id']+'"')
            data = cursor.fetchall()
            return render_template('facultyhome.html',name=data[0][2])
        
    msg = "Invalid email/password"
    try:          
        with sqlite3.connect('users.db') as con:
            cursor = con.cursor()
            cursor.execute('Select * from Teachers where staff_id ="'+request.form['staff_id']+'"')
            data = cursor.fetchall()
            if data:
                if data[0][1]==request.form['password']:
                    msg = 'Login successfully'
                    if request.method =='POST':
                        session['staff_id'] = request.form['staff_id']
                    if 'staff_id' in session:
                        return render_template('facultyhome.html',name=data[0][2])
                    
                else:
                    msg = "Invalid email/password"
            
            
    except BaseException as e:
        msg =e
        con.rollback()
    finally:
        con.close()
    return render_template('facultylogin.html',msg=msg)
    

@app.route('/facultychangepwd')
def facultychangepwd():
    return render_template("facultyupdatepwd.html")

@app.route('/facultyupdatepwd', methods=['POST'])
def facultyupdatepwd():
    data = []
    if request.method == 'POST':
        staff_id = request.form['staff_id']
        password = request.form['password']
        
        try:      
            with sqlite3.connect('users.db') as con:
                cursor = con.cursor()
                cursor.execute('UPDATE Teachers SET password = ? WHERE staff_id = ?', (password, staff_id))
                con.commit()
               
                cursor.execute('SELECT * FROM Teachers WHERE staff_id = ?', (staff_id,))
                data = cursor.fetchall()

        except sqlite3.Error as e:
            if con:
                con.rollback()
        finally:
            return render_template("facultyprofile.html", data=data)
    
    return render_template("facultyprofile.html", data=data)

@app.route('/facultyprofile')
def facultyprofile():
    if 'staff_id' in session:
        try:      
            with sqlite3.connect('users.db') as con:
                cursor = con.cursor()
                cursor.execute('SELECT * FROM Teachers WHERE staff_id = ?', (session['staff_id'],))
                data = cursor.fetchall()  
                if data:
                    return render_template('facultyprofile.html', data=data)  
                else:
                    return 'No staff found with the given ID', 404
        except Exception as e:
            con.rollback()
            return str(e), 500  
    else:
        abort(401) 

@app.route('/facultylogout')
def facultylogout():
    if 'staff_id' in session:
        session.pop('staff_id',None)
        return render_template('facultylogout.html')
    return "You are already logout"


@app.route('/display_teachers_courses')
def display_teachers_courses():
    teacher_id=session['staff_id']
    con = sqlite3.connect('users.db')
    cur = con.cursor()

    cur.execute("""
        SELECT 
            T.faculty_name, 
            C.course_name 
        FROM 
            TeacherCourse TC
        JOIN 
            Teachers T ON TC.staff_id = T.staff_id
        JOIN 
            Courses C ON TC.course_id = C.course_id
    WHERE 
            T.staff_id = ?
    """, (teacher_id,))

    teacher_courses = cur.fetchall()
    
    con.close()

    return render_template('display_teachers_courses.html', teacher_courses=teacher_courses)

@app.route('/teacher_students')
def teacher_students():
    teacher_id=session['staff_id']
    con = sqlite3.connect('users.db')
    cur = con.cursor()

    cur.execute("""
        SELECT 
            T.faculty_name, 
            C.course_name, 
            S.student_name 
        FROM 
            TeacherCourse TC
        JOIN 
            Teachers T ON TC.staff_id = T.staff_id
        JOIN 
            Courses C ON TC.course_id = C.course_id
        JOIN 
            Selections E ON E.courseid = C.course_id
        JOIN 
            Students S ON E.studentid = S.student_id
        WHERE 
            T.staff_id = ?
    """, (teacher_id,))

    teacher_students = cur.fetchall()

    con.close()

    if not teacher_students:
        return  redirect(url_for('TeacherResults'))

    return render_template('teacher_students.html', teacher_students=teacher_students)
    
@app.route('/TeacherResults')
def TeacherResults():
    teacher_id=session['staff_id']
    message=f"No students found under Teacher ID: {teacher_id}"
    flash(message)
    return render_template("TeacherResults.html")


#Admin


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/adminlogin')
def adminlogin():
    return render_template('adminlogin.html')

@app.route('/adminlogout')
def adminlogout():
    return render_template('adminlogout.html')

@app.route('/adminloginvalidate',methods=['POST'])
def adminloginvalidate():
    if request.method == 'POST':
        username = request.form['admin_id']
        password = request.form['password']

        valid_username = 'admin'
        valid_password = 'admin'

        if username == valid_username and password == valid_password:
            session['username'] = username  
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard')) 
        else:
            flash('Invalid credentials. Please try again.', 'danger')

    return render_template('adminlogin.html')

@app.route('/manage_students')
def manage_students():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Students')
    students = cursor.fetchall()
    conn.close()
    return render_template('manage_students.html', students=students)

@app.route('/add_student', methods=['POST'])
def add_student():
    student_id = request.form['student_id']
    student_name = request.form['student_name']
    department = request.form['department']
    year = request.form['year']
    semester = request.form['semester']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO Students (student_id,password,department,year,semester, student_name) VALUES (?, ?,?, ?,?, ?)', (student_id, student_id, department, year,semester, student_name))
    conn.commit()
    conn.close()
    flash('Student added successfully!','success')
    return redirect(url_for('manage_students'))

@app.route('/delete_student/<student_id>', methods=['POST'])
def delete_student(student_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM Students WHERE student_id = ?', (student_id,))
    conn.commit()
    conn.close()
    flash('Student deleted successfully!','warning')
    return redirect(url_for('manage_students'))

@app.route('/manage_courses')
def manage_courses():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Courses')
    courses = cursor.fetchall()
    conn.close()
    return render_template('manage_courses.html', courses=courses)

@app.route('/add_course', methods=['POST'])
def add_course():
    course_id = request.form['course_id']
    course_name = request.form['course_name']
    branch = request.form['department']
    semester = request.form['semester']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO Courses (course_id, course_name, branch, semester) VALUES (?, ?, ?, ?)', (course_id, course_name, branch, semester))
    conn.commit()
    conn.close()
    flash('Course added successfully!', 'success')
    return redirect(url_for('manage_courses'))

@app.route('/delete_course/<course_id>', methods=['POST'])
def delete_course(course_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM Courses WHERE course_id = ?', (course_id,))
    conn.commit()
    conn.close()
    flash('Course deleted successfully!' , 'danger')
    return redirect(url_for('manage_courses'))

# Manage Teachers
@app.route('/manage_teachers')
def manage_teachers():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Teachers')
    teachers = cursor.fetchall()
    conn.close()
    return render_template('manage_teachers.html', teachers=teachers)

@app.route('/add_teacher', methods=['POST'])
def add_teacher():
    teacher_id = request.form['teacher_id']
    teacher_name = request.form['teacher_name']
    qualification = request.form.get('qualification')
    designation = request.form.get('designation')
    department = request.form['department']
    research_projects = request.form.get('research_projects', '')  # Empty if not provided
    patents = request.form.get('patents', '')  # Empty if not provided
    rating = float(request.form.get('rating'))  # Rating should be a float
    years_of_experience = int(request.form.get('years_of_experience'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO Teachers (staff_id,password, faculty_name,qualification, designation, research_projects, patents, rating, years_of_experience, department) VALUES (?, ?,?, ?,?, ?,?, ?,?, ?)', (teacher_id,teacher_id, teacher_name,qualification, designation, research_projects, patents, rating, years_of_experience, department))
    conn.commit()
    conn.close()
    flash('Teacher added successfully!','success')
    return redirect(url_for('manage_teachers'))

@app.route('/delete_teacher/<teacher_id>', methods=['POST'])
def delete_teacher(teacher_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM Teachers WHERE staff_id = ?', (teacher_id,))
    conn.commit()
    conn.close()
    flash('Teacher deleted successfully!')
    return redirect(url_for('manage_teachers'))


if __name__=='__main__':
    app.run(debug = True)


