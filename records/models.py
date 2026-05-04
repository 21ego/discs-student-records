from django.db import models
from django.core.exceptions import ValidationError

class Student(models.Model):
    id = models.CharField(max_length=6, primary_key=True)
    name = models.CharField(max_length=100)
    qpi = models.FloatField()
    year = models.IntegerField()
    course = models.CharField(max_length=20)

    def clean(self):
        # ID must be 6 digits starting with 21–25
        if not (self.id.isdigit() and len(self.id) == 6 and self.id[:2] in ["21","22","23","24","25"]):
            raise ValidationError("ID must be 6 digits starting with 21–25.")

        # Name must contain only letters and spaces
        if not all(ch.isalpha() or ch.isspace() for ch in self.name):
            raise ValidationError("Name must contain only letters and spaces.")
        
        if len(self.name.strip().split()) < 2:
            raise ValidationError("Name must include at least a first and last name.")

        # QPI must be between 1.0 and 4.0
        if not (1.0 <= self.qpi <= 4.0):
            raise ValidationError("QPI must be between 1.0 and 4.0.")

        # Year must be between 1 and 5
        if not (1 <= self.year <= 5):
            raise ValidationError("Year must be between 1 and 5.")

        # Course must be one of the allowed values
        if self.course not in ["BS MIS","BS CS","BS CS-DGDD"]:
            raise ValidationError("Course must be BS MIS, BS CS, or BS CS-DGDD.")

        # ID-Year mapping rule
        prefix = self.id[:2]
        expected_year = {"25":1, "24":2, "23":3, "22":4, "21":5}.get(prefix)
        if expected_year and self.year != expected_year:
            raise ValidationError(f"ID starting with {prefix} must be Year {expected_year}.")

    def clone(self):
        return Student(id=self.id, name=self.name, qpi=self.qpi, year=self.year, course=self.course)