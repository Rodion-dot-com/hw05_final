from http import HTTPStatus

from django.test import Client, TestCase


class AboutURLTests(TestCase):
    """Checking that urls in app about is working correctly."""

    @classmethod
    def setUpClass(cls):
        """Creates the post in the database."""
        super().setUpClass()
        cls.guest_client = Client()

    def test_publicly_available_url_exists_at_desired_location(self):
        """
        Checks if there are exists at desired location of pages accessible
        to unauthorized users.
        """
        urls = (
            '/about/author/',
            '/about/tech/',
        )
        for address in urls:
            with self.subTest(adress=address):
                response = AboutURLTests.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_is_the_correct_template_for_the_url_unauthorized(self):
        """
        Checks if the correct templates are being used for unauthorized users.
        """
        urls_templates = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for address, template in urls_templates.items():
            with self.subTest(adress=address):
                response = AboutURLTests.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_unexisting_page(self):
        """
        Checks that a request to an unexisting page will return a 404 error.
        """
        response = AboutURLTests.guest_client.get('/about/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
