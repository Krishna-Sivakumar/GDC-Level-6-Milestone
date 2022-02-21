from datetime import datetime, timezone
from json import loads
from random import choice

from django.contrib.auth.models import User
from django.test import TestCase

from tasks.models import STATUS_CHOICES, Task, TaskHistory
from tasks.tasks import batch_email


class ViewTests(TestCase):

    def setUp(self):
        self.usernames = ["u1", "u2", "u3", ]
        self.password = "this is a test password phrase"

    def login(self, username, password):
        response = self.client.post("/user/login/", {
            "username": username,
            "password": password
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/tasks")

    def logout(self):
        response = self.client.get("/user/logout/")
        self.assertEqual(response.url, "/user/login")
        self.assertEqual(response.status_code, 302)

    def add_task(self, **kwargs):
        return self.client.post("/add-task/", {
            "title": kwargs["title"],
            "description": "Dummy description",
            "completed": kwargs.get("completed") or False,
            "deleted": kwargs.get("deleted") or False,
            "status": STATUS_CHOICES[0][1],
            "priority": kwargs.get("priority") or 1,
        })

    def update_task(self, **kwargs):
        task_obj: Task = Task.objects.get(pk=kwargs["pk"])
        return self.client.post(f"/update-task/{task_obj.pk}/", {
            "title": kwargs.get("title") or task_obj.title,
            "description": kwargs.get("description") or task_obj.description,
            "completed": kwargs.get("completed") or task_obj.completed,
            "deleted": kwargs.get("deleted") or task_obj.completed,
            "status": kwargs.get("status") or task_obj.status,
            "priority": kwargs.get("priority") or task_obj.priority
        })

    def delete_task(self, **kwargs):
        task_obj: Task = Task.objects.get(pk=kwargs.get("pk"))
        return self.client.post(f"/delete-task/{task_obj.pk}/")

    def test_unauthenticated_access(self):
        endpoints = [
            "/tasks/",
            "/all_tasks/",
            "/completed_tasks/",
            "/add-task/",
        ]

        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, f"/user/login?next={endpoint}")

        api_endpoints = [
            "/api/task/",
            "/api/history/",
        ]

        for endpoint in api_endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 403)

    def test_authentication(self):
        self.assertEqual(User.objects.all().count(), 0)
        for username in self.usernames:
            self.assertFalse(User.objects.filter(username=username).exists())

            response = self.client.post(
                "/user/signup/", {"username": username, "password1": self.password, "password2": self.password})
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, f"/user/login")

            self.assertTrue(User.objects.filter(username=username).exists())

            response = self.client.post(
                "/user/login/", {"username": username,
                                 "password": self.password}
            )
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, "/tasks")

            response = self.client.get("/tasks/")
            self.assertEqual(response.status_code, 200)

            response = self.client.get("/user/logout/")

        self.assertEqual(User.objects.all().count(), 3)

    def test_adding_tasks(self):
        self.test_authentication()
        self.assertEqual(User.objects.all().count(), 3)
        for user in User.objects.all():
            self.login(user.username, self.password)

            # <test>
            for title in ["A", "B", "C"]:
                response = self.add_task(title=title)
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.url, "/tasks")

            response = self.client.get("/tasks/")
            self.assertEqual(
                set(response.context["object_list"]),
                set(
                    Task.objects.filter(
                        user=user,
                        completed=False,
                        deleted=False
                    )
                )
            )
            # </test>

            self.logout()

    def test_completing_tasks(self):
        self.test_adding_tasks()

        user = User.objects.first()

        self.login(user.username, self.password)

        task = Task.objects.filter(user=user).first()
        self.assertFalse(task.completed)

        self.update_task(pk=task.pk, completed=True)

        task = Task.objects.filter(user=user).first()
        self.assertTrue(task.completed)

        self.logout()

    def test_deleting_tasks(self):
        self.test_completing_tasks()

        user = User.objects.last()

        self.login(user.username, self.password)

        task = Task.objects.filter(user=user).first()
        self.assertFalse(task.deleted)

        self.delete_task(pk=task.pk)

        task = Task.objects.filter(user=user).first()
        self.assertTrue(task.deleted)

        self.logout()

    def test_authorization(self):
        self.test_deleting_tasks()
        for user in User.objects.all():
            self.login(user.username, self.password)

            endpoints = ["/tasks/", "/completed_tasks/", "/all_tasks/"]

            for endpoint in endpoints:
                # check if each task in the queryset belongs to the current user
                self.assertTrue(
                    all(
                        map(
                            lambda task: (task.user.username == user.username) and (
                                not task.deleted),
                            list(self.client.get(
                                endpoint).context.get("object_list"))
                        )
                    )
                )

            for endpoint in ["/api/task/", "/api/history/"]:
                queryset = loads(self.client.get(endpoint).content)
                self.assertTrue(
                    map(
                        lambda task: task.user.username != user.username,
                        queryset
                    )
                )

            self.logout()

    def test_cascading_tasks(self):
        self.test_authentication()

        user = User.objects.first()
        self.login(user.username, self.password)

        self.add_task(title="C", priority=1)
        self.add_task(title="D", priority=3)
        self.add_task(title="E", priority=5)
        self.add_task(title="B", priority=1)
        self.add_task(title="A", priority=1)

        priority = 1
        priority_matches = []
        for task in Task.objects.filter(
            user=user,
            completed=False,
            deleted=False
        ).order_by("priority"):
            priority_matches.append(priority == task.priority)
            priority += 1

        self.assertTrue(all(priority_matches))

        self.logout()

    def test_updating_cascade(self):
        self.test_adding_tasks()

        user = User.objects.first()

        self.login(user.username, self.password)

        first_task: Task = Task.objects.filter(
            user=user).order_by("priority").first()

        self.update_task(pk=first_task.pk, priority=first_task.priority+1)

        priority, priority_matches = 2, []
        for task in Task.objects.filter(user=user).order_by("priority"):
            priority_matches.append(priority == task.priority)
            priority += 1

        all(priority_matches)

        self.logout()

    def test_history_generation(self):
        self.test_authorization()

        for task in Task.objects.all():
            task.status = choice(STATUS_CHOICES)[0]
            task.save()

        user = User.objects.first()

        self.login(user.username, self.password)

        task: Task = Task.objects.filter(
            user=user, deleted=False, completed=False).first()

        from_status = task.status
        to_status = choice(STATUS_CHOICES)[0]
        while to_status == from_status:
            to_status = choice(STATUS_CHOICES)[0]

        self.update_task(pk=task.pk, status=to_status)

        history_obj: TaskHistory = TaskHistory.objects.filter(
            task=task).last()
        self.assertEqual(history_obj.from_status, from_status)
        self.assertEqual(history_obj.to_status, to_status)

        self.logout()

    def test_history_authorization(self):
        self.test_history_generation()
        user = User.objects.first()

        self.login(user.username, self.password)

        self.assertTrue(
            all(
                map(
                    lambda history: Task.objects.get(
                        pk=history.get("task")).user == user,
                    loads(self.client.get("/api/history/").content)
                )
            ), f"returned history objects do not belong to user \"{user.username}\"."
        )

        self.logout()

    def test_redirect_away_from_login(self):
        self.test_authentication()

        user = User.objects.first()

        self.login(user.username, self.password)

        res = self.client.get("/user/login/")
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, "/tasks")

        self.client.get("/user/signup/")
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, "/tasks")

        self.logout()

    def test_nested_history(self):
        self.test_history_generation()

        TaskHistory.objects.all().update()

        task_obj = TaskHistory.objects.first().task

        user = task_obj.user

        self.login(user.username, self.password)

        history_objects = loads(
            self.client.get(f"/api/task/{task_obj.pk}/history/").content
        )

        self.assertEqual(len(history_objects),
                         TaskHistory.objects.filter(task=task_obj).count())

        self.assertTrue(
            all(
                map(
                    lambda history: history.get("task") == task_obj.pk,
                    history_objects
                )
            )
        )

        self.logout()

    def test_report_form(self):
        print(datetime.utcnow())
        pass

    def test_report_timing(self):
        # batch_email()
        pass

    def test_deleting_user(self):
        pass
