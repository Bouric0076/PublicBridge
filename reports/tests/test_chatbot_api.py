from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
import json

class ChatbotApiTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='tester', password='pass1234')

    def test_chatbot_api_basic(self):
        self.client.login(username='tester', password='pass1234')
        url = reverse('chatbot_api')
        payload = {'message': 'hello', 'context': {'conversation_history': []}}
        resp = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('response', data)
        self.assertIn('confidence', data)
