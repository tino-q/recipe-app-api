from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """Return recipe detail url"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': 5.00
    }

    defaults.update(params)
    return Recipe.objects.create(user=user, **defaults)


def sample_tag(user, name='Some tag'):
    """Create and return sample tag"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Some Ingredient'):
    """Create and return sample ingredient"""
    return Ingredient.objects.create(user=user, name=name)


class PublicRecipesApiTests(TestCase):
    """Test the public recipe api"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for accessing the recipes list"""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipesApiTests(TestCase):
    """Test the private recipe api"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'test@email.com',
            'randompass'
        )

        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrievieng recipes"""
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipess_limited_to_user(self):
        """Test that a user can only access to his recipes"""

        otherUser = get_user_model().objects.create_user(
            'other@email.com',
            'otherrandompass'
        )
        my_recipe = sample_recipe(user=self.user)
        sample_recipe(user=otherUser)

        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['title'], my_recipe.title)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.data, serializer.data)

    def test_view_recipe_detail(self):
        """Test viewing a recipe"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    # def test_create_tag_successfull(self):
    #     payload = {'name': 'test tag'}
    #     self.client.post(TAGS_URL, payload)

    #     tag = Tag.objects.filter(
    #         user=self.user,
    #         name=payload['name']
    #     ).first()

    #     self.assertTrue(bool(tag))
    #     self.assertEqual(tag.name, payload['name'])

    # def test_create_tag_invalid(self):
    #     """Test creating tag with invalid payload"""

    #     payload = {'name': ''}
    #     res = self.client.post(TAGS_URL, payload)

    #     self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
