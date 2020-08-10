from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse('recipe:ingredient-list')


class PublicIngredientsApiTests(TestCase):
    """Test the public ingredient api"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for accessing the ingredients list"""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    """Test the private ingredient api"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'test@email.com',
            'randompass'
        )

        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients_list(self):
        """Test retrievieng ingredients"""
        Ingredient.objects.create(user=self.user, name='Cream')
        Ingredient.objects.create(user=self.user, name='Cheese')

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Test that a user can only access to his tags"""

        otherUser = get_user_model().objects.create_user(
            'other@email.com',
            'otherrandompass'
        )
        ingredient = Ingredient.objects.create(user=self.user, name='Vegan')
        Ingredient.objects.create(user=otherUser, name='Fruits')

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_create_ingredient_successfull(self):
        payload = {'name': 'test ingredient'}

        self.client.post(INGREDIENTS_URL, payload)

        ingredient = Ingredient.objects.filter(
            user=self.user,
            name=payload['name']
        ).first()

        self.assertTrue(bool(ingredient))
        self.assertEqual(ingredient.name, payload['name'])

    def test_create_ingredient_invalid(self):
        """Test creating ingredient with invalid payload"""
        payload = {'name': ''}

        res = self.client.post(INGREDIENTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
