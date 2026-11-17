import unittest

from backend.app.agent.task_policy import build_task_policy


class TaskPolicyTests(unittest.TestCase):
    def test_catalog_and_scales(self):
        policy = build_task_policy()
        self.assertEqual(len(policy["tasks"]), 10)
        self.assertEqual(len({task["id"] for task in policy["tasks"]}), 10)
        for task in policy["tasks"]:
            self.assertIn(task["risk"], (1, 2, 3))
            self.assertIn(task["value"], (1, 2, 3))
            self.assertGreater(task["time_minutes"], 0)
            self.assertTrue(task["frequency"])
            self.assertTrue(task["reviewer"])
            self.assertEqual(task["review_status"], "PENDING_REVIEW")

    def test_top_three_per_intent(self):
        for intent in ("CONSULTA", "RADICACION", "CONSULTA_ESTADO", "FUERA_DE_ALCANCE"):
            policy = build_task_policy(intent)
            eligible = [task for task in policy["tasks"] if task["applicable"] and task["risk"] < 3]
            expected = sorted(eligible, key=lambda t: (-t["value"], t["risk"], t["time_minutes"], t["id"]))[:3]
            self.assertEqual(policy["selected_task_ids"], [task["id"] for task in expected])
            self.assertEqual(len(expected), 3)
            self.assertTrue(policy["mandatory_steps_preserved"])

    def test_matrix(self):
        tasks = {task["id"]: task for task in build_task_policy()["tasks"]}
        self.assertEqual(tasks["knowledge"]["matrix_quadrant"], "GANANCIA_RAPIDA")
        self.assertEqual(tasks["register"]["matrix_quadrant"], "PROYECTO_ESTRATEGICO")

    def test_sensitive_cases_keep_human_supervision(self):
        policy = build_task_policy("RADICACION", True)
        self.assertTrue(policy["requires_human_approval"])
        self.assertNotIn("escalate", policy["selected_task_ids"])
        self.assertIn("intervención humana prioritaria", policy["presentation"]["text"])
        self.assertEqual(policy["presentation"]["target_seconds"], 120)

    def test_calls_do_not_mutate_catalog(self):
        first = build_task_policy()
        first["tasks"][0]["risk"] = 99
        self.assertEqual(build_task_policy()["tasks"][0]["risk"], 1)


if __name__ == "__main__":
    unittest.main()
