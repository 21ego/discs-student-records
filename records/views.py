from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ValidationError
from .models import Student
from .utils import build_hash_table, merge_sort, UndoRedoManager, sort_by_id, sort_by_name, sort_by_qpi

# per-record undo/redo stacks
history_managers = {} # stacks per student

def student_list(request):
    # build hash table for all students
    students = list(Student.objects.all())
    hash_table = build_hash_table(students)
    course_list = ["BS MIS", "BS CS", "BS CS-DGDD"]

    filtered_students = []

    # search
    q = request.GET.get("q")
    if q:
        if q in hash_table:
            filtered_students = [hash_table[q]]
        else:
            for sid, student in hash_table.items():
                if q.lower() in student.name.lower() or q.lower() in student.course.lower():
                    filtered_students.append(student)
    else:
        filtered_students = list(hash_table.values())

    # filters
    year = request.GET.get("year")
    if year and year != "ALL":
        filtered_students = [s for s in filtered_students if str(s.year) == year]

    course = request.GET.get("course")
    if course and course != "ALL":
        filtered_students = [s for s in filtered_students if s.course == course]

    # sorting
    sort = request.GET.get("sort")
    order = request.GET.get("order", "asc")
    reverse = (order == "desc")

    if sort == "id":
        filtered_students = merge_sort(filtered_students, key=sort_by_id, reverse=reverse)
    elif sort == "name":
        filtered_students = merge_sort(filtered_students, key=sort_by_name, reverse=reverse)
    elif sort == "qpi":
        filtered_students = merge_sort(filtered_students, key=sort_by_qpi, reverse=reverse)

    # count how many students
    record_count = len(filtered_students)

    return render(request, "records/student_list.html", {
        "students": filtered_students,
        "course_list": course_list,
        "record_count": record_count
    })


def student_add(request):
    course_list = ["BS MIS", "BS CS", "BS CS-DGDD"]
    error = None
    if request.method == "POST":
        try:
            student_id = request.POST["id"].strip()
            student_name = request.POST["name"].strip().lower().title()
            
            # Check for duplicate ID
            if Student.objects.filter(id=student_id).exists():
                raise ValidationError(f"A student with ID {student_id} already exists.")
            
            # Check for duplicate Name
            if Student.objects.filter(name=student_name).exists():
                raise ValidationError(f"A student with the name '{student_name}' already exists.")

            s = Student(
                id=student_id,
                name=student_name,
                qpi=float(request.POST["qpi"]),
                year=int(request.POST["year"]),
                course=request.POST["course"].strip()
            )
            s.clean()
            s.save()
            history_managers[s.id] = UndoRedoManager()
            return redirect("student_list")
        except ValidationError as e:
            error = e.messages[0]  # show first error message
        except ValueError:
            error = "Please enter valid numeric values for QPI and Year."
    return render(request, "records/student_form.html", {"error": error, "course_list": course_list})

def student_edit(request, pk):
    course_list = ["BS MIS", "BS CS", "BS CS-DGDD"]
    s = get_object_or_404(Student, pk=pk)
    error = None
    if request.method == "POST":
        try:
            old_id = s.id
            new_id = request.POST["id"].strip()
            
            # If ID is changing, check if the new ID already exists
            if new_id != old_id and Student.objects.filter(id=new_id).exists():
                raise ValidationError(f"A student with ID {new_id} already exists.")

            mgr = history_managers.get(old_id, UndoRedoManager())
            mgr.record_state(s)

            # Update fields
            s.name = request.POST["name"].strip()
            s.qpi = float(request.POST["qpi"])
            s.year = int(request.POST["year"])
            s.course = request.POST["course"].strip()
            
            # Handle ID change for primary key
            if new_id != old_id:
                # Create new record with new ID and delete old one
                new_student = Student(
                    id=new_id,
                    name=s.name,
                    qpi=s.qpi,
                    year=s.year,
                    course=s.course
                )
                new_student.clean()
                new_student.save()
                s.delete()
                # Transfer history to new ID
                history_managers[new_id] = mgr
                history_managers.pop(old_id, None)
            else:
                s.clean()
                s.save()
                history_managers[old_id] = mgr
                
            return redirect("student_list")
        except ValidationError as e:
            error = e.messages[0]
        except ValueError:
            error = "Please enter valid numeric values for QPI and Year."
    return render(request, "records/student_form.html", {"student": s, "error": error, "course_list": course_list})

def student_delete(request, pk):
    s = get_object_or_404(Student, pk=pk)
    s.delete()
    history_managers.pop(pk, None)
    return redirect("student_list")

def student_undo(request, pk):
    s = get_object_or_404(Student, pk=pk)
    mgr = history_managers.get(s.id)
    if mgr:
        prev = mgr.undo(s)
        if prev:
            # If the ID in the history is different, we need to handle it
            if prev.id != s.id:
                old_id = s.id
                new_id = prev.id
                
                # Create new record with old ID from history
                new_student = Student(
                    id=new_id,
                    name=prev.name,
                    qpi=prev.qpi,
                    year=prev.year,
                    course=prev.course
                )
                new_student.save()
                s.delete()
                
                # Transfer history
                history_managers[new_id] = mgr
                history_managers.pop(old_id, None)
            else:
                s.name, s.qpi, s.year, s.course = prev.name, prev.qpi, prev.year, prev.course
                s.save()
    return redirect("student_list")


def student_redo(request, pk):
    s = get_object_or_404(Student, pk=pk)
    mgr = history_managers.get(s.id)
    if mgr:
        nxt = mgr.redo(s)
        if nxt:
            # If the ID in the history is different, we need to handle it
            if nxt.id != s.id:
                old_id = s.id
                new_id = nxt.id
                
                # Create new record with new ID from history
                new_student = Student(
                    id=new_id,
                    name=nxt.name,
                    qpi=nxt.qpi,
                    year=nxt.year,
                    course=nxt.course
                )
                new_student.save()
                s.delete()
                
                # Transfer history
                history_managers[new_id] = mgr
                history_managers.pop(old_id, None)
            else:
                s.name, s.qpi, s.year, s.course = nxt.name, nxt.qpi, nxt.year, nxt.course
                s.save()
    return redirect("student_list")

