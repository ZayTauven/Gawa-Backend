import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("sis", "0004_classroom_school_student_school"),
    ]

    operations = [
        migrations.CreateModel(
            name="TimetableSlot",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("day_of_week", models.PositiveSmallIntegerField(choices=[(1, "Monday"), (2, "Tuesday"), (3, "Wednesday"), (4, "Thursday"), (5, "Friday"), (6, "Saturday"), (7, "Sunday")])),
                ("start_time", models.TimeField()),
                ("end_time", models.TimeField()),
                ("subject", models.CharField(max_length=200)),
                ("room", models.CharField(blank=True, max_length=100)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True, null=True)),
                ("classroom", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="timetable_slots", to="sis.classroom")),
                ("school", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="timetable_slots", to="users.school")),
                ("teacher", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="timetable_slots", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["day_of_week", "start_time", "classroom__name"],
            },
        ),
        migrations.AddConstraint(
            model_name="timetableslot",
            constraint=models.CheckConstraint(condition=models.Q(end_time__gt=models.F("start_time")), name="sis_timetable_slot_end_after_start"),
        ),
    ]
